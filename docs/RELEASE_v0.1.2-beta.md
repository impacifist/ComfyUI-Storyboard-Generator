# v0.1.2-beta

Adds LTX 2.5 prompt conversion and fixes light surfaces inside the dark ComfyUI workbench.

## Changes

- Bundles the standalone v0.5.6-beta engine, pinned to `5f10f8694c7340ac2305ea6d4522afe39f2893fe` with 36 verified file hashes.
- Offers LTX 2.5 text and starting-image modes, using locally reviewed official guidance and a dedicated compiler policy. Prompts use chronological English prose with original dialogue in quotation marks, approved edits and audio continuity.
- Preserves per-clip copy, TXT/JSON exports, portable STRING snapshots and existing MiniMax/Seedance modes. Queueing saved prompt nodes does not call an LLM.
- Corrects CSS specificity for library backgrounds, guide/output panes and input fields, and adjusts metadata colors for the dark theme.
- Start images remain external: connect them separately in the video workflow. The 4–15-second planner range is an application policy, not LTX's maximum. Set frames/FPS in the rendering workflow and disable Prompt Enhance to evaluate the exact generated wording.

## Validation and scope

22 addon unit tests, Ruff, JavaScript syntax and all vendor hashes are checked. Isolated real-ComfyUI smoke checks cover library/conversion colors and text contrast, LTX selection, exact clipboard contents, portable nodes, wires, reload, real STRING execution, mocked Ollama unload, languages and mobile. The shared engine has 179 unit tests and browser conversion checks covering both LTX modes and existing model behavior. AI responses are mocked; actual LTX video quality and seamless joins are not verified.

Release archives exclude keys and private settings. No new credential fields or runtime dependencies are added. Local API-key storage remains plaintext.

Update the node pack, restart ComfyUI and refresh the browser with Ctrl+F5. The update does not alter your video workflows or download LTX models.

## 한국어

LTX 2.5 텍스트·시작 이미지 기반 프롬프트 변환을 추가하고, 보관함과 변환 화면의 흰 배경·글자 대비를 수정했습니다. 클립별 복사와 STRING 출력은 그대로 지원합니다. 시작 이미지는 영상 워크플로우에서 직접 연결하며, 현재 4~15초 분할 범위는 앱 정책입니다. 실제 영상 품질은 미검증입니다. 노드 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요.

## 日本語

LTX 2.5のテキスト・開始画像向けプロンプト変換を追加し、ライブラリと変換画面の白い背景・文字のコントラストを修正しました。クリップごとのコピーとSTRING出力にも対応します。開始画像は動画ワークフローで直接接続してください。現在の分割範囲4〜15秒はアプリ側の設定です。実際の動画品質は未検証です。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。
