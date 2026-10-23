"""Serve the static demo below a project path; validate exports without any AI."""

import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from support import ROOT  # noqa: E402
from storyboard_addon.clip_snapshot import decode_snapshot  # noqa: E402
from build_demo import build  # noqa: E402
from playwright.sync_api import expect, sync_playwright  # noqa: E402


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    site = ROOT / 'dist' / 'demo-browser' / 'ComfyUI-Storyboard-Generator'
    build(site)
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=site.parent))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    artifacts = ROOT / 'storage/browser-check'
    artifacts.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={'width': 1600, 'height': 1050})
            page.context.grant_permissions(['clipboard-read', 'clipboard-write'])
            errors, requests = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda request: requests.append((request.method, request.url)))
            url = f'http://127.0.0.1:{server.server_port}/ComfyUI-Storyboard-Generator/'
            try:
                page.goto(url)
                expect(page.locator('.shot-card')).to_have_count(6)
                page.screenshot(path=str(artifacts / 'demo-storyboard-desktop.png'), full_page=True)
                page.locator('.shot-card').first.click()
                expect(page.locator('#shot-dialog')).to_be_visible()
                expect(page.locator('#shot-detail')).to_contain_text('Still raining.')
                page.keyboard.press('Escape')
                expect(page.locator('#shot-dialog')).not_to_be_visible()
                page.locator('#tab-story').focus()
                page.keyboard.press('ArrowRight')
                expect(page.locator('#tab-prompts')).to_be_focused()
                expect(page.locator('.clip')).to_have_count(2)
                page.locator('#limit').select_option('10')
                expect(page.locator('.clip')).to_have_count(3)
                for model in ('minimax-h3-text', 'seedance-2-text', 'ltx-2.5-text'):
                    page.locator('#model').select_option(model)
                    expect(page.locator('.clip')).to_have_count(3)
                page.locator('#model').select_option('minimax-h3-text')
                page.locator('.clip-header button').first.click()
                expect(page.locator('#status')).to_have_text('Prompt copied.')
                copied = page.evaluate('navigator.clipboard.readText()')
                assert 'Still raining.' in copied and '<d>' in copied
                page.locator('.clip input').nth(2).uncheck()
                page.locator('#add-nodes').click()
                expect(page.locator('.node-pair')).to_have_count(2)
                # A node can choose a different saved clip without generating anything.
                page.locator('.node select').first.select_option('C03')
                expect(page.locator('.preview-node .node-body').first).to_contain_text("Yes. I'd like that.")
                with page.expect_download() as download:
                    page.locator('#export-workflow').click()
                exported = artifacts / 'demo-exported-workflow.json'
                download.value.save_as(exported)
                workflow = json.loads(exported.read_text(encoding='utf-8'))
                assert len(workflow['links']) == 2
                snapshots = [decode_snapshot(n['widgets_values'][0]) for n in workflow['nodes'] if n['type'] == 'StoryboardClipPrompt']
                assert [c['clip_id'] for c in snapshots] == ['C03', 'C02']
                assert all(n['type'] in ('StoryboardClipPrompt', 'PreviewAny') for n in workflow['nodes'])
                page.screenshot(path=str(artifacts / 'demo-nodes-desktop.png'), full_page=True)
                page.locator('#tab-prompts').click()
                with page.expect_download() as download:
                    page.locator('#download-txt').click()
                text_file = artifacts / 'demo-exported-prompts.txt'
                download.value.save_as(text_file)
                assert copied.replace('\r\n', '\n') in text_file.read_text(encoding='utf-8')
                page.locator('#limit').select_option('15')
                page.locator('#add-nodes').click()
                expect(page.locator('.node-pair')).to_have_count(4)
                page.locator('#tab-prompts').click()
                page.locator('#add-nodes').click()
                expect(page.locator('.node-pair')).to_have_count(4)  # Dedupe unchanged identities.
                page.locator('.node-title button').first.click()
                expect(page.locator('.node-pair')).to_have_count(3)
                for language in ('en', 'ko', 'ja'):
                    page.locator('#language').select_option(language)
                    expect(page.locator('html')).to_have_attribute('lang', language)
                    # Existing nodes retain the conversion they came from.
                    expect(page.locator('.node-pair')).to_have_count(3)
                    for width in (390, 768, 1440):
                        page.set_viewport_size({'width': width, 'height': 1000})
                        for tab in ('story', 'prompts', 'nodes'):
                            page.locator('#tab-' + tab).click()
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (language, width, tab)
                    page.screenshot(path=str(artifacts / ('demo-' + language + '.png')), full_page=True)
                page.reload()
                expect(page.locator('html')).to_have_attribute('lang', 'ja')
                expect(page.locator('.shot-card')).to_have_count(6)
                page.locator('#tab-nodes').click()
                expect(page.locator('#node-empty')).to_be_visible()  # Only language persists.
                page.locator('#reset').click()
                expect(page.locator('#story-panel')).to_be_visible()
                assert not errors, errors
                assert all(method == 'GET' and address.startswith(url) for method, address in requests), requests
                print('PASS: real formatter samples, 3 languages, clipboard, TXT, signed snapshots, workflow connections, node selection/dedupe, keyboard and 27 responsive views; no API calls or uploads.')
            except Exception:
                page.screenshot(path=str(artifacts / 'demo-failure.png'), full_page=True)
                raise
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == '__main__':
    main()
