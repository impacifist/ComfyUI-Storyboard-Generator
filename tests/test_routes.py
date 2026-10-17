import json
import tempfile
import unittest
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from support import service
from storyboard_addon import routes


class RouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.old_root = service.library.ROOT
        service.configure(self.directory.name)
        app = web.Application(client_max_size=20_000_000)
        app.router.add_get(routes.PREFIX + "/api/{path:.*}", routes.api_route)
        app.router.add_post(routes.PREFIX + "/api/{path:.*}", routes.api_route)
        app.router.add_get(routes.PREFIX + "/studio/", routes.studio_route)
        app.router.add_get(routes.PREFIX + "/studio/{asset}", routes.studio_route)
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        service.configure(self.old_root)
        self.directory.cleanup()

    async def test_namespaced_studio_assets_and_same_origin_iframe(self):
        response = await self.client.get(routes.PREFIX + "/studio/")
        self.assertEqual(response.status, 200)
        body = await response.text()
        self.assertIn('/storyboard-generator/studio/app.js', body)
        self.assertIn('/storyboard-generator/studio/bridge.js', body)
        self.assertIn('/storyboard-generator/studio/diagnostics.js', body)
        self.assertIn('/storyboard-generator/studio/workbench.js', body)
        self.assertIn('/storyboard-generator/studio/studio.css', body)
        self.assertEqual((await self.client.get(routes.PREFIX + "/studio/workbench.js")).status, 200)
        self.assertEqual((await self.client.get(routes.PREFIX + "/studio/studio.css")).status, 200)
        self.assertIn("frame-ancestors 'self'", response.headers["Content-Security-Policy"])
        response = await self.client.get(routes.PREFIX + "/studio/app.js")
        self.assertIn('/storyboard-generator/api/config', await response.text())
        response = await self.client.get(routes.PREFIX + "/studio/diagnostics.js")
        self.assertEqual(response.status, 200)
        self.assertIn('/storyboard-generator/api/diagnostics', await response.text())
        self.assertEqual((await self.client.get(routes.PREFIX + "/studio/.env")).status, 404)

    async def test_cross_origin_host_and_fetch_site_rejected(self):
        for headers in ({"Origin": "https://evil.example"}, {"Host": "evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
            response = await self.client.get(routes.PREFIX + "/api/config", headers=headers)
            self.assertEqual(response.status, 403)
        with patch.object(routes.ipaddress, "ip_address") as ip:
            ip.return_value.is_loopback = False
            self.assertEqual((await self.client.get(routes.PREFIX + "/api/config")).status, 403)

    async def test_content_type_body_shape_limit_and_method_restrictions(self):
        path = routes.PREFIX + "/api/library/save"
        self.assertEqual((await self.client.post(path, data="{}")).status, 415)
        self.assertEqual((await self.client.post(path, json=[])).status, 400)
        self.assertEqual((await self.client.post(path, data="{", headers={"Content-Type": "application/json"})).status, 400)
        self.assertEqual((await self.client.get(path)).status, 404)
        with patch.object(routes, "MAX_BODY", 8):
            self.assertEqual((await self.client.post(path, json={"long": "request"})).status, 413)

    async def test_unload_post_security_busy_and_safe_status(self):
        path = routes.PREFIX + "/api/ollama/unload"
        with patch.object(service, "unload_model", return_value={"status": "unloaded"}) as unload, \
             patch.object(service.providers, "load_settings", return_value={}):
            for headers in ({"Origin": "https://evil.example"}, {"Host": "evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
                self.assertEqual((await self.client.post(path, json={"model": "qwen"}, headers=headers)).status, 403)
            unload.assert_not_called()
            self.assertEqual((await self.client.get(path)).status, 404)
            service.BUSY.acquire()
            try:
                self.assertEqual((await self.client.post(path, json={"model": "qwen"})).status, 409)
                unload.assert_not_called()
            finally:
                service.BUSY.release()
            response = await self.client.post(path, json={"model": "qwen"})
            self.assertEqual(response.status, 200)
            self.assertEqual(await response.json(), {"ollama_release": {"status": "unloaded"}})
            unload.assert_called_once()

    async def test_secret_failures_redacted_and_busy_status(self):
        with patch.object(service, "dispatch", side_effect=RuntimeError("private-key-value")):
            response = await self.client.get(routes.PREFIX + "/api/config")
            self.assertEqual(response.status, 500)
            self.assertNotIn("private-key-value", json.dumps(await response.json()))
        with patch.object(service, "dispatch", side_effect=service.BusyError("busy")):
            response = await self.client.post(routes.PREFIX + "/api/generate", json={})
            self.assertEqual(response.status, 409)
