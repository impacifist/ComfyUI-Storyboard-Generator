# v0.1.9-beta — Directional clip connections without duplicated action bridges

## English

- Includes the v0.5.13-beta engine and assembly version 9. Removes free-form LLM handoff prose that was previously inserted at both ends of a clip connection.
- Uses distinct renderer-owned incoming/outgoing scope rules for continuous shots, planned cuts and scene changes. Each concrete action stays with its assigned shot; inherited states are already established, not commands to perform the establishing action again. The compiler also guards context, summaries and identity fields against anticipating future behavior.
- Exposes `handoff_policy` alongside request/output inspection records. The public authored sample uses the same new formatter and clip-specific summaries.
- Preserves existing signed STRING nodes, wires and saved conversions. Restart ComfyUI, refresh with Ctrl+F5, **reconvert**, then explicitly add/update the desired clip prompt nodes. Old saved prompts are not automatically rewritten. Sampling, motion-context frames, trimming and video node settings are unchanged.

Validation: 231 shared-engine and 36 addon tests (267 total), Ruff and JavaScript checks; browser conversion/inspection/export and static-demo regressions; isolated real ComfyUI loading, STRING queueing, workflow reload, dark surfaces and mobile checks. Synthetic timing/action tests use mocked AI and cover all six guide modes. Actual rendered continuity is not verified. Release ZIPs exclude private settings, API keys, saved databases and generated media.

## 한국어

같은 연결용 행동 문장을 양쪽 클립에 반복 삽입하던 처리를 제거했습니다. 프로그램이 이전 클립의 종료 범위와 다음 클립의 시작 범위를 구분하고, 연속 동작·컷 전환·장면 전환을 다르게 처리합니다. LLM 전송 이력 보기에서 추가된 연결 규칙도 확인할 수 있습니다.

총 267개 단위 테스트와 브라우저·실제 ComfyUI 검증을 통과했습니다. 실제 영상에서의 반복 동작 해소는 새 생성으로 확인해야 합니다. 업데이트 후 ComfyUI 재시작·Ctrl+F5를 하고 **프롬프트 재변환 → 사용할 클립 노드 추가·업데이트**를 진행하세요. 기존 저장 프롬프트와 노드 연결은 자동으로 바뀌지 않습니다.

## 日本語

同じ接続用の動作文を両方のクリップへ繰り返し挿入する処理を廃止しました。プログラムが前のクリップの終了範囲と次のクリップの開始範囲を区別し、連続動作・カット切り替え・場面転換をそれぞれ処理します。LLM入力・出力の確認画面で追加された接続規則も確認できます。

合計267件の単体テストとブラウザー・実際のComfyUI検証を通過しました。実際の動画での反復解消は新しい生成で確認してください。更新後はComfyUI再起動・Ctrl+F5を行い、**プロンプト再変換 → 使用するクリップノードの追加・更新**を実施してください。保存済みプロンプトとノード接続は自動変更されません。
