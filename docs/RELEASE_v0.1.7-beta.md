# v0.1.7-beta — Cleaner review and an interactive sample

## English

- Includes the v0.5.11-beta shared engine. Removes review warnings based only on literal differences between adjacent character/prop state descriptions. Original state data, editing and conversion validation are preserved. Reload or review an existing storyboard to apply the new review logic.
- Adds a no-install [interactive sample](https://impacifist.github.io/ComfyUI-Storyboard-Generator/) in English, Korean and Japanese: inspect fixed authored shots, compare H3/Seedance/LTX prompts with 10/15-second clip budgets, copy/download text and export real Storyboard Clip Prompt → Preview Any workflow connections. The sample does not call an AI or generate video.
- Makes vendor archive hashes consistent across Windows/Linux and adds a regression test. Existing STRING snapshots, workflow connections and saved conversions are preserved.

Validation: 220 shared-engine and 34 addon unit tests; Ruff and JavaScript checks; browser review/edit/export and three-language checks. The sample's workflow import and exact STRING output were also verified in isolated ComfyUI. AI responses in integration checks are mocked; video quality is not verified. Release archives exclude API keys, private settings, databases and generated media.

Update the node pack, restart ComfyUI and refresh with Ctrl+F5. Existing storyboards do not need regeneration.

## 한국어

인물·소품의 상태 설명 차이만으로 띄우던 자동 경고를 제거했습니다. 기존 콘티를 다시 생성할 필요 없이 불러오거나 다시 검수하면 적용됩니다. 상태 데이터와 변환 검증, 저장된 STRING 노드 및 연결은 유지됩니다.

설치 없이 살펴볼 수 있는 3개 언어의 예시 체험 페이지를 추가하고 Windows·Linux의 공유 코드 해시 검증을 통일했습니다. 체험 페이지는 고정된 예시를 사용하며 실제 AI·영상 생성은 하지 않습니다. 총 254개 단위 테스트와 브라우저 검증을 통과했습니다. 업데이트 후 ComfyUI를 재시작하고 Ctrl+F5로 새로고침하세요.

## 日本語

人物・小物の状態の記述が異なるだけで表示していた自動警告を削除しました。既存のストーリーボードを再生成する必要はなく、読み込み直すか再検証すると適用されます。状態データ、変換の検証、保存済みSTRINGノードと接続は維持されます。

インストール不要の3言語サンプルページを追加し、Windows・Linuxで共有コードのハッシュ検証を統一しました。体験ページは固定サンプルで、実際のAI・動画生成は行いません。合計254件の単体テストとブラウザー検証を通過しました。更新後はComfyUIを再起動し、Ctrl+F5で再読み込みしてください。
