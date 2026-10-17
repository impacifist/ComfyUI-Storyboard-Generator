# 커뮤니티 소개 준비

## 어디에 어떻게 소개할지

첫 소개는 ComfyUI판을 중심으로 r/comfyui에 올리는 구성을 권장합니다. 캐릭터 설정 → 콘티 수정 → 15초 클립 두 개 → STRING 노드 연결까지 한 화면 흐름으로 보여주세요. 웹 앱은 ComfyUI 없이 쓸 수 있는 대안으로 본문 끝에 연결하면 됩니다. 서로 다른 두 제품의 기능 목록을 처음부터 모두 나열할 필요는 없습니다.

일본어 소개는 X의 짧은 사용 화면과 일본어 README를 연결하고, Qiita나 Zenn에는 설치법과 설계 설명을 담은 튜토리얼로 구성하는 편이 좋습니다. Qiita는 홍보·판매를 주목적으로 하는 글을 금지하지만 자작 기술의 설명을 주목적으로 하는 글은 구분합니다. Zenn도 기술 지식 공유를 중심으로 하고 제품 홍보가 주목적인 글은 피하도록 안내합니다.

- [Qiita 공식 커뮤니티 가이드](https://help.qiita.com/ja/articles/qiita-community-guideline)
- [Zenn 공식 커뮤니티 가이드](https://zenn.dev/guideline)
- [r/comfyui 규칙](https://www.reddit.com/r/comfyui/about/rules/)
- [r/StableDiffusion 규칙](https://www.reddit.com/r/StableDiffusion/about/rules/)

레딧 규칙 페이지의 세부 내용은 이번 조사에서 로그인 없이 확인하지 못했습니다. 게시 당일 직접 규칙과 플레어를 확인하세요. 같은 글을 여러 곳에 연속 게시하기보다는 첫 사용자의 설치·동작 피드백을 반영한 뒤 다음 채널로 넓히는 방식이 적절합니다.

## 보여줄 순서

1. 어떤 문제를 해결하는지 한 문장: 인물 설정을 콘티와 클립별 영상 프롬프트로 연결한다.
2. 해당 언어의 제작 화면: 성격·말투 입력과 컷별 결과를 함께 보여준다.
3. 변환 화면: 30초 콘티를 15초 두 클립으로 나누고 개별 복사 버튼을 사용한다.
4. ComfyUI 연결 화면: 각 클립을 별도 STRING 노드로 연결한다.
5. GitHub, 설치법, 일본어/영어 README, 구체적인 피드백 질문을 덧붙인다.

지금 공개된 예시는 직접 작성한 콘티와 모의 AI 변환을 사용합니다. 이를 실제 AI 생성 결과나 완성 영상으로 소개하지 마세요. 실제 모델로 만든 예시를 준비하면, 사용자가 넣은 설정 → 생성된 콘티 → 수정한 부분 → 실제 영상 순으로 별도 사례를 추가할 수 있습니다. 앱 자체와 사용 모델의 비용도 구분하세요. 저장소에 라이선스가 정해지기 전에는 "open source" 대신 "source available on GitHub"로 표현하는 것이 현재 설명과 맞습니다.

## Reddit 영문 초안

**Title:** I built a ComfyUI panel that turns character personas into storyboards and clip-by-clip video prompts

I made Storyboard Generator to keep character settings, storyboard editing and video prompt preparation in one workflow.

Inside ComfyUI, you can define 1–5 characters, review and edit the shots, then convert selected shots into MiniMax H3 or Seedance prompts. You can adjust clip lengths, copy each clip separately, or add clips as individual STRING nodes and connect them to your video workflow.

It supports OpenAI, Claude, Ollama, LM Studio and compatible endpoints. The interface and guides are available in English, Korean and Japanese. There is also a standalone local web app if you do not use ComfyUI.

The screenshots show the actual UI with authored sample content and mocked conversion responses. This tool prepares storyboards and prompts; it does not render videos. It is an early beta, and I would especially appreciate feedback on clip planning, Japanese dialogue and installation compatibility.

ComfyUI version: https://github.com/impacifist/ComfyUI-Storyboard-Generator

Standalone app: https://github.com/impacifist/ai-video-storyboard-generator

## 日本語の紹介文案

**タイトル：** ComfyUIでキャラクター設定からストーリーボードと動画用プロンプトを作るツールを公開しました

キャラクター設定、カットごとの確認・修正、動画プロンプトへの変換を一つの流れで扱える「Storyboard Generator」を作りました。

登場人物は1〜5人まで設定できます。ストーリーボードを確認してからMiniMax H3／Seedance向けに変換し、クリップの長さを調整したり、個別にプロンプトをコピーしたりできます。ComfyUIではクリップごとにSTRINGノードを追加して、動画ワークフローへ接続できます。

OpenAI、Claude、Ollama、LM Studioなどに対応しています。日本語UI・日本語の説明書とサンプルも用意しました。ComfyUIを使わない方向けには、ローカルWebアプリ版もあります。

掲載画像は実際のUIですが、内容は手作業のサンプルとテスト用の模擬AI応答です。動画そのものを生成するツールではありません。まだベータ版なので、クリップ分割や日本語のセリフ、導入時に気づいた点を教えていただけると助かります。

ComfyUI版：https://github.com/impacifist/ComfyUI-Storyboard-Generator/blob/main/README.ja.md

Webアプリ版：https://github.com/impacifist/ai-video-storyboard-generator/blob/main/README.ja.md

Qiita／Zennに投稿する場合は、この短い紹介文だけではなく、導入手順、元の設定、カット編集、ノード接続、実装上の工夫まで説明する記事にしてください。
