import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const PREFIX = "/storyboard-generator";
const TYPE = "StoryboardClipPrompt";
const messages = {
  title: ["Storyboard", "스토리보드", "ストーリーボード"],
  studio: ["Create", "제작", "制作"],
  library: ["Library", "보관함", "ライブラリ"],
  convert: ["Convert", "변환", "変換"],
  clips: ["Clip prompts", "클립 프롬프트", "クリッププロンプト"],
  close: ["Close", "닫기", "閉じる"],
  project: ["Project", "작품", "作品"],
  version: ["Conversion", "변환본", "変換結果"],
  refresh: ["Refresh", "새로고침", "更新"],
  search: ["Find a clip by number, scene or shot", "번호·장면·컷으로 클립 찾기", "番号・場面・カットで検索"],
  selectAll: ["Select visible clips", "보이는 클립 선택", "表示中のクリップを選択"],
  clear: ["Clear selection", "선택 해제", "選択を解除"],
  add: ["Add selected clips as nodes", "선택한 클립을 노드로 추가", "選択したクリップをノードに追加"],
  use: ["Use this clip in the selected node", "선택한 노드에 이 클립 적용", "選択ノードにこのクリップを適用"],
  update: ["Update matching nodes", "일치하는 노드 갱신", "一致するノードを更新"],
  cancelTarget: ["Add new nodes instead", "새 노드 추가로 전환", "新しいノードを追加"],
  noProjects: ["Create or import a storyboard in Create, then generate its video prompts.", "제작에서 콘티를 만들거나 불러온 뒤 영상 프롬프트로 변환하세요.", "制作でストーリーボードを作成または読み込み、動画プロンプトに変換してください。"],
  noConversions: ["This project has no converted prompts yet. Open it in the Studio to convert.", "아직 변환된 프롬프트가 없습니다. 제작 화면에서 이 콘티를 변환하세요.", "変換済みプロンプトがありません。制作画面でこの作品を変換してください。"],
  noMatches: ["No clips match your search.", "검색에 맞는 클립이 없습니다.", "該当するクリップがありません。"],
  openProject: ["Open project in Studio", "제작 화면에서 작품 열기", "制作画面で作品を開く"],
  snapshot: ["Nodes keep a saved prompt copy. Queue execution does not call the AI. New conversions never overwrite connected nodes automatically.", "노드는 확정된 프롬프트 사본을 저장합니다. 영상 실행 시 AI를 다시 호출하지 않으며, 새 변환본이 연결된 노드를 자동으로 덮어쓰지 않습니다.", "ノードは確定したプロンプトのコピーを保存します。実行時にAIを呼び出さず、新しい変換結果で既存ノードを自動上書きしません。"],
  connected: ["Node added", "노드 추가됨", "ノード追加済み"],
  connectedOutput: ["Connected", "연결됨", "接続済み"],
  older: ["Another conversion is on the canvas", "다른 변환본의 노드가 있음", "別の変換結果のノードあり"],
  ready: ["Ready to add", "추가 가능", "追加可能"],
  preview: ["Prompt preview", "프롬프트 미리보기", "プロンプトの確認"],
  choose: ["Choose clip", "클립 선택", "クリップを選択"],
  missing: ["Choose a clip in the Storyboard panel", "스토리보드 패널에서 클립을 선택하세요", "ストーリーボードパネルでクリップを選択"],
  selected: ["selected", "개 선택", "件選択"],
  clipsUnit: ["clips", "클립", "クリップ"],
  updated: ["Nodes updated. Existing connections were preserved.", "노드를 갱신했습니다. 기존 연결은 유지됩니다.", "ノードを更新しました。既存の接続は保持されます。"],
  added: ["Selected clips are on the canvas. Connect each prompt output to a STRING input.", "선택한 클립을 캔버스에 추가했습니다. prompt 출력을 문자열 입력에 연결하세요.", "選択したクリップを追加しました。prompt出力を文字列入力に接続してください。"],
  mismatch: ["Some clips have different source shots. Choose those nodes individually to reassign them.", "원본 컷 구성이 다른 클립은 자동 갱신하지 않았습니다. 해당 노드에서 클립을 직접 다시 선택하세요.", "元のカット構成が異なるクリップは更新していません。各ノードでクリップを選び直してください。"],
  loadError: ["Could not load clips. Refresh and check the ComfyUI server.", "클립을 불러오지 못했습니다. 새로고침하고 ComfyUI 서버를 확인하세요.", "クリップを読み込めません。更新してComfyUIサーバーを確認してください。"],
  confirmUpdate: ["Replace matching nodes with the selected conversion? Prompt text and duration will change; wires stay connected.", "일치하는 노드를 선택한 변환본으로 갱신할까요? 프롬프트와 길이가 바뀌며 연결선은 유지됩니다.", "一致するノードを選択した変換結果に更新しますか？プロンプトと長さが変わり、接続線は保持されます。"],
};
let language = "en";
try { language = localStorage.getItem("comfyui-storyboard.ui-language") || "en"; } catch { /* Optional persistence. */ }
const t = (key) => messages[key]?.[language === "ko" ? 1 : language === "ja" ? 2 : 0] || key;
const text = (tag, className, value = "") => { const e = document.createElement(tag); e.className = className; e.textContent = value; return e; };
const button = (key, action, className = "sg-button") => {
  const b = text("button", className); b.type = "button"; b.dataset.label = key; b.textContent = t(key); b.addEventListener("click", action); return b;
};
const request = async (path) => {
  const result = await api.fetchApi(PREFIX + "/api" + path);
  const value = await result.json();
  if (!result.ok) throw new Error(value.error || t("loadError"));
  return value;
};
const activeGraph = () => app.canvas?.graph || app.graph;
const graphNodes = () => activeGraph()?._nodes?.filter(n => n.type === TYPE) || [];
const snapshotOf = (node) => { try { return JSON.parse(node.widgets?.find(w => w.name === "clip_data")?.value || "null"); } catch { return null; } };
const keyOf = (clip) => `${clip.board_id}/${clip.conversion_id}/${clip.clip_id}`;

