import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import URLError

from support import service
from storyboard_addon import ollama_memory
from storyboard_addon.service import ValidationError


class OllamaMemoryTests(unittest.TestCase):
    def test_unload_request_is_local_prompt_free_bounded_and_confirmed(self):
        opener = Mock()
        opener.open.return_value = io.BytesIO(b'{"done":true,"done_reason":"unload"}')
        with patch.object(ollama_memory, "build_opener", return_value=opener):
            self.assertEqual(ollama_memory.unload_model("http://localhost:11434", "qwen:latest"), {"status": "unloaded"})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/api/generate")
        self.assertEqual(json.loads(request.data), {"model": "qwen:latest", "stream": False, "keep_alive": 0})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15)

    def test_bad_target_fails_before_network(self):
        for base, model in (("http://remote.example", "qwen"), ("http://localhost:11434", ""),
                            ("http://localhost:11434", "qwen\nprivate"), ("http://localhost:11434", "x" * 201)):
            with self.subTest(base=base), patch.object(ollama_memory, "build_opener") as opener:
                with self.assertRaises(ValidationError):
                    ollama_memory.unload_model(base, model)
                opener.assert_not_called()

    def test_failures_redacted_and_uncertain_response_never_claims_unload(self):
        for response, expected in ((b'{"done":true}', "unconfirmed"), (b'{"done":false,"done_reason":"unload"}', "unconfirmed"),
                                   (b'PRIVATE', "failed"), (b'x' * 1_000_001, "failed")):
            opener = Mock()
            opener.open.return_value = io.BytesIO(response)
            with patch.object(ollama_memory, "build_opener", return_value=opener):
                self.assertEqual(ollama_memory.unload_model("http://localhost:11434", "qwen"), {"status": expected})
        for error in (URLError("PRIVATE"), TimeoutError("PRIVATE")):
            opener = Mock()
            opener.open.side_effect = error
            with patch.object(ollama_memory, "build_opener", return_value=opener):
                self.assertEqual(ollama_memory.unload_model("http://localhost:11434", "qwen"), {"status": "failed"})

    def test_auto_unload_after_entire_operation_result_and_lock_protection(self):
        events = []
        payload = {"provider": "ollama", "model": "qwen", "unload_ollama_after": True}

        def compile(path, cleaned):
            self.assertNotIn("unload_ollama_after", cleaned)
            events.extend(["generate", "repair", "save"])
            return {"id": "saved", "result": {"prompts": ["one", "two"]}}

        def unload(base, model):
            self.assertTrue(service.BUSY.locked())
            self.assertEqual(model, "qwen")
            with self.assertRaises(service.BusyError):
                service.dispatch("/ollama/unload", {"model": "qwen"})
            events.append("unload")
            return {"status": "failed"}

        with patch.object(service.providers, "load_settings", return_value={}), \
             patch.object(service, "operation", side_effect=compile), patch.object(service, "unload_model", side_effect=unload):
            result = service.dispatch("/conversion/compile", payload)
        self.assertEqual(events, ["generate", "repair", "save", "unload"])
        self.assertEqual(result["id"], "saved")
        self.assertEqual(result["result"]["prompts"], ["one", "two"])
        self.assertEqual(result["ollama_release"]["status"], "failed")
        self.assertTrue(payload["unload_ollama_after"])
        self.assertFalse(service.BUSY.locked())

    def test_no_unload_for_opt_out_other_provider_failed_conversion_or_plan(self):
        for path, payload in (("/conversion/compile", {"provider": "ollama", "model": "qwen"}),
                              ("/conversion/compile", {"provider": "openai", "unload_ollama_after": True}),
                              ("/conversion/plan", {"provider": "ollama", "unload_ollama_after": True})):
            with patch.object(service, "operation", return_value={}), patch.object(service, "unload_model") as unload:
                service.dispatch(path, payload)
                unload.assert_not_called()
        with patch.object(service.providers, "load_settings", return_value={}), \
             patch.object(service, "operation", side_effect=ValidationError("invalid")), patch.object(service, "unload_model") as unload:
            with self.assertRaises(ValidationError):
                service.dispatch("/conversion/compile", {"provider": "ollama", "model": "qwen", "unload_ollama_after": True})
            unload.assert_not_called()
        self.assertFalse(service.BUSY.locked())
        with self.assertRaises(ValidationError):
            service.dispatch("/conversion/compile", {"unload_ollama_after": "false"})

    def test_manual_unload_uses_configured_base_and_selected_model_only(self):
        with patch.object(service.providers, "load_settings", return_value={"OLLAMA_BASE_URL": "http://127.0.0.1:11435"}), \
             patch.object(service, "unload_model", return_value={"status": "unloaded"}) as unload:
            result = service.dispatch("/ollama/unload", {"model": "qwen", "base": "http://evil.example"})
        unload.assert_called_once_with("http://127.0.0.1:11435", "qwen")
        self.assertEqual(result["ollama_release"]["status"], "unloaded")
