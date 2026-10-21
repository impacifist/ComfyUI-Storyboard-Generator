# v0.1.4-beta — Review shot-count differences inside ComfyUI

## English

- Includes the v0.5.8-beta shared engine and a dark-theme preview showing requested/generated shot counts and total duration.
- Choose **Use this draft** to accept without an extra AI request, **Generate again** to retry, or download the draft JSON. A failed retry keeps the previous draft available.
- Acceptance updates the shot-count setting and saves a new storyboard. Existing saved storyboards, portable STRING nodes and workflow connections remain unchanged.
- Unaccepted drafts live only in the current page session. Use or download before refreshing. Only otherwise valid, complete results with 3–60 shots are recoverable; incomplete batches, invalid data and missing locked shots remain errors.

Validation: 25 addon tests and 203 shared-engine tests; Ruff and JavaScript checks; browser generation-choice and existing workflow regressions; isolated real ComfyUI verification of acceptance/save, dark contrast, mobile layouts, STRING queueing and workflow reload. AI requests are mocked; no paid AI or video generation was run. Release archives exclude private settings, API keys, databases and generated media.

Update the node pack, restart ComfyUI, then refresh the browser with Ctrl+F5.

## 한국어

요청한 컷 수와 다르게 생성된 완전하고 유효한 결과를 미리 확인하고 **이 결과 사용**, **다시 생성**, JSON 다운로드 중에서 선택할 수 있습니다. 수락 시 추가 AI 호출 없이 새 콘티로 저장합니다. 재생성에 실패해도 기존 초안은 유지됩니다. 기존 저장 콘티와 STRING 노드·연결은 유지됩니다.

미선택 초안은 새로고침 전에 사용하거나 다운로드하세요. 불완전한 생성이나 잘못된 데이터, 고정 컷 누락은 계속 차단합니다. 총 228개 단위 테스트와 실제 ComfyUI의 모의 AI 연동 검증을 통과했습니다. 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요.

## 日本語

完全で有効な結果のカット数が依頼と異なる場合、プレビューを確認して**この下書きを使う**、**再生成**、JSONダウンロードを選べます。確定すると追加のAI呼び出しなしに新しいストーリーボードとして保存します。再試行に失敗しても前の下書きは残ります。保存済みの内容とSTRINGノード・接続は維持されます。

未確定の下書きは再読み込み前に使用するかダウンロードしてください。不完全な生成、不正なデータ、固定カットの欠落は引き続きエラーです。合計228件の単体テストと実際のComfyUIでの模擬AI連携検証を通過しました。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。