export function setClip(node, clip) {
  const widget = node.widgets?.find(w => w.name === "clip_data");
  if (!widget) throw new Error("Storyboard node input is unavailable. Refresh ComfyUI.");
  widget.value = JSON.stringify(clip);
  node.properties ||= {};
  node.properties.storyboard = {board_id: clip.board_id, conversion_id: clip.conversion_id, clip_id: clip.clip_id, revision: clip.revision};
  node.title = `${clip.clip_id} · ${clip.duration}s · ${clip.summary.slice(0, 44)}`;
  node.setDirtyCanvas?.(true, true);
}

export function addClipNodes(clips) {
  const graph = activeGraph();
  if (!graph) throw new Error("Open a workflow before adding clips.");
  const existing = new Set(graphNodes().map(snapshotOf).filter(Boolean).map(keyOf));
  const base = app.canvas?.graph_mouse || [100, 100];
  const created = [];
  graph.beforeChange?.();
  try {
    for (const clip of clips) {
      if (existing.has(keyOf(clip))) continue;
      const node = LiteGraph.createNode(TYPE);
      if (!node) throw new Error("Storyboard Clip Prompt is not registered. Restart ComfyUI and refresh.");
      graph.add(node);
      setClip(node, clip);
      node.pos = [base[0] + (created.length % 3) * 400, base[1] + Math.floor(created.length / 3) * 210];
      created.push(node);
      existing.add(keyOf(clip));
    }
    if (created.length && LiteGraph.LGraphGroup) {
      const group = new LiteGraph.LGraphGroup(`${clips[0].title.slice(0, 70)} · ${clips[0].target_model}`);
      group.pos = [base[0] - 20, base[1] - 55];
      group.size = [Math.min(3, created.length) * 400 - 15, Math.ceil(created.length / 3) * 210 + 50];
      graph.add(group);
    }
  } finally { graph.afterChange?.(); }
  return created;
}

export function updateClipNodes(clips) {
  let changed = 0, mismatches = 0;
  const graph = activeGraph();
  graph.beforeChange?.();
  try {
    for (const node of graphNodes()) {
      const old = snapshotOf(node);
      const clip = clips.find(c => old && c.board_id === old.board_id && c.clip_id === old.clip_id);
      if (!clip || keyOf(clip) === keyOf(old)) continue;
      if (JSON.stringify(clip.source_shots) !== JSON.stringify(old.source_shots)) { mismatches++; continue; }
      setClip(node, clip); changed++;
    }
  } finally { graph.afterChange?.(); }
  return {changed, mismatches};
}

