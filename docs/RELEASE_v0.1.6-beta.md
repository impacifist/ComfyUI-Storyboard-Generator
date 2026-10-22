# v0.1.6-beta — Targeted English instruction repair

## English

- Includes the v0.5.10-beta shared engine. Completed direction drafts with non-English delivery/camera/action instructions can use the existing single repair attempt to translate only the affected instruction fields, rather than requesting the entire direction object again.
- Source dialogue, IDs, approved clip structure, valid fields and warnings are preserved. Translation responses must match the exact requested keys, remain nonempty where required and pass the English policy; the final assembled result is fully revalidated before saving. No partial result is saved on failure.
- Shows a translated-field count in the panel and preserves the prior shot-order restoration notice when both repairs apply. Existing STRING snapshots, nodes, connections and saved conversions remain unchanged.
- The initial generation plus at most one repair remains the limit. Targeted translation handles up to 100 affected strings. Other validation failures retain the full-object repair path. No English-policy relaxation or automatic retry loop is added.

Validation: 220 shared-engine and 29 addon unit tests; four AI adapters and three video-model guides; browser conversion/save, three-language responsive checks and isolated real ComfyUI panel/STRING/workflow tests. AI responses and unload requests are mocked. Actual Gemma generation and video quality are not verified. ZIPs exclude API keys, private settings, databases and generated media.

Update the node pack, restart ComfyUI and refresh with Ctrl+F5.

## 한국어

영어로 변환되지 않은 연기·카메라·행동 지시만 부분 번역하고 전체 결과를 다시 검증하도록 개선했습니다. 원본 대사·컷 구성·화자 연결과 기존 경고는 유지하며, 교정은 최대 1회입니다. 화면에서 교정한 문구 수를 확인할 수 있습니다. 기존 STRING 노드와 연결, 저장 결과는 유지됩니다.

총 249개 단위 테스트와 실제 ComfyUI 패널 검증을 통과했습니다. AI 응답은 모의 테스트이며 실제 젬마 모델 실행은 포함하지 않습니다. 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요.

## 日本語

英語になっていない演技・カメラ・動作指示のみを部分翻訳し、全体を再検証します。元のセリフ、カット構成、話者の対応と警告を維持し、自動修正は最大1回です。パネルに翻訳した指示文の件数を表示します。既存のSTRINGノード、接続と保存済みの結果は維持されます。

合計249件の単体テストと実際のComfyUIパネル検証を通過しました。AI応答は模擬テストで、実際のGemmaモデルの実行は含みません。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。
