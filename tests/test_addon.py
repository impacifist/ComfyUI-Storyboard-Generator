import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support import ROOT, direction_output, document, fake_ai, service
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

    def test_source_speakers_survive_each_model_and_portable_string_output(self):
        ids = [c["id"] for c in self.document["brief"]["characters"]]
        original = copy.deepcopy(self.document)
        self.document["story"]["shots"][0]["dialogue"] = [
            {"speaker": ids[1], "text": "First speaker.", "delivery": ""},
            {"speaker": ids[0], "text": "Second speaker.", "delivery": ""}]
        self.board = service.dispatch("/library/save", {"document": self.document})["saved"]["id"]
        self.payload["id"] = self.board
        for target in ("minimax-h3-text", "seedance-2-text", "ltx-2.5-text", "ltx-2.5-image"):
            with self.subTest(target=target):
                self.payload["guide_id"] = target
                result = self.compile()
                clip = service.dispatch("/bundle/" + result["id"])["clips"][0]
                self.assertIn("Character 2", clip["prompt"])
                self.assertIn("Character 1", clip["prompt"])
                self.assertIn("without speaking or lip-syncing it", clip["prompt"])
                snapshot = clip_snapshot.encode_snapshot(clip)
                with patch.object(service.providers, "generate_json", side_effect=AssertionError("No queue-time AI")):
                    self.assertEqual(nodes.StoryboardClipPrompt().output_clip(snapshot)[0], clip["prompt"])
        self.assertEqual(original["brief"], self.document["brief"])

    def test_four_reference_kinds_compile_into_portable_string_nodes(self):
        png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII="
        images = []
        for kind in ("character", "background", "prop", "other"):
            image = service.dispatch("/references/upload", {"id": self.board, "kind": kind, "data": png, "name": "sample.png",
                "character_id": self.document["brief"]["characters"][0]["id"] if kind == "character" else "",
                "target_name": "Phone" if kind == "prop" else "Lighting" if kind == "other" else "",
                "note": "Use only the warm lighting." if kind == "other" else ""})["asset"]
            images.append(image)
        saved = service.dispatch("/references/save", {"id": self.board, "references": images})["references"]
        self.assertEqual([a["kind"] for a in saved], ["character", "background", "prop", "other"])
        for target in ("minimax-h3-reference", "seedance-2-reference"):
            self.payload.update(guide_id=target, references=saved)
            result = self.compile()
            clip = service.dispatch("/bundle/" + result["id"])["clips"][0]
            self.assertIn("Prop 1 (Phone)", clip["prompt"])
            self.assertIn("Visual reference 1 (Lighting)", clip["prompt"])
            with patch.object(service.providers, "generate_json", side_effect=AssertionError("No extra AI")):
                self.assertEqual(nodes.StoryboardClipPrompt().output_clip(clip_snapshot.encode_snapshot(clip))[0], clip["prompt"])

    def test_mismatched_count_requires_acceptance_without_another_ai_request(self):
        story = copy.deepcopy(self.document["story"])
        story["shots"] = story["shots"][:5]
        original = copy.deepcopy(self.document)
        with patch.object(service.providers, "generate_json", return_value=story) as ai:
            result = service.dispatch("/generate", {"brief": self.document["brief"], "provider": "openai",
                "model": "mock", "offer_count_choice": True})
            pending = result["pending_generation"]
            self.assertEqual((pending["requested_count"], pending["actual_count"]), (6, 5))
            self.assertEqual(len(service.library.listing()), 1)
            accepted = service.dispatch("/generation/accept", {"document": pending["document"],
                "requested_brief": self.document["brief"]})
            ai.assert_called_once()
        self.assertEqual(accepted["document"]["brief"]["shot_count"], 5)
        self.assertEqual(service.library.load(self.board), original)
        service.dispatch("/library/save", {"document": accepted["document"]})
        self.assertEqual(len(service.library.listing()), 2)

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

    def test_complete_id_permutation_is_saved_and_becomes_correct_portable_strings(self):
        def reordered(provider, model, system, user, schema):
            request = json.loads(user)
            self.assertIn('shot_contract', request)
            draft = direction_output(request['plan'])
            draft['clips'].reverse()
            for clip in draft['clips']:
                clip['shots'].reverse()
            return draft

        with patch.object(service.providers, 'generate_json', side_effect=reordered) as ai:
            result = service.dispatch('/conversion/compile', self.payload)
        self.assertEqual(ai.call_count, 1)
        self.assertTrue(result['result']['validation_report']['reordered_by_id'])
        self.assertEqual(service.library.load(self.board), self.document)
        bundle = service.dispatch('/bundle/' + result['id'])
        self.assertEqual([c['clip_id'] for c in bundle['clips']], ['C01', 'C02'])
        for clip in bundle['clips']:
            self.assertEqual(nodes.StoryboardClipPrompt().output_clip(clip_snapshot.encode_snapshot(clip))[0], clip['prompt'])

    def test_failed_structure_repair_preserves_saved_conversion_and_source(self):
        first = self.compile()
        layout = service.conversion.preflight(self.document, self.payload)[0]
        invalid = direction_output(layout)
        invalid['clips'][1]['shots'].pop()
        with patch.object(service.providers, 'generate_json', return_value=invalid) as ai:
            with self.assertRaisesRegex(service.ValidationError, 'clips.C02.shots'):
                service.dispatch('/conversion/compile', self.payload)
        self.assertEqual(ai.call_count, 2)
        self.assertEqual(len(service.library.conversions(self.board)), 1)
        self.assertEqual(service.library.conversions(self.board)[0]['id'], first['id'])
        self.assertEqual(service.library.load(self.board), self.document)

    def test_targeted_delivery_translation_preserves_portable_strings_and_source(self):
        calls = []

        def translate(provider, model, system, user, schema):
            data = json.loads(user)
            calls.append(data)
            if 'instruction_translations' in data:
                self.assertNotIn('plan', data)
                return {'translations': {item['key']: 'With concern' for item in data['instruction_translations']}}
            draft = direction_output(data['plan'])
            draft['clips'][0]['shots'][0]['deliveries'][0] = '걱정스럽게'
            return draft

        with patch.object(service.providers, 'generate_json', side_effect=translate):
            result = service.dispatch('/conversion/compile', {**self.payload, 'provider': 'lmstudio'})
        self.assertEqual(len(calls), 2)
        self.assertEqual(result['result']['validation_report']['repair_kind'], 'instruction_translation')
        self.assertEqual(service.library.load(self.board), self.document)
        bundle = service.dispatch('/bundle/' + result['id'])
        self.assertIn('With concern', bundle['clips'][0]['prompt'])
        for clip in bundle['clips']:
            self.assertEqual(nodes.StoryboardClipPrompt().output_clip(clip_snapshot.encode_snapshot(clip))[0], clip['prompt'])

    def test_failed_delivery_translation_preserves_prior_saved_conversion(self):
        first = self.compile()
        layout = service.conversion.preflight(self.document, self.payload)[0]
        invalid = direction_output(layout)
        invalid['clips'][0]['shots'][0]['deliveries'][0] = '걱정스럽게'
        with patch.object(service.providers, 'generate_json', side_effect=[invalid, {'translations': {'T001': '걱정스럽게'}}]) as ai:
            with self.assertRaisesRegex(service.ValidationError, '1회.*deliveries'):
                service.dispatch('/conversion/compile', self.payload)
        self.assertEqual(ai.call_count, 2)
        self.assertEqual(len(service.library.conversions(self.board)), 1)
        self.assertEqual(service.library.conversions(self.board)[0]['id'], first['id'])
        self.assertEqual(service.library.load(self.board), self.document)