let panel, frame, clipTab, studioTab, list, projectSelect, conversionSelect, search, status, count, apply, update, cancelTarget;
let projects = [], bundle = null, target = null, selected = new Set(), catalogSequence = 0, bundleSequence = 0;
let selectedGraph = null;
let tab = "studio";
let currentStudioView = "create";
const studioTabs = new Map();

function translate() {
  if (!panel) return;
  for (const e of panel.querySelectorAll("[data-label]")) e.textContent = t(e.dataset.label);
  search.placeholder = t("search"); search.setAttribute("aria-label", t("search"));
  renderClips();
}

function selectTab(value) {
  tab = value;
  frame.hidden = value !== "studio"; clipTab.hidden = value !== "clips";
  for (const [view, button] of studioTabs) button.setAttribute("aria-selected", String(value === "studio" && view === currentStudioView));
  panel.querySelector("#sg-clips-tab").setAttribute("aria-selected", String(value === "clips"));
}

function openStudioView(view) {
  currentStudioView = view;
  selectTab("studio");
  for (const control of studioTabs.values()) control.disabled = true;
  frame.contentWindow.postMessage({type: "storyboard:studio-view", view}, location.origin);
}

function say(message, error = false) {
  status.textContent = message; status.classList.toggle("sg-error", error);
}

function makePanel() {
  const css = document.createElement("link"); css.rel = "stylesheet"; css.href = new URL("./panel.css", import.meta.url).href; document.head.append(css);
  panel = text("dialog", "sg-panel"); panel.id = "storyboard-panel"; panel.setAttribute("aria-labelledby", "sg-title");
  const header = text("header", "sg-header");
  const title = text("h2", "", t("title")); title.id = "sg-title"; title.dataset.label = "title";
  const tabs = text("div", "sg-tabs"); tabs.setAttribute("role", "tablist"); tabs.setAttribute("aria-label", "Storyboard views");
  for (const [view, label] of [["create", "studio"], ["manage", "library"], ["convert", "convert"]]) {
    const control = button(label, () => openStudioView(view)); control.setAttribute("role", "tab");
    control.id = "sg-" + view + "-tab"; control.disabled = true; studioTabs.set(view, control); tabs.append(control);
  }
  studioTab = studioTabs.get("create");
  const clips = button("clips", () => { selectTab("clips"); refresh().catch(showError); }); clips.id = "sg-clips-tab"; clips.setAttribute("role", "tab");
  tabs.append(clips);
  header.append(title, tabs, button("close", () => panel.close(), "sg-button sg-close"));
  frame = document.createElement("iframe"); frame.className = "sg-studio"; frame.title = "Storyboard Studio";
  frame.src = api.apiURL(PREFIX + "/studio/");
  clipTab = text("section", "sg-clips");
  const filters = text("div", "sg-filters");
  projectSelect = document.createElement("select"); projectSelect.id = "sg-project";
  conversionSelect = document.createElement("select"); conversionSelect.id = "sg-conversion";
  for (const [key, control] of [["project", projectSelect], ["version", conversionSelect]]) {
    const label = text("label", ""); const caption = text("span", "", t(key)); caption.dataset.label = key; label.append(caption, control); filters.append(label);
  }
  filters.append(button("refresh", () => refresh().catch(showError)));
  projectSelect.addEventListener("change", () => { fillConversions(); loadBundle().catch(showError); });
  conversionSelect.addEventListener("change", () => loadBundle().catch(showError));
  search = document.createElement("input"); search.type = "search"; search.id = "sg-search"; search.addEventListener("input", renderClips);
  const tools = text("div", "sg-tools");
  tools.append(search, button("selectAll", () => { for (const clip of visibleClips()) selected.add(clip.clip_id); renderClips(); }), button("clear", () => { selected.clear(); renderClips(); }));
  list = text("div", "sg-list"); list.id = "sg-clip-list";
  const foot = text("footer", "sg-footer"); count = text("span", "sg-count"); count.setAttribute("aria-live", "polite");
  apply = button("add", () => {
    try {
      if (selectedGraph !== activeGraph()) throw new Error("The active workflow changed. Reopen the Storyboard panel before applying clips.");
      const clips = bundle.clips.filter(c => selected.has(c.clip_id));
      if (target) {
        if (!graphNodes().includes(target)) throw new Error("The selected node was removed. Choose another node.");
        const graph = activeGraph(); graph.beforeChange?.();
        try { setClip(target, clips[0]); } finally { graph.afterChange?.(); }
        target = null; say(t("updated"));
      } else { addClipNodes(clips); say(t("added")); }
      renderClips();
    } catch (error) { showError(error); }
  }, "sg-button sg-primary");
  update = button("update", async () => {
    try {
      const approved = await app.extensionManager.dialog.confirm({title: t("update"), message: t("confirmUpdate"), type: "overwrite"});
      if (!approved) return;
      if (selectedGraph !== activeGraph()) throw new Error("The active workflow changed. Reopen the panel first.");
      const outcome = updateClipNodes(bundle.clips.filter(c => selected.has(c.clip_id)));
      say(outcome.mismatches ? t("mismatch") : t("updated")); renderClips();
    } catch (error) { showError(error); }
  });
  cancelTarget = button("cancelTarget", () => { target = null; renderClips(); });
  foot.append(count, cancelTarget, update, apply);
  status = text("p", "sg-status"); status.setAttribute("role", "status");
  const note = text("p", "sg-note", t("snapshot")); note.dataset.label = "snapshot";
  clipTab.append(filters, tools, list, status, note, foot);
  panel.append(header, frame, clipTab); document.body.append(panel); translate(); selectTab("studio");
  panel.addEventListener("close", () => { target = null; });
  window.addEventListener("message", (event) => {
    if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
    if (event.data?.type === "storyboard:studio-busy" && typeof event.data.busy === "boolean") {
      for (const control of studioTabs.values()) control.disabled = event.data.busy;
    }
    if (event.data?.type === "storyboard:studio-view" && ["create", "manage", "convert"].includes(event.data.view)) {
      currentStudioView = event.data.view;
      if (tab === "studio") selectTab("studio");
    }
    if (event.data?.type === "storyboard:conversion-ready" && /^[a-f0-9]{32}$/.test(event.data.id)) refresh(event.data.id).catch(showError);
    if (event.data?.type === "storyboard:language" && ["en", "ko", "ja"].includes(event.data.language)) {
      language = event.data.language; translate();
    }
  });
}

