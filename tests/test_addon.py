import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support import ROOT, document, fake_ai, service
from storyboard_addon import clip_snapshot, nodes


class AddonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.old_roots = (service.library.ROOT, service.providers.ROOT)
        self.addCleanup(lambda: service.configure(self.old_roots[0]))
        service.configure(self.temporary.name)
        self.document = document()
        self.board = service.dispatch("/library/save", {"document": self.document})["saved"]["id"]
        self.payload = {"id": self.board, "selected": [s["id"] for s in self.document["story"]["shots"]],
                        "split_mode": "fixed", "limit": 15, "guide_id": "minimax-h3-text", "provider": "openai", "model": "mock"}

    def compile(self):
        with patch.object(service.providers, "generate_json", side_effect=fake_ai) as mock:
            result = service.dispatch("/conversion/compile", self.payload)
        mock.assert_called_once()
        return result

    def test_create_plan_compile_bundle_and_portable_node_without_provider_calls(self):
        result = self.compile()
        bundle = service.dispatch("/bundle/" + result["id"])
        self.assertEqual(len(bundle["clips"]), 2)
        self.assertEqual([c["duration"] for c in bundle["clips"]], [15, 15])
        self.assertIn(self.document["story"]["shots"][0]["purpose"], bundle["clips"][0]["summary"])
        saved = clip_snapshot.encode_snapshot(bundle["clips"][0])
        service.dispatch("/library/delete", {"id": self.board})
        with patch.object(service.providers, "generate_json", side_effect=AssertionError("Queue must not call AI")):
            node = nodes.StoryboardClipPrompt()
            self.assertEqual(node.output_clip(saved), (bundle["clips"][0]["prompt"], 15., "C01"))
            self.assertTrue(node.VALIDATE_INPUTS(saved))
        self.assertEqual(service.dispatch("/catalog")["projects"], [])

    def test_two_conversions_have_distinct_identities_and_never_change_prior_snapshot(self):
        first = self.compile()
        one = service.dispatch("/bundle/" + first["id"])
        second = self.compile()
        two = service.dispatch("/bundle/" + second["id"])
        self.assertNotEqual(one["conversion_id"], two["conversion_id"])
        self.assertNotEqual(one["clips"][0]["revision"], two["clips"][0]["revision"])
        self.assertEqual(service.dispatch("/bundle/" + first["id"]), one)

    def test_ltx_modes_reach_portable_string_nodes_without_extra_ai_calls(self):
        for mode in ("text", "image"):
            self.payload["guide_id"] = f"ltx-2.5-{mode}"
            compiled = self.compile()
            bundle = service.dispatch("/bundle/" + compiled["id"])
            for clip in bundle["clips"]:
                self.assertEqual(clip["target_model"], "LTX 2.5")
                self.assertNotIn("[Shot", clip["prompt"])
                self.assertNotIn("<d>", clip["prompt"])
                snapshot = clip_snapshot.encode_snapshot(clip)
                with patch.object(service.providers, "generate_json", side_effect=AssertionError("No extra AI")):
                    self.assertEqual(nodes.StoryboardClipPrompt().output_clip(snapshot),
                                     (clip["prompt"], float(clip["duration"]), clip["clip_id"]))

    def test_catalog_excludes_prompts_provider_settings_and_credentials(self):
        self.compile()
        value = service.dispatch("/catalog")
        self.assertEqual(len(value["projects"][0]["conversions"]), 1)
        encoded = json.dumps(value)
        self.assertNotIn('"prompt"', encoded)
        self.assertNotIn("API_KEY", encoded)
        self.assertEqual(value["projects"][0]["id"], self.board)

    def test_invalid_snapshots_fail_before_any_output(self):
        clip = service.dispatch("/bundle/" + self.compile()["id"])["clips"][0]
        for key, bad in (("duration", 16), ("duration", float("nan")), ("clip_id", "../../key"), ("prompt", ""), ("source_shots", [])):
            changed = copy.deepcopy(clip)
            changed[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                clip_snapshot.decode_snapshot(json.dumps(changed))
        changed = {**clip, "api_key": "private"}
        with self.assertRaises(ValueError):
            clip_snapshot.encode_snapshot(changed)
        self.assertIsInstance(nodes.StoryboardClipPrompt.VALIDATE_INPUTS(""), str)

    def test_snapshot_tampering_detected_and_node_does_not_access_library(self):
        clip = service.dispatch("/bundle/" + self.compile()["id"])["clips"][0]
        clip["prompt"] += " Changed"
        with patch.object(service.library, "load", side_effect=AssertionError("No library access")):
            with self.assertRaises(ValueError):
                nodes.StoryboardClipPrompt().output_clip(json.dumps(clip))

    def test_busy_gate_and_provider_errors_do_not_save_conversion(self):
        service.BUSY.acquire()
        try:
            with self.assertRaises(service.BusyError):
                service.dispatch("/conversion/compile", self.payload)
        finally:
            service.BUSY.release()
        with patch.object(service.providers, "generate_json", side_effect=service.providers.ProviderError("Safe provider failure")):
            with self.assertRaises(service.providers.ProviderError):
                service.dispatch("/conversion/compile", self.payload)
        self.assertEqual(service.library.conversions(self.board), [])

    def test_vendor_files_match_pinned_revision(self):
        manifest = json.loads((ROOT / "_vendor/upstream.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["commit"]), 40)
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / "_vendor" / name).read_bytes()).hexdigest(), digest, name)

    def test_private_settings_and_library_are_outside_vendor(self):
        with patch.dict("os.environ", {}, clear=True):
            service.providers.save_settings({"values": {"OPENAI_API_KEY": "test-only-key"}, "clear_keys": []})
            self.assertNotIn("test-only-key", json.dumps(service.providers.configuration()))
        self.assertTrue((Path(self.temporary.name) / ".local-secrets/ui-settings.json").exists())
        self.assertTrue((Path(self.temporary.name) / "storage/library/storyboards.sqlite3").exists())

    def test_shared_lmstudio_engine_does_not_apply_socket_timeout(self):
        opener = unittest.mock.Mock()
        opener.open.return_value = io.BytesIO(b'{"choices":[{"finish_reason":"stop","message":{"content":"{\\"message\\":\\"ok\\"}"}}]}')
        with patch.object(service.providers, "load_settings", return_value={}), \
             patch.object(service.providers, "build_opener", return_value=opener):
            result = service.providers.generate_json("lmstudio", "mock", "system", "user", service.engine.obj(message=service.engine.TEXT))
        self.assertEqual(result, {"message": "ok"})
        self.assertIsNone(opener.open.call_args.kwargs["timeout"])

    def test_auto_unload_after_conversion_is_saved_and_keeps_bundle_on_failure(self):
        payload = {**self.payload, "provider": "ollama", "unload_ollama_after": True}

        def unload(base, model):
            self.assertEqual(len(service.library.conversions(self.board)), 1)
            return {"status": "failed"}

        with patch.object(service.providers, "load_settings", return_value={}), \
             patch.object(service.providers, "generate_json", side_effect=fake_ai), \
             patch.object(service, "unload_model", side_effect=unload) as release:
            result = service.dispatch("/conversion/compile", payload)
        release.assert_called_once()
        self.assertEqual(result["ollama_release"]["status"], "failed")
        self.assertEqual(len(service.dispatch("/bundle/" + result["id"])["clips"]), 2)
