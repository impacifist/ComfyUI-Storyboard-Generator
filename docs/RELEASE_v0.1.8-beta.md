# v0.1.8-beta — Inspect and edit LLM conversion input

## English

- Includes the v0.5.12-beta shared engine. Adds a dark-theme **Inspect / edit LLM input** dialog with clip/shot action assignment, original source offsets, assigned dialogue, editable system/user input and a read-only schema.
- Segment directions and descriptive edits apply only to this conversion. Original speech/speakers, IDs, timings, state and reference bindings remain protected. Preview and validation do not call an AI; stale edits are rejected before sending. Normal conversion consent is required again after edits.
- Successful new conversions save actual logical requests and parsed JSON outputs, including bounded repairs, for inspection/download. No API keys or authentication headers are included. Source stories and personas may be present, so keep private traces local. Existing conversions are preserved and have no retroactive trace.
- Clarifies that an unedited split-shot action list is whole-source context. Preserves existing STRING snapshots, connections and queue behavior. No video generation or ComfyUI execution is added to the public static sample.

See the [inspection guide](_vendor/docs/guides/request-inspection.md) in the repository root. Applied input edits are page-session state, not permanent storyboard edits.

Validation: 226 shared-engine and 35 addon tests; Ruff and JavaScript checks; browser inspection/edit/compile/history/download and stale-edit tests; isolated real ComfyUI routes/panel, dark contrast, mobile layout, STRING queueing and workflow reload. AI responses and model-unload requests are mocked. Actual video quality is not verified. Release archives exclude private settings, API keys, saved databases and generated media.

Update the node pack, restart ComfyUI and refresh with Ctrl+F5. Reconvert to capture new request/output traces.

## 한국어

변환 설정에 **LLM 전송 내용 확인·수정**을 추가했습니다. 클립별 행동·원본 시간 범위·대사를 확인하고 구간별 지시와 시스템·사용자 요청을 수정할 수 있습니다. 확인·검증은 AI를 호출하지 않으며, 수정 후 전송 동의를 다시 선택해야 합니다. ID·시간·원본 대사·화자·상태·레퍼런스 연결은 보호합니다.

새 변환의 실제 논리 요청·JSON 응답 이력을 결과에서 비교·다운로드할 수 있습니다. 원본 콘티와 기존 STRING 노드·연결은 유지됩니다. 기록에는 이야기·페르소나가 포함될 수 있으므로 비공개 자료는 로컬에 보관하세요. 총 261개 단위 테스트와 브라우저·실제 ComfyUI 검증을 통과했습니다. 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요. 새 기록을 보려면 다시 변환해야 합니다.

## 日本語

変換設定に**LLMへの入力を確認・編集**を追加しました。クリップごとの動作・元の時間範囲・セリフを確認し、区間の指示とシステム・ユーザー入力を編集できます。確認・検証ではAIを呼び出さず、変更後は送信への同意が再度必要です。ID・時間・元のセリフ・話者・状態・参考画像の対応は保護します。

新しい変換の論理入力とJSON応答を結果から比較・ダウンロードできます。元のストーリーボード、既存のSTRINGノードと接続は維持されます。記録には物語・人物設定が含まれる場合があるため、非公開資料はローカルで保管してください。合計261件の単体テストとブラウザー・実際のComfyUI検証を通過しました。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。新しい記録には再変換が必要です。