function showError(error) { say(error.message || t("loadError"), true); }
const visibleClips = () => (bundle?.clips || []).filter(c => `${c.clip_id} ${c.summary} ${c.source_shots.join(" ")}`.toLocaleLowerCase().includes(search?.value.toLocaleLowerCase().trim() || ""));

function fillConversions(preferred) {
  conversionSelect.replaceChildren();
  const conversions = projects.find(p => p.id === projectSelect.value)?.conversions || [];
  for (const [index, item] of conversions.entries()) {
    const date = new Date(item.created_at);
    const dateLabel = Number.isNaN(date.valueOf()) ? item.created_at : new Intl.DateTimeFormat(language, {dateStyle: "short", timeStyle: "medium"}).format(date);
    const option = text("option", "", `v${conversions.length - index} · ${item.target_model} · ${item.clips} ${t("clipsUnit")} · ${dateLabel}`);
    option.value = item.id; conversionSelect.append(option);
  }
  if ([...conversionSelect.options].some(o => o.value === preferred)) conversionSelect.value = preferred;
}

async function refresh(preferred) {
  const sequence = ++catalogSequence;
  const result = await request("/catalog");
  if (sequence !== catalogSequence) return;
  const priorProject = projectSelect.value, priorConversion = preferred || conversionSelect.value;
  projects = result.projects;
  projectSelect.replaceChildren();
  for (const project of projects) { const o = text("option", "", project.title); o.value = project.id; projectSelect.append(o); }
  const requestedProject = projects.find(p => p.conversions.some(c => c.id === priorConversion));
  if (requestedProject) projectSelect.value = requestedProject.id;
  else if (projects.some(p => p.id === priorProject)) projectSelect.value = priorProject;
  fillConversions(priorConversion); await loadBundle();
}

