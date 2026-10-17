"""Capture localized documentation in temporary ComfyUI; mock AI, no video rendering."""

import argparse
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
from support import direction_output, service  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--sample", required=True, type=Path)
    parser.add_argument("--language", choices=["en", "ko", "ja"], required=True)
    args = parser.parse_args()
    language = args.language
    sample = args.sample.resolve()
    images = ROOT / "docs/images"
    images.mkdir(parents=True, exist_ok=True)
    artifacts = ROOT / "storage/showcase" / language
    artifacts.mkdir(parents=True, exist_ok=True)
    document = json.loads(sample.read_text(encoding="utf-8"))
    service.engine.validate_document(document)

    def mock_ai(provider, model, system, user, schema):
        request = json.loads(user)
        result = direction_output(request["plan"], request["references"])
        for clip in result["clips"]:
            for shot in clip["shots"]:
                shot["dialogue_language"] = {"en": "English", "ko": "Korean", "ja": "Japanese"}[language]
        return result

    with tempfile.TemporaryDirectory(prefix=f"storyboard-showcase-{language}-") as temporary:
        runtime = Path(temporary)
        plugin = runtime / "custom_nodes/ComfyUI-Storyboard-Generator"
        shutil.copytree(ROOT, plugin, ignore=shutil.ignore_patterns(
            ".git", "storage", "output", "dist", "__pycache__", ".ruff_cache", ".env", ".local-secrets", ".venv"))
        data = runtime / "user/storyboard-generator"
        service.configure(data)
        board = service.library.save(document)["id"]
        payload = {"id": board, "selected": [s["id"] for s in document["story"]["shots"]],
                   "split_mode": "auto", "limit": 15, "clip_durations": {"C01": 15, "C02": 15},
                   "guide_id": "minimax-h3-text", "provider": "openai", "model": "documentation-mock"}
        with patch.object(service.providers, "generate_json", side_effect=mock_ai) as ai:
            conversion = service.dispatch("/conversion/compile", payload)
            assert ai.call_count == 1
        assert [c["duration"] for c in conversion["result"]["plan"]["clips"]] == [15, 15]
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        environment = {k: v for k, v in os.environ.items() if k not in service.providers.SETTING_FIELDS}
        environment.update(STORYBOARD_DATA_DIR=str(data), PYTHONUTF8="1")
        command = [str(args.python.resolve()), "main.py", "--cpu", "--listen", "127.0.0.1", "--port", str(port),
                   "--base-directory", str(runtime), "--disable-all-custom-nodes", "--whitelist-custom-nodes",
                   "ComfyUI-Storyboard-Generator", "--disable-api-nodes", "--disable-auto-launch"]
        base = f"http://127.0.0.1:{port}"
        with (artifacts / "server.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=args.comfy, env=environment, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Temporary ComfyUI exited; see storage/showcase logs")
                    try:
                        with urlopen(base + "/object_info/StoryboardClipPrompt", timeout=2) as response:
                            assert "StoryboardClipPrompt" in json.load(response)
                        break
                    except OSError:
                        time.sleep(.4)
                else:
                    raise TimeoutError("Temporary ComfyUI did not become ready")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch()
                    try:
                        page = browser.new_page(viewport={"width": 1600, "height": 1050})
                        page.context.grant_permissions(["clipboard-read", "clipboard-write"])
                        page.add_init_script(f"""
                          localStorage.setItem('persona-storyboard.ui-language', '{language}');
                          localStorage.setItem('comfyui-storyboard.ui-language', '{language}');
                        """)
                        errors = []
                        page.on("pageerror", lambda e: errors.append(str(e)))
                        page.goto(base)
                        page.wait_for_function("window.comfyAPI?.app?.app", timeout=60000)
                        page.evaluate("async () => { window.captureApp = (await import('./scripts/app.js')).app; }")
                        expect(page.locator("#splash-loader")).not_to_be_visible(timeout=60000)
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(1500)
                        page.evaluate("async language => await captureApp.ui.settings.setSettingValue('Comfy.Locale', language)", language)
                        page.get_by_role("button", name="Storyboard", exact=True).click()
                        studio = page.frame_locator(".sg-studio")
                        expect(studio.locator("#brief-form")).to_be_visible()
                        frame = page.locator(".sg-studio").element_handle().content_frame()
                        frame.wait_for_function("document.readyState === 'complete' && typeof busy !== 'undefined' && !busy")
                        with page.expect_response("**/storyboard-generator/api/validate") as validated:
                            studio.locator("#file").set_input_files(str(sample))
                        assert validated.value.ok
                        expect(studio.locator("#board-title")).to_have_text(document["brief"]["title"])
                        page.screenshot(path=str(images / f"create-{language}.png"))

                        page.get_by_role("tab", name={"en": "Library", "ko": "보관함", "ja": "ライブラリ"}[language], exact=True).click()
                        expect(studio.locator(".library-row")).to_have_count(1)
                        page.screenshot(path=str(images / f"library-{language}.png"))

                        page.locator("#sg-convert-tab").click()
                        studio.locator("#brief-form").evaluate("async (_, id) => { document.querySelector('#video-family').value = 'minimax'; await loadSaved(id, true); }", board)
                        expect(studio.locator("#conversion-results .prompt-output").first).to_be_visible()
                        studio.locator("#conversion-ai-provider").select_option("openai")
                        studio.locator("#conversion-ai-model").fill("documentation-mock")
                        page.set_viewport_size({"width": 1920, "height": 1200})
                        studio.locator(".conversion-settings").evaluate("node => { node.scrollTop = 0; }")
                        studio.locator("#conversion-results").evaluate("node => { node.scrollTop = 0; }")
                        page.screenshot(path=str(images / f"convert-{language}.png"))
                        copy_buttons = studio.locator("#conversion-results .prompt-copy")
                        expect(copy_buttons).to_have_count(2)
                        prompts = [c["prompt"] for c in conversion["result"]["output"]["clips"]]
                        for index, prompt in enumerate(prompts):
                            copy_buttons.nth(index).click()
                            expect(studio.locator(".prompt-copy-status").nth(index)).to_contain_text(
                                {"en": "Copied.", "ko": "복사했습니다.", "ja": "コピーしました。"}[language])
                            copied = page.evaluate("navigator.clipboard.readText()")
                            assert copied.replace("\r\n", "\n") == prompt.replace("\r\n", "\n")
                        assert not studio.locator(".prompt-clip").nth(1).evaluate("node => node.open")

                        page.locator("#sg-clips-tab").click()
                        page.set_viewport_size({"width": 1600, "height": 1050})
                        page.locator("#sg-project").select_option(board)
                        page.locator("#sg-conversion").select_option(conversion["id"])
                        expect(page.locator(".sg-clip")).to_have_count(2)
                        page.get_by_role("button", name={"en": "Select visible clips", "ko": "보이는 클립 선택", "ja": "表示中のクリップを選択"}[language], exact=True).click()
                        page.get_by_role("button", name={"en": "Add selected clips as nodes", "ko": "선택한 클립을 노드로 추가", "ja": "選択したクリップをノードに追加"}[language], exact=True).click()
                        page.evaluate("""language => {
                          const nodes = captureApp.graph._nodes.filter(n => n.type === 'StoryboardClipPrompt');
                          nodes.forEach((node, i) => {
                            node.pos = [180 + 620*i, 250];
                            const preview = LiteGraph.createNode('PreviewAny');
                            preview.title = {en:'Prompt preview',ko:'프롬프트 미리보기',ja:'プロンプトのプレビュー'}[language];
                            captureApp.graph.add(preview); preview.pos = [180 + 620*i, 550];
                            preview.size = [360, 150]; node.connect(0, preview, 0);
                          });
                          for (const group of captureApp.graph._groups) {group.pos = [150, 180]; group.size = [1040, 280];}
                          captureApp.canvas.ds.changeScale(1); captureApp.canvas.ds.offset = [50, 20];
                          captureApp.canvas.setDirty(true,true);
                        }""", language)
                        page.screenshot(path=str(images / f"clips-{language}.png"))
                        page.locator("#storyboard-panel .sg-close").click()
                        page.wait_for_timeout(400)
                        page.screenshot(path=str(images / f"nodes-{language}.png"))
                        assert not errors, errors
                        print(f"PASS ({language}): 5 actual ComfyUI screenshots; localized authored example; 2 x 15s clips; connected STRING nodes; mocked AI only.", flush=True)
                    except Exception:
                        page.screenshot(path=str(artifacts / "failure.png"))
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
    main()
