import {makeWorkflow} from "./workflow.js";

const copy = {
  sample: ["Interactive sample", "체험용 예시", "体験サンプル"],
  install: ["Install in ComfyUI ↗", "ComfyUI에 설치 ↗", "ComfyUIにインストール ↗"],
  notice: ["Explore an authored sample. No AI calls, API keys or uploads. Generation and execution require the installed app.", "미리 작성한 예시를 체험합니다. AI 호출·API 키·업로드가 없습니다. 실제 생성과 실행은 설치한 앱에서 가능합니다.", "事前に作成したサンプルを体験できます。AI呼び出し・APIキー・アップロードはありません。実際の生成と実行にはアプリのインストールが必要です。"],
  scenario: ["SAMPLE SCENARIO", "예시 설정", "サンプル設定"], reset: ["Reset", "초기화", "リセット"],
  duration: ["Duration", "길이", "長さ"], shots: ["Shots", "컷 수", "カット数"],
  characters: ["Characters", "등장인물", "登場人物"], scene: ["Scene & direction", "상황과 연출", "場面と演出"],
  asideHelp: ["These personas and shots are a fixed example. Install the app to create stories from your own characters.", "인물과 콘티는 고정된 예시입니다. 직접 설정한 인물로 이야기를 만들려면 앱을 설치하세요.", "人物設定とカットは固定サンプルです。自分のキャラクターで物語を作るにはアプリをインストールしてください。"],
  story: ["Storyboard", "콘티", "ストーリーボード"], prompts: ["Video prompts", "영상 프롬프트", "動画プロンプト"], nodes: ["STRING nodes", "STRING 노드", "STRINGノード"],
  storyTitle: ["A story, shot by shot", "컷으로 살펴보는 이야기", "カットごとに見る物語"],
  storyHelp: ["Open a shot to inspect its acting, dialogue and camera direction.", "컷을 눌러 행동·대사·카메라 연출을 확인하세요.", "カットを開いて演技・セリフ・カメラ演出を確認できます。"],
  seePrompts: ["See video prompts →", "영상 프롬프트 보기 →", "動画プロンプトを見る →"],
  promptsTitle: ["From shots to video prompts", "콘티를 영상 프롬프트로", "カットから動画プロンプトへ"],
  promptHelp: ["Compare sample outputs built with the real formatter. Model choice changes the syntax.", "실제 변환 코드로 구성한 예시입니다. 모델을 바꾸면 해당 형식의 프롬프트를 볼 수 있습니다.", "実際の整形コードで構成したサンプルです。モデルを変えると対応する形式のプロンプトを確認できます。"],
  downloadTxt: ["Download TXT", "TXT 다운로드", "TXTをダウンロード"], model: ["Video model", "영상 모델", "動画モデル"],
  clipLength: ["Maximum clip length", "클립 최대 길이", "クリップの最大長"],
  addNodes: ["Add selected clips as nodes →", "선택한 클립을 노드로 추가 →", "選択クリップをノードに追加 →"],
  nodesTitle: ["One clip. One STRING output.", "클립마다 하나의 STRING 출력", "クリップごとにSTRING出力"],
  nodeHelp: ["Connection preview: saved prompt → Preview Any. Video sampling is not running in this page.", "연결 미리보기: 저장된 프롬프트 → Preview Any. 이 페이지에서 영상 샘플링을 실행하지 않습니다.", "接続プレビュー：保存したプロンプト → Preview Any。このページでは動画のサンプリングは実行しません。"],
  exportWorkflow: ["Download workflow JSON", "워크플로우 JSON 다운로드", "ワークフローJSONをダウンロード"],
  noNodes: ["Choose the clips you want to use", "사용할 클립을 선택하세요", "使用するクリップを選択してください"],
  noNodesHelp: ["Add them from Video prompts, then connect each saved prompt to your video workflow.", "영상 프롬프트에서 클립을 추가하고 각 프롬프트를 영상 워크플로우에 연결합니다.", "動画プロンプトからクリップを追加し、それぞれを動画ワークフローに接続します。"],
  chooseClips: ["Choose clips", "클립 선택", "クリップを選択"],
  workflowHelp: ["The downloaded workflow contains real Storyboard Clip Prompt → Preview Any connections. Install the custom node pack before opening it in ComfyUI. Running these nodes reads saved text; it does not generate video or call an LLM.", "다운로드한 워크플로우에는 실제 Storyboard Clip Prompt → Preview Any 연결이 들어 있습니다. 커스텀 노드를 설치한 뒤 ComfyUI에서 여세요. 실행하면 저장된 텍스트를 출력하며 영상 생성이나 LLM 호출은 하지 않습니다.", "ダウンロードしたワークフローには実際のStoryboard Clip Prompt → Preview Any接続が入っています。カスタムノードをインストールしてからComfyUIで開いてください。実行すると保存テキストを出力します。動画生成やLLM呼び出しは行いません。"],
  close: ["Close", "닫기", "閉じる"], personality: ["Personality", "성격", "性格"], speech: ["Speaking style", "말투", "話し方"],
  desire: ["Wants", "바라는 것", "望み"], fear: ["Concern", "걱정", "不安"], habit: ["Habit", "습관", "癖"], fixed: ["Appearance", "외형", "外見"],
  location: ["Location", "장소", "場所"], intent: ["Interaction", "상호작용", "やり取り"], ending: ["Ending", "결말", "結末"],
  visual: ["Composition", "화면 구성", "画面構成"], actions: ["Acting", "행동", "演技"], dialogue: ["Dialogue", "대사", "セリフ"],
  camera: ["Camera", "카메라", "カメラ"], copy: ["Copy prompt", "프롬프트 복사", "プロンプトをコピー"],
  copied: ["Prompt copied.", "프롬프트를 복사했습니다.", "プロンプトをコピーしました。"],
  copyFailed: ["Copy failed. Open the prompt and select its text, or download TXT.", "복사하지 못했습니다. 프롬프트를 펼쳐 선택하거나 TXT를 내려받으세요.", "コピーできませんでした。プロンプトを開いて選択するか、TXTをダウンロードしてください。"],
  expand: ["Read prompt", "프롬프트 펼치기", "プロンプトを読む"],
  clips: ["clips", "개 클립", "クリップ"], selected: ["selected", "개 선택", "件選択中"],
  removed: ["Node removed.", "노드를 제거했습니다.", "ノードを削除しました。"],
  remove: ["Remove node", "노드 삭제", "ノードを削除"],
  added: ["Selected clips added. Each node keeps its own saved prompt.", "선택한 클립을 추가했습니다. 노드마다 해당 클립의 프롬프트가 저장됩니다.", "選択クリップを追加しました。各ノードに個別のプロンプトが保存されます。"],
  resetDone: ["Sample reset. No files or settings were changed.", "예시를 초기화했습니다. 파일과 실제 설정에는 영향이 없습니다.", "サンプルをリセットしました。実際のファイルや設定は変更していません。"],
  loading: ["Loading the sample…", "예시를 불러오는 중…", "サンプルを読み込み中…"],
  loadFailed: ["Could not load the sample. Refresh the page to try again.", "예시를 불러오지 못했습니다. 새로고침 후 다시 시도하세요.", "サンプルを読み込めませんでした。再読み込みしてください。"],
};
const $ = s => document.querySelector(s);
const el = (tag, cls, text) => { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; };
let language = "en";
try { if (["en", "ko", "ja"].includes(localStorage.getItem("storyboard.sample.language"))) language = localStorage.getItem("storyboard.sample.language"); } catch { /* Optional browser preference only. */ }
const t = key => copy[key][language === "ko" ? 1 : language === "ja" ? 2 : 0];
let data, selected = new Set(), nodeClips = [], activeTab = "story", loading = true;
const sample = () => data.samples[language];
const bundle = () => sample().variants[`${$("#model").value}:${$("#limit").value}`];
const status = text => { $("#status").textContent = text; };
function field(parent, label, value) { const dl = el("dl", "field"); dl.append(el("dt", "", label), el("dd", "", value)); parent.append(dl); }
function button(text, handler, cls = "secondary") { const b = el("button", cls, text); b.type = "button"; b.addEventListener("click", handler); return b; }
function names() { return Object.fromEntries(sample().document.brief.characters.map(c => [c.id, c.name])); }
function showTab(key, focus = false) {
  activeTab = key;
  for (const tab of ["story", "prompts", "nodes"]) { const control = $(`#tab-${tab}`); control.setAttribute("aria-selected", String(tab === key)); control.tabIndex = tab === key ? 0 : -1; $(`#${tab}-panel`).hidden = tab !== key; }
  if (focus) $(`#tab-${key}`).focus();
}
function renderScenario() {
  const {brief, story} = sample().document;
  $("#scenario-title").textContent = brief.title; $("#scenario-summary").textContent = story.summary;
  $("#characters").replaceChildren();
  brief.characters.forEach((c, i) => {
    const details = el("details", "persona"), summary = el("summary"), content = el("div", "persona-content");
    summary.append(el("span", "avatar", String(i + 1)), el("span", "", c.name));
    for (const key of ["personality", "speech", "desire", "fear", "habit", "fixed"]) field(content, t(key), c[key]);
    details.append(summary, content); $("#characters").append(details);
  });
  $("#scene-details").replaceChildren();
  for (const key of ["location", "intent", "ending"]) field($("#scene-details"), t(key), brief[key]);
}
function openShot(shot) {
  $("#shot-title").textContent = `${shot.id} · ${shot.duration}s · ${shot.purpose}`;
  const content = $("#shot-detail"); content.replaceChildren();
  field(content, t("visual"), shot.visual); field(content, t("actions"), shot.actions.join("\n"));
  field(content, t("dialogue"), shot.dialogue.map(d => `${names()[d.speaker]}: “${d.text}”\n${d.delivery}`).join("\n\n"));
  field(content, t("camera"), Object.values(shot.camera).join(" · "));
  $("#shot-dialog").showModal();
}
function renderStory() {
  const container = $("#shots"); container.replaceChildren();
  for (const shot of sample().document.story.shots) {
    const card = button("", () => openShot(shot), "shot-card");
    const top = el("div", "shot-top"), id = el("div", "shot-id"); id.append(el("span", "", shot.id), el("span", "", `${shot.duration}s`));
    top.append(id, el("span", "shot-camera", shot.camera.size));
    const body = el("div", "shot-body"); body.append(el("h3", "shot-purpose", shot.purpose));
    for (const line of shot.dialogue) { const p = el("p", "shot-dialogue"); p.append(el("span", "shot-speaker", names()[line.speaker]), document.createTextNode(`“${line.text}”`)); body.append(p); }
    body.append(el("p", "shot-action", shot.actions.join(" "))); card.append(top, body); container.append(card);
  }
}
async function copyPrompt(prompt) {
  try { await navigator.clipboard.writeText(prompt); status(t("copied")); } catch { status(t("copyFailed")); }
}
function updateSelection() {
  $("#selection-count").textContent = `${selected.size} / ${bundle().clips.length} ${t("selected")}`;
  $("#add-nodes").disabled = !selected.size;
}
function renderPrompts(reset = false) {
  if (reset) selected = new Set(bundle().clips.map(c => c.clip_id));
  $("#clip-summary").textContent = `${bundle().clips.length} ${t("clips")} · 30s`;
  $("#timeline").replaceChildren(); $("#clips").replaceChildren();
  bundle().clips.forEach(clip => {
    $("#timeline").append(button(`${clip.clip_id} · ${clip.duration}s`, () => { const d = $(`#clip-${clip.clip_id} details`); d.open = true; d.scrollIntoView({block: "nearest"}); }, ""));
    const article = el("article", "clip"); article.id = `clip-${clip.clip_id}`;
    const header = el("div", "clip-header"), label = el("label", "clip-label"), check = document.createElement("input"); check.type = "checkbox"; check.checked = selected.has(clip.clip_id);
    check.addEventListener("change", () => { if (check.checked) selected.add(clip.clip_id); else selected.delete(clip.clip_id); updateSelection(); });
    const caption = el("span", "", `${clip.clip_id} · ${clip.duration}s`); caption.append(el("span", "clip-meta", clip.source_shots.join(" → ")));
    label.append(check, caption); header.append(label, button(t("copy"), () => copyPrompt(clip.prompt)));
    const details = el("details"); details.append(el("summary", "", t("expand")), el("pre", "", clip.prompt));
    article.append(header, details); $("#clips").append(article);
  });
  updateSelection();
}
function renderNodes() {
  $("#node-empty").hidden = !!nodeClips.length; $("#node-canvas").hidden = !nodeClips.length; $("#export-workflow").disabled = !nodeClips.length;
  $("#node-canvas").replaceChildren();
  nodeClips.forEach((clip, i) => {
    const pair = el("div", "node-pair"), node = el("article", "node"), head = el("div", "node-title");
    const remove = button("×", () => { nodeClips.splice(i, 1); renderNodes(); status(t("removed")); }, ""); remove.setAttribute("aria-label", `${t("remove")} ${clip.clip_id}`);
    head.append(el("span", "", "Storyboard Clip Prompt"), remove);
    const body = el("div", "node-body"), select = document.createElement("select"); select.setAttribute("aria-label", `Node ${i + 1}: clip`);
    // A node retains its own conversion; never silently replace it when the model/language changes.
    const available = Object.values(data.samples).flatMap(s => Object.values(s.variants)).find(b => b.conversion_id === clip.conversion_id).clips;
    for (const item of available) { const option = el("option", "", `${item.clip_id} · ${item.duration}s · ${item.source_shots.join(", ")}`); option.value = item.clip_id; option.selected = item.clip_id === clip.clip_id; select.append(option); }
    select.addEventListener("change", () => { nodeClips[i] = available.find(c => c.clip_id === select.value); renderNodes(); });
    body.append(select, el("p", "node-preview", `${clip.target_model} · ${clip.summary}`));
    const ports = el("div", "ports"); ports.append(el("span", "active-port", "prompt · STRING ●"), el("span", "", "duration_seconds · FLOAT"), el("span", "", "clip_id · STRING"));
    body.append(ports); node.append(head, body);
    const wire = el("div", "wire"); wire.setAttribute("aria-label", "STRING connection");
    const sink = el("article", "node preview-node"); sink.append(el("div", "node-title", "Preview Any"), el("div", "node-body", clip.prompt));
    pair.append(node, wire, sink); $("#node-canvas").append(pair);
  });
}
function render() {
  document.documentElement.lang = language; $("#language").value = language;
  document.querySelectorAll("[data-copy]").forEach(n => { n.textContent = t(n.dataset.copy); });
  renderScenario(); renderStory(); renderPrompts(true); renderNodes(); showTab(activeTab);
}
function download(value, name, type) { const url = URL.createObjectURL(new Blob([value], {type})); const a = document.createElement("a"); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
for (const key of ["story", "prompts", "nodes"]) $(`#tab-${key}`).addEventListener("click", () => { if (!loading) showTab(key); });
$(".tabs").addEventListener("keydown", event => { const tabs = ["story", "prompts", "nodes"]; const offset = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0; if (offset && !loading) { event.preventDefault(); showTab(tabs[(tabs.indexOf(activeTab) + offset + 3) % 3], true); } });
$("#next").addEventListener("click", () => { if (!loading) showTab("prompts", true); });
$("#back-prompts").addEventListener("click", () => showTab("prompts", true));
$("#close-shot").addEventListener("click", () => $("#shot-dialog").close());
$("#language").addEventListener("change", () => { language = $("#language").value; try { localStorage.setItem("storyboard.sample.language", language); } catch { /* Optional preference. */ } if (!loading) { $("#shot-dialog").close(); render(); status(""); } });
for (const selector of ["#model", "#limit"]) $(selector).addEventListener("change", () => { if (!loading) { renderPrompts(true); status(""); } });
$("#reset").addEventListener("click", () => { if (loading) return; nodeClips = []; $("#model").value = "minimax-h3-text"; $("#limit").value = "15"; activeTab = "story"; render(); status(t("resetDone")); });
$("#add-nodes").addEventListener("click", () => { const existing = new Set(nodeClips.map(c => `${c.conversion_id}:${c.clip_id}`)); for (const clip of bundle().clips) { const key = `${clip.conversion_id}:${clip.clip_id}`; if (selected.has(clip.clip_id) && !existing.has(key)) { nodeClips.push(clip); existing.add(key); } } renderNodes(); showTab("nodes", true); status(t("added")); });
$("#download-txt").addEventListener("click", () => { if (!loading) download(bundle().clips.map(c => `${c.clip_id} · ${c.duration}s · ${c.source_shots.join(", ")}\n\n${c.prompt}`).join("\n\n" + "─".repeat(60) + "\n\n"), "sample-video-prompts.txt", "text/plain;charset=utf-8"); });
$("#export-workflow").addEventListener("click", () => { if (nodeClips.length) download(JSON.stringify(makeWorkflow(nodeClips), null, 2), "storyboard-sample-workflow.json", "application/json"); });
status(t("loading"));
fetch(new URL("./data.json", import.meta.url)).then(response => { if (!response.ok) throw new Error("Sample unavailable"); return response.json(); }).then(value => { data = value; loading = false; render(); status(""); }).catch(() => status(t("loadFailed")));