async function loadBundle() {
  const sequence = ++bundleSequence;
  const id = conversionSelect.value;
  const previous = bundle?.conversion_id;
  bundle = null; apply.disabled = update.disabled = true;
  if (id) {
    const result = await request("/bundle/" + id);
    if (sequence !== bundleSequence) return;
    bundle = result;
  }
  if (previous !== bundle?.conversion_id) selected.clear();
  if (target && bundle) {
    const old = snapshotOf(target);
    const match = bundle.clips.find(c => c.clip_id === old?.clip_id);
    if (match) selected.add(match.clip_id);
  }
  say(""); renderClips();
}

function renderClips() {
  if (!list) return;
  list.replaceChildren();
  const clips = visibleClips();
  if (!clips.length) {
    list.append(text("p", "sg-empty", t(!projects.length ? "noProjects" : !bundle ? "noConversions" : "noMatches")));
    if (projects.length && !bundle) list.append(button("openProject", () => {
      selectTab("studio"); frame.contentWindow.postMessage({type: "storyboard:open-project", id: projectSelect.value}, location.origin);
    }));
  }
  for (const clip of clips) {
    const row = text("article", "sg-clip"); row.dataset.clipId = clip.clip_id;
    const label = text("label", "sg-clip-heading");
    const checkbox = document.createElement("input"); checkbox.type = "checkbox"; checkbox.checked = selected.has(clip.clip_id); checkbox.setAttribute("aria-label", clip.clip_id);
    checkbox.addEventListener("change", () => { if (target) selected.clear(); if (checkbox.checked) selected.add(clip.clip_id); else selected.delete(clip.clip_id); renderClips(); });
    const identity = text("strong", "sg-clip-id", clip.clip_id);
    const summary = text("span", "sg-summary", clip.summary);
    const duration = text("span", "sg-duration", `${clip.duration}s`);
    label.append(checkbox, identity, summary, duration);
    const nodes = graphNodes();
    const matches = nodes.filter(n => { const snap = snapshotOf(n); return snap && keyOf(snap) === keyOf(clip); });
    const older = nodes.some(n => { const snap = snapshotOf(n); return snap && snap.board_id === clip.board_id && snap.clip_id === clip.clip_id && keyOf(snap) !== keyOf(clip); });
    const connected = matches.some(n => n.outputs?.[0]?.links?.length);
    const details = document.createElement("details"); details.className = "sg-preview";
    details.append(text("summary", "", t("preview")), text("pre", "", clip.prompt));
    row.append(label, text("p", "sg-clip-meta", `${clip.source_shots.join(" · ")} / ${t(connected ? "connectedOutput" : matches.length ? "connected" : older ? "older" : "ready")}`), details);
    list.append(row);
  }
  count.textContent = `${selected.size} ${t("selected")}`;
  apply.textContent = t(target ? "use" : "add");
  apply.disabled = !bundle || selected.size === 0 || (target && selected.size !== 1);
  cancelTarget.hidden = !target;
  update.hidden = !!target;
  update.disabled = !bundle || selected.size === 0;
}

export async function openPanel(node = null) {
  if (!panel) makePanel();
  target = node; selectedGraph = activeGraph();
  if (!panel.open) panel.showModal();
  selectTab(node ? "clips" : tab);
  try { await refresh(snapshotOf(node)?.conversion_id); } catch (error) { showError(error); }
}

app.registerExtension({
  name: "Storyboard.Generator",
  commands: [{id: "Storyboard.Open", label: "Storyboard", function: () => openPanel()}],
  menuCommands: [{path: ["Extensions"], commands: ["Storyboard.Open"]}],
  actionBarButtons: [{icon: "pi pi-video", tooltip: "Storyboard", onClick: () => openPanel()}],
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== TYPE) return;
    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function(...args) {
      const result = onCreated?.apply(this, args);
      const widget = this.widgets?.find(w => w.name === "clip_data");
      if (widget) { widget.type = "hidden"; widget.computeSize = () => [0, -4]; if (widget.inputEl) widget.inputEl.style.display = "none"; }
      this.addWidget("button", t("choose"), null, () => openPanel(this), {serialize: false});
      this.size = [360, 150];
      return result;
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function(...args) {
      const result = onConfigure?.apply(this, args);
      const clip = snapshotOf(this);
      if (clip) setClip(this, clip);
      return result;
    };
  },
});
