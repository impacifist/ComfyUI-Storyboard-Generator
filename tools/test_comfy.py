"""Real ComfyUI smoke test in an isolated CPU instance; no existing server changes."""

import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from support import document, fake_ai, service  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402


def main(comfy, python):
    artifacts = ROOT / "storage/browser-check"
    artifacts.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="comfy-storyboard-smoke-") as temporary:
        temporary = Path(temporary)
        runtime = temporary / "runtime"
        runtime.mkdir()
        plugin = runtime / "custom_nodes/ComfyUI-Storyboard-Generator"
        shutil.copytree(ROOT, plugin, ignore=shutil.ignore_patterns(".git", "storage", "output", "dist", "__pycache__", ".ruff_cache", ".env", ".env.*", ".local-secrets", ".venv"))
        data = runtime / "user/storyboard-generator"
        service.configure(data)
        doc = document()
        doc["brief"]["title"] = "After-school conversation — demo"
        doc["brief"]["duration"] = 45
        for shot in doc["story"]["shots"]:
            shot["duration"] = 7.5
        board = service.library.save(doc)["id"]
        payload = {"id": board, "selected": [s["id"] for s in doc["story"]["shots"]], "split_mode": "auto", "limit": 15,
                   "clip_durations": {"C01": 13, "C02": 13, "C03": 13}, "guide_id": "ltx-2.5-text", "provider": "openai", "model": "mock"}
        def reordered_ai(*args):
            draft = fake_ai(*args)
            draft["clips"].reverse()
            for clip in draft["clips"]:
                clip["shots"].reverse()
            return draft

        with patch.object(service.providers, "generate_json", side_effect=reordered_ai):
            first = service.dispatch("/conversion/compile", payload)
            second = service.dispatch("/conversion/compile", payload)
        assert first["result"]["validation_report"]["reordered_by_id"]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        environment = {key: value for key, value in os.environ.items() if key not in service.providers.SETTING_FIELDS}
        environment["STORYBOARD_DATA_DIR"] = str(data)
        environment["PYTHONUTF8"] = "1"
        command = [str(python), "main.py", "--cpu", "--listen", "127.0.0.1", "--port", str(port), "--base-directory", str(runtime),
                   "--disable-all-custom-nodes", "--whitelist-custom-nodes", "ComfyUI-Storyboard-Generator", "--disable-api-nodes", "--disable-auto-launch"]
        base = f"http://127.0.0.1:{port}"
        with (artifacts / "comfy-smoke.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=comfy, env=environment, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Isolated ComfyUI exited. See storage/browser-check/comfy-smoke.log")
                    try:
                        with urlopen(base + "/object_info/StoryboardClipPrompt", timeout=2) as response:
                            assert "StoryboardClipPrompt" in json.load(response)
                            break
                    except OSError:
                        time.sleep(.4)
                else:
                    raise TimeoutError("Isolated ComfyUI did not become ready")
                print("PASS: real ComfyUI loaded the custom node and routes.", flush=True)
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    page = browser.new_page(viewport={"width": 1600, "height": 1050})
                    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    try:
                        page.goto(base)
                        page.wait_for_function("window.comfyAPI?.app?.app", timeout=60000)
                        page.evaluate("async () => { window.testApp = (await import('./scripts/app.js')).app; }")
                        page.wait_for_function("window.testApp?.graph && window.testApp?.canvas", timeout=60000)
                        expect(page.locator("#splash-loader")).not_to_be_visible(timeout=60000)
                        page.keyboard.press("Escape")  # Dismiss ComfyUI's first-run template browser.
                        page.get_by_role("button", name="Storyboard", exact=True).click(timeout=30000)
                        expect(page.locator("#storyboard-panel")).to_be_visible()
                        studio = page.frame_locator(".sg-studio")
                        expect(studio.locator("#brief-form")).to_be_visible()
                        frame = page.locator(".sg-studio").element_handle().content_frame()
                        frame.wait_for_function("document.readyState === 'complete' && typeof busy !== 'undefined' && !busy")

                        def dark_surface(selector, require_dark=True):
                            style = studio.locator(selector).first.evaluate("""node => {
                              const style = getComputedStyle(node);
                              let surface = node;
                              while (surface.parentElement && getComputedStyle(surface).backgroundColor === 'rgba(0, 0, 0, 0)') surface = surface.parentElement;
                              return {bg: getComputedStyle(surface).backgroundColor, ink: style.color};
                            }""")
                            import re
                            colors = {key: [int(n) / 255 for n in re.findall(r'\d+', value)[:3]] for key, value in style.items()}
                            assert len(colors["bg"]) == 3, (selector, style)
                            if require_dark:
                                assert max(colors["bg"]) < .3, (selector, style)
                            def luminance(rgb):
                                values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
                                return sum(v * weight for v, weight in zip(values, (.2126, .7152, .0722)))
                            light, dark = sorted([luminance(colors["ink"]), luminance(colors["bg"])], reverse=True)
                            assert (light + .05) / (dark + .05) >= 4.5, (selector, style)

                        def conversion_layout():
                            for width in (1440, 1920, 2560):
                                page.set_viewport_size({"width": width, "height": 1080})
                                assert page.locator("#storyboard-panel").evaluate("node => node.getBoundingClientRect().width >= innerWidth * .97")
                                dimensions = studio.locator("#conversion-controls").evaluate("""node => {
                                  const setting = node.querySelector('.conversion-settings').getBoundingClientRect();
                                  const result = node.querySelector('#conversion-results').getBoundingClientRect();
                                  const workspace = node.querySelector('.conversion-workspace').getBoundingClientRect();
                                  const view = document.querySelector('#conversion-view').getBoundingClientRect();
                                  return {settings: setting.width, results: result.width, workspace: workspace.width,
                                    view: view.width, viewport: innerWidth, beside: result.left >= setting.right,
                                    aligned: Math.abs(result.top - setting.top) < 2};
                                }""")
                                assert dimensions['view'] >= dimensions['viewport'] - 44, dimensions
                                assert dimensions['workspace'] >= dimensions['view'] - 2, dimensions
                                assert .3 < dimensions['settings'] / dimensions['workspace'] < .5, dimensions
                                assert dimensions['results'] >= dimensions['workspace'] * .5, dimensions
                                assert dimensions['beside'] and dimensions['aligned'], dimensions
                                assert studio.locator("body").evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")
                            page.set_viewport_size({"width": 1600, "height": 1050})
                        studio.locator("#example").click()
                        studio.locator("#generate").click()
                        expect(studio.locator("#shots .shot")).to_have_count(6)
                        assert studio.locator("#generate").evaluate("node => node.form.id") == "brief-form"
                        page.screenshot(path=str(artifacts / "workbench-create-desktop.png"))
                        studio.locator("#workbench-next").click()
                        expect(studio.locator("#conversion-controls")).to_be_visible()
                        expect(page.locator("#sg-convert-tab")).to_have_attribute("aria-selected", "true")
                        expect(studio.locator("#conversion-results")).to_be_empty()
                        for lang in ("ko", "ja", "en"):
                            studio.locator("#brief-form").evaluate("(_, language) => I18n.select(language)", lang)
                            conversion_layout()
                        page.screenshot(path=str(artifacts / "conversion-before-wide.png"))
                        page.get_by_role("tab", name="Library", exact=True).click()
                        expect(studio.locator(".library-row").first).to_be_visible()
                        for selector in ("#library-items", ".library-toolbar", ".library-toolbar input", ".library-list-heading"):
                            dark_surface(selector)
                        studio.locator(".library-row").first.get_by_role("button", name="Preview content", exact=True).click()
                        expect(studio.locator("#saved-preview")).to_be_visible()
                        dark_surface("#saved-preview")
                        studio.locator("#saved-preview-close").click()
                        page.screenshot(path=str(artifacts / "library-dark.png"))
                        page.locator("#sg-clips-tab").click()
                        page.locator("#sg-project").select_option(board)
                        page.locator("#sg-conversion").select_option(first["id"])
                        expect(page.locator(".sg-clip")).to_have_count(3)
                        page.locator("#sg-search").fill("C02")
                        expect(page.locator(".sg-clip")).to_have_count(1)
                        page.locator("#sg-search").fill("")
                        page.get_by_role("button", name="Select visible clips", exact=True).click()
                        page.get_by_role("button", name="Add selected clips as nodes", exact=True).click()
                        assert page.evaluate("testApp.graph._nodes.filter(n => n.type === 'StoryboardClipPrompt').length") == 3
                        page.get_by_role("button", name="Add selected clips as nodes", exact=True).click()
                        assert page.evaluate("testApp.graph._nodes.filter(n => n.type === 'StoryboardClipPrompt').length") == 3
                        first_value = page.evaluate("testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').widgets.find(w => w.name === 'clip_data').value")
                        page.evaluate("""() => {
                          const nodes = testApp.graph._nodes.filter(n => n.type === 'StoryboardClipPrompt');
                          const sink = LiteGraph.createNode('PreviewAny'); testApp.graph.add(sink);
                          nodes[0].connect(0, sink, 0);
                          window.savedWorkflow = testApp.graph.serialize();
                        }""")
                        workflow = page.evaluate("savedWorkflow")
                        (artifacts / "sample-workflow.json").write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
                        page.locator("#sg-conversion").select_option(second["id"])
                        expect(page.locator(".sg-clip-meta").first).to_contain_text("Another conversion")
                        assert page.evaluate("testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').widgets.find(w => w.name === 'clip_data').value") == first_value
                        page.get_by_role("button", name="Select visible clips", exact=True).click()
                        page.evaluate("testApp.extensionManager.dialog.confirm = async () => true")
                        page.get_by_role("button", name="Update matching nodes", exact=True).click()
                        expect(page.locator(".sg-status")).to_contain_text("Nodes updated")
                        assert page.evaluate("testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').outputs[0].links.length") == 1
                        page.screenshot(path=str(artifacts / "clips-desktop.png"))
                        page.get_by_role("button", name="Close", exact=True).click()
                        page.evaluate("""() => {
                          const clips = testApp.graph._nodes.filter(n => n.type === 'StoryboardClipPrompt');
                          clips.forEach((node, index) => { node.pos = [100 + index * 410, 250]; });
                          const sink = testApp.graph._nodes.find(n => n.type === 'PreviewAny');
                          sink.pos = [570, 570]; sink.size = [360, 150];
                          for (const group of testApp.graph._groups) {
                            group.pos = [70, 180]; group.size = [1210, 270];
                          }
                          testApp.canvas.ds.scale = 1;
                          testApp.canvas.ds.offset = [70, 30];
                          testApp.canvas.setDirty(true, true);
                        }""")
                        page.wait_for_timeout(400)
                        page.screenshot(path=str(artifacts / "nodes-desktop.png"))
                        page.evaluate("async () => { await testApp.loadGraphData(window.savedWorkflow); }")
                        assert page.evaluate("testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').widgets.find(w => w.name === 'clip_data').value") == first_value
                        awaitable = page.request.post(base + "/prompt", data={"prompt": {
                            "1": {"class_type": "StoryboardClipPrompt", "inputs": {"clip_data": first_value}},
                            "2": {"class_type": "PreviewAny", "inputs": {"source": ["1", 0]}}}})
                        assert awaitable.ok, awaitable.text()
                        queued = awaitable.json()["prompt_id"]
                        for _ in range(40):
                            history = page.request.get(base + "/history/" + queued).json()
                            if queued in history:
                                assert history[queued]["status"]["status_str"] == "success", history
                                assert history[queued]["outputs"]["2"]["text"][0] == json.loads(first_value)["prompt"]
                                break
                            page.wait_for_timeout(250)
                        else:
                            raise AssertionError("String-only queue test did not complete")
                        page.evaluate("""async () => {
                          const node = testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt');
                          await node.widgets.find(w => w.name === 'Choose clip').callback();
                        }""")
                        expect(page.get_by_role("button", name="Use this clip in the selected node", exact=True)).to_be_visible()
                        page.locator(".sg-clip input[aria-label='C03']").check()
                        page.get_by_role("button", name="Use this clip in the selected node", exact=True).click()
                        assert page.evaluate("JSON.parse(testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').widgets.find(w => w.name === 'clip_data').value).clip_id") == "C03"
                        assert page.evaluate("testApp.graph._nodes.find(n => n.type === 'StoryboardClipPrompt').outputs[0].links.length") == 1
                        # UI lifecycle requests are mocked; never unload a user's real model.
                        page.get_by_role("tab", name="Create", exact=True).click()
                        expect(studio.locator("#creation-view")).to_be_visible()
                        page.locator("#sg-convert-tab").click()
                        expect(studio.locator("#conversion-view")).to_be_visible()
                        studio.locator("#brief-form").evaluate("async (_, id) => { await loadSaved(id, true); }", board)
                        studio.locator("#video-family").select_option("ltx")
                        studio.locator("#video-guide").select_option("image")
                        expect(studio.locator("#ltx-image-help")).to_be_visible()
                        studio.locator("#official-guide-preview > summary").click()
                        for selector in (".conversion-settings", "#official-guide-preview > summary", ".result-metadata > summary", "#official-guide-body", "#official-system-body", ".prompt-clip .prompt-output"):
                            dark_surface(selector)
                        studio.locator("#official-guide-preview > summary").click()
                        studio.locator("#conversion-results .prompt-copy").first.click()
                        expect(studio.locator(".prompt-copy-status").first).to_have_text("Copied.")
                        copied = page.evaluate("navigator.clipboard.readText()")
                        expected_prompt = second["result"]["output"]["clips"][0]["prompt"]
                        assert copied.replace("\r\n", "\n") == expected_prompt.replace("\r\n", "\n")
                        studio.locator("#conversion-ai-provider").evaluate("node => { node.value='ollama'; node.dispatchEvent(new Event('change')); }")
                        studio.locator("#conversion-ai-model").fill("mock-ollama")
                        studio.locator("#ollama-memory").evaluate("node => { node.parentElement.open = true; }")
                        expect(studio.locator("#ollama-auto-unload")).to_be_checked()
                        unload_calls, conversion_calls = [], []

                        def unload_route(route):
                            unload_calls.append(route.request.post_data_json)
                            route.fulfill(json={"ollama_release": {"status": "unloaded"}})

                        def conversion_route(route):
                            body = route.request.post_data_json
                            conversion_calls.append(body)
                            result = {**first}
                            if body.get("unload_ollama_after"):
                                result["ollama_release"] = {"status": "unloaded"}
                            route.fulfill(json=result)

                        page.route("**/storyboard-generator/api/ollama/unload", unload_route)
                        page.route("**/storyboard-generator/api/conversion/compile", conversion_route)
                        studio.locator("#ollama-unload").click()
                        expect(studio.locator("#ollama-memory-status")).to_contain_text("confirmed")
                        assert unload_calls == [{"model": "mock-ollama"}]
                        studio.locator("#conversion-consent").check()
                        with page.expect_request("**/storyboard-generator/api/conversion/compile"):
                            studio.locator("#conversion-run").click()
                        expect(studio.locator("#ollama-memory-status")).to_contain_text("confirmed")
                        assert conversion_calls[-1]["unload_ollama_after"] is True
                        expect(studio.locator("#conversion-results")).to_contain_text("Clip and shot order was restored using the original IDs.")
                        assert conversion_calls[-1]["guide_id"] == "ltx-2.5-image"
                        assert conversion_calls[-1]["references"] == []
                        studio.locator("#ollama-auto-unload").uncheck()
                        with page.expect_request("**/storyboard-generator/api/conversion/compile"):
                            studio.locator("#conversion-run").click()
                        expect(studio.locator("#ollama-memory-status")).to_be_empty()
                        assert conversion_calls[-1]["unload_ollama_after"] is False
                        assert studio.locator("#brief-form").evaluate("() => localStorage.getItem('comfyui-storyboard.ollama-auto-unload')") == "false"
                        expect(studio.locator(".prompt-clip .prompt-output").first).to_be_in_viewport()
                        page.screenshot(path=str(artifacts / "ollama-memory-desktop.png"))
                        # Exercise the actual reference routes and shared composer in the dark iframe.
                        studio.locator("#video-family").select_option("minimax")
                        studio.locator("#video-guide").select_option("reference")
                        studio.locator("#reference-panel").evaluate("node => { node.parentElement.open = true; }")
                        png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=")
                        for index, kind in enumerate(("character", "background", "prop", "other"), 1):
                            studio.locator(f'[data-reference-kind="{kind}"]').click()
                            if kind in ("prop", "other"):
                                studio.locator("#reference-target-name").fill("Phone" if kind == "prop" else "Lighting")
                            if kind == "other":
                                studio.locator("#reference-usage").fill("Use only the warm backlight.")
                            studio.locator("#reference-files").set_input_files({"name": "reference.png", "mimeType": "image/png", "buffer": png})
                            expect(studio.locator(".reference-card")).to_have_count(index)
                        for selector in ("#reference-panel", ".reference-composer", ".reference-group[open] .reference-card", "#reference-usage"):
                            dark_surface(selector)
                        dark_surface('.reference-kind-picker [aria-pressed="true"]', require_dark=False)
                        conversion_layout()
                        studio.locator("#reference-panel").scroll_into_view_if_needed()
                        page.screenshot(path=str(artifacts / "references-four-types-dark.png"))
                        page.screenshot(path=str(artifacts / "conversion-full-width.png"))
                        page.screenshot(path=str(artifacts / "conversion-after-wide.png"))
                        page.set_viewport_size({"width": 390, "height": 844})
                        assert studio.locator("body").evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")
                        page.set_viewport_size({"width": 1600, "height": 1050})
                        page.get_by_role("tab", name="Clip prompts", exact=True).click()
                        studio.locator("#brief-form").evaluate("() => I18n.select('ko')")
                        expect(page.get_by_role("button", name="선택한 클립을 노드로 추가", exact=True)).to_be_visible()
                        studio.locator("#brief-form").evaluate("() => I18n.select('ja')")
                        expect(page.get_by_role("button", name="選択したクリップをノードに追加", exact=True)).to_be_visible()
                        studio.locator("#brief-form").evaluate("() => I18n.select('en')")
                        page.locator("#storyboard-panel .sg-close").click()
                        page.get_by_role("button", name="Storyboard", exact=True).click()
                        page.locator("#sg-clips-tab").click()
                        page.set_viewport_size({"width": 390, "height": 844})
                        page.screenshot(path=str(artifacts / "clips-mobile.png"))
                        assert page.locator("#storyboard-panel").evaluate("e => e.scrollWidth <= e.clientWidth + 1")
                        page.get_by_role("tab", name="Create", exact=True).click()
                        expect(studio.locator("#creation-view")).to_be_visible()
                        assert studio.locator("body").evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")
                        expect(studio.locator("#generate")).to_be_visible()
                        for lang in ("ko", "ja", "en"):
                            studio.locator("#brief-form").evaluate("(_, language) => I18n.select(language)", lang)
                            assert studio.locator("body").evaluate("() => document.documentElement.scrollWidth <= innerWidth + 1")
                        page.screenshot(path=str(artifacts / "workbench-create-mobile.png"))
                        page.set_viewport_size({"width": 1600, "height": 1050})
                        generation_requests = []

                        def generation_route(route):
                            body = route.request.post_data_json
                            generation_requests.append(body)
                            assert body['offer_count_choice'] is True
                            candidate = json.loads(json.dumps(body['previous']))
                            candidate['story']['shots'] = candidate['story']['shots'][:5]
                            candidate['brief']['shot_count'] = 5
                            route.fulfill(json={'pending_generation': {'document': candidate,
                                'review': service.engine.review(candidate), 'requested_count': body['brief']['shot_count'], 'actual_count': 5}})

                        page.route("**/storyboard-generator/api/generate", generation_route)
                        studio.locator("#regenerate").click()
                        expect(studio.locator("#generation-choice")).to_be_visible()
                        expect(studio.locator("#generation-choice-count")).to_contain_text("Generated: 5")
                        assert studio.locator("#brief-form").evaluate("() => project.story.shots.length") == 6
                        for selector in ("#generation-choice", "#generation-choice-preview", "#generation-choice-count"):
                            dark_surface(selector)
                        page.screenshot(path=str(artifacts / "generation-count-choice-dark.png"))
                        for width in (390, 1600):
                            page.set_viewport_size({"width": width, "height": 1050})
                            assert studio.locator("#generation-choice").evaluate("node => node.scrollWidth <= node.clientWidth + 1")
                        studio.locator("#generation-choice-use").click()
                        expect(studio.locator("#generation-choice")).not_to_be_visible()
                        expect(studio.locator("#stats")).to_contain_text("5 shots")
                        assert len(generation_requests) == 1
                        assert studio.locator("#brief-form").evaluate("() => project.brief.shot_count") == 5
                        assert not errors, errors
                        print("PASS: toolbar, embedded creation, clip search, 3 nodes, deduplication, explicit update, per-node selection, preserved wires, workflow reload, actual STRING queue, Ollama auto/manual unload UI with mocked requests, 3 languages and mobile.", flush=True)
                    except Exception:
                        page.screenshot(path=str(artifacts / "failure.png"))
                        (artifacts / "browser-errors.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
                        raise
                    finally:
                        browser.close()
            finally:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--comfy", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    main(args.comfy.resolve(), args.python.resolve())
