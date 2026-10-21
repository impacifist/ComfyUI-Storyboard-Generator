# v0.1.5-beta — Keep conversion shots aligned with the plan

## English

- Bundles the v0.5.9-beta shared engine with an explicit per-clip source shot contract and schema-bound IDs for H3, Seedance and LTX conversion.
- Restores only complete, unique ID permutations without an extra AI call. A visible notice explains the restoration. Whole direction objects and original dialogue/speaker bindings remain together.
- Missing, duplicate, renamed or misplaced entries still require a valid AI correction. The one-repair budget is unchanged; errors now identify the affected clip, expected/returned IDs and counts. Failed conversions preserve saved storyboards and prior conversions.
- Portable STRING nodes, saved snapshots and existing workflow wires remain unchanged. Reconvert to use the new compiler instructions.

Validation: 212 shared-engine tests and 27 addon tests, including saved-result/STRING preservation, four AI adapters, all three video guides and synthetic long multi-person plans; Ruff, JavaScript checks, browser conversion and isolated real ComfyUI checks for restoration notices, dark surfaces, languages, mobile layout, queueing and workflow reload. AI and unload requests are mocked; actual AI/video quality is not verified. Release archives exclude private settings, API keys, databases and generated media.

Update the node pack, restart ComfyUI and refresh with Ctrl+F5.

## 한국어

클립별 원본 컷 ID 규칙을 강화하고, ID가 정확히 대응하는 단순 순서 변경은 추가 AI 호출 없이 복원하도록 개선했습니다. 누락·중복·임의 번호 변경은 계속 검증하며, 오류와 자동 교정 요청에 예상·응답 컷 목록을 구체적으로 표시합니다. 기존 콘티·변환 결과·STRING 노드와 연결은 유지됩니다.

총 239개 단위 테스트와 실제 ComfyUI의 모의 AI 연동 검증을 통과했습니다. 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요. 새 규칙은 다시 변환할 때 적용됩니다.

## 日本語

クリップごとの元のカットID規則を強化し、IDが完全に対応する単純な順序変更のみ追加のAI呼び出しなしに復元します。欠落・重複・勝手な番号変更は引き続き検証し、エラーと自動修正依頼に予定・応答カット一覧を具体的に表示します。既存のストーリーボード・変換結果・STRINGノードと接続は維持されます。

合計239件の単体テストと実際のComfyUIでの模擬AI連携検証を通過しました。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。新しい規則は再変換時に適用されます。
