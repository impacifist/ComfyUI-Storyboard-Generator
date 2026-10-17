# v0.1.1-beta

Each clip in the conversion panel now has a **Copy prompt** button. It copies only that clip's prompt body, with its original dialogue, even when the clip details are collapsed. All-clips TXT/JSON/ZIP exports remain available. Clipboard success and failure are displayed, with a selection-based fallback.

The pinned engine/UI snapshot is updated to standalone v0.5.5-beta. English, Korean and Japanese READMEs now show matching real ComfyUI interfaces and authored story examples, including separate clip nodes connected to STRING inputs. Public sample JSON files and a reproducible capture script are included. AI responses in documentation are mocked; no live model quality is claimed.

Validation: 21 unit tests, Ruff, JavaScript syntax, all 34 vendor checksums and three localized ComfyUI showcase runs passed. Each run compared both clip copies against the actual clipboard and checked copying a collapsed clip. Publication files were scanned for credential patterns and private-data paths. API configuration responses, diagnostics and node snapshot boundaries retain their existing secret-redaction checks. Local API settings remain plaintext; no encryption guarantee is made.

Update the node pack, restart ComfyUI and hard-refresh the browser. Back up your local settings and library before replacing installation files.

## 한국어

변환 결과에서 클립마다 **프롬프트 복사** 버튼을 사용할 수 있습니다. 접힌 클립도 바로 복사하며, 전체 TXT·JSON·ZIP 다운로드는 유지합니다. 세 언어의 설명서와 예시 화면을 각 언어로 맞췄습니다.

## 日本語

変換結果の各クリップに**プロンプトをコピー**ボタンを追加しました。閉じたクリップからも本文だけをコピーできます。英語・韓国語・日本語の説明書には、それぞれ同じ言語のUIとサンプルを掲載しています。
