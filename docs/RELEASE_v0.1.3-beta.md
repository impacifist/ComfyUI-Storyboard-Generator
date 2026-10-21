# v0.1.3-beta — Speaker binding, grouped references and conversion layout

## English

- Bundles the unmodified v0.5.7-beta engine with verified hashes in `_vendor/upstream.json`.
- Strengthens original-speaker attribution for H3, Seedance and LTX, with explicit H3 Subject/speaker binding and separate off-screen/voiceover instructions. Saved results require reconversion to use the new assembly.
- Adds Character, Background, Prop and Other references, grouped images per target and optional shot selection in H3/Seedance reference mode. Prop association does not change approved holders, actions or transfers. LTX retains its separate starting-image mode.
- Fixes the conversion view shrinking to a centered column before results exist. Settings/references stay on the left and prompts on the right, using the panel width in both states. The settings pane grows with the window; the primary action stays at the bottom. Fixes selected reference button contrast.
- Preserves existing portable STRING snapshots, wires, clipboard contents and queue behavior. Images are attached to video workflows separately; no video rendering or image analysis is added.

Validation: 24 addon tests and 193 shared-engine tests; Ruff and JavaScript checks; browser reference/TXT/ZIP checks; isolated real ComfyUI tests for empty and populated conversion views, three languages, 1440/1920/2560 desktop widths and mobile, dark contrast, real STRING queueing and workflow reload. AI/Ollama lifecycle requests are mocked; actual video quality is not verified. Archives exclude API keys, settings, databases and generated artifacts.

Update the node pack, restart ComfyUI, then refresh the browser with Ctrl+F5. Existing prompts remain available; reconvert selected storyboards to apply the new attribution rules.

## 한국어

화자 연결 개선, 인물·배경·소품·그 외 레퍼런스 분류와 대상별 이미지 묶음·적용 컷 선택을 반영했습니다. 변환 전 화면이 가운데로 좁아지는 문제를 수정하고 왼쪽 설정·오른쪽 결과 배치를 유지합니다. 저장된 STRING 노드와 연결은 유지되며 이미지 연결은 영상 워크플로우에서 별도로 처리합니다.

노드 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요. 새 화자 규칙을 적용하려면 다시 변환하세요. 총 217개 단위 테스트와 실제 ComfyUI의 모의 AI 연동 검증을 통과했으며, 실제 영상 품질은 미검증입니다.

## 日本語

話者の対応を強化し、人物・背景・小物・その他の参考画像、対象ごとの画像グループ、適用カット指定を追加しました。変換前の画面が中央の狭い列になる問題を修正し、左側の設定・右側の結果という配置を維持します。既存のSTRINGノードと接続は維持されます。画像は動画ワークフローへ別途接続してください。

更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。新しい話者ルールには再変換が必要です。合計217件の単体テストと実際のComfyUIでの模擬AI連携検証を通過しています。実際の動画品質は未検証です。
