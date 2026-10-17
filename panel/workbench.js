"use strict";

// ComfyUI presentation only. Keep the shared engine and Studio snapshot unchanged.
const workbenchCopy = {
  source: ["Storyboard shots", "원본 콘티 확인", "元のストーリーボード"],
  references: ["Reference images", "참조 이미지", "参照画像"],
  memory: ["Ollama model memory", "Ollama 모델 메모리", "Ollamaモデルのメモリ"],
  next: ["Save and convert", "저장하고 프롬프트 변환", "保存してプロンプト変換"],
  empty: ["Choose a storyboard, set the clip lengths, then convert.", "콘티를 고르고 클립 길이를 정한 뒤 프롬프트로 변환하세요.", "ストーリーボードを選び、クリップの長さを設定して変換してください。"],
  emptyBoard: ["Your storyboard appears here", "생성한 콘티를 여기서 확인합니다", "作成したストーリーボードがここに表示されます"],
  create: ["Create a storyboard", "콘티 만들기", "ストーリーボードを作成"],
  convert: ["Generate video prompts", "영상 프롬프트 만들기", "動画プロンプトを作成"],
  edit: ["Edit characters and scene on the left. Review the shots on the right.", "왼쪽에서 인물과 상황을 설정하고 오른쪽에서 콘티를 확인하세요.", "左で人物と状況を設定し、右でストーリーボードを確認します。"],
};
const workbenchText = (key) => workbenchCopy[key][I18n.language === "ko" ? 1 : I18n.language === "ja" ? 2 : 0];
const workbenchLabels = [];
function foldWorkbench(element, key) {
  const details = document.createElement("details"); details.className = "workbench-fold";
  const summary = el("summary", ""); workbenchLabels.push([summary, key]);
  element.before(details); details.append(summary, element);
  return details;
}
document.body.classList.add("comfy-workbench");
foldWorkbench($("#reference-panel"), "references");
foldWorkbench($("#ollama-memory"), "memory");
const sourceFold = foldWorkbench(document.querySelector(".conversion-original"), "source");
document.querySelector(".conversion-settings").prepend(sourceFold);
document.querySelector(".conversion-workspace").append($("#conversion-results"));
// Keep the connection chooser visible without requiring an extra disclosure click.
document.querySelector(".provider-box").open = true;
document.querySelector(".conversion-advanced").open = true;

const dock = el("div", "workbench-dock"); dock.id = "workbench-dock";
const createActions = el("div", "workbench-action-group");
const convertActions = el("div", "workbench-action-group");
const dockNote = el("p", "helper");
const nextAction = el("button", "secondary"); nextAction.type = "button"; nextAction.id = "workbench-next";
$("#generate").setAttribute("form", "brief-form");
createActions.append($("#consent-label"), nextAction, $("#generate"));
convertActions.append($("#conversion-consent").closest("label"), $("#conversion-run"));
dock.append(dockNote, createActions, convertActions); document.body.append(dock);
nextAction.addEventListener("click", () => libraryAction(async () => {
  if (!project) return;
  const result = await api("/storyboard-generator/api/library/save", {document: project});
  await switchStudio("convert"); await loadSaved(result.saved.id, true);
}));

function updateWorkbench() {
  const view = document.querySelector("main").dataset.studio || "create";
  createActions.hidden = view !== "create";
  convertActions.hidden = view !== "convert" || $("#conversion-controls").hidden;
  dock.hidden = view === "manage" || (view === "convert" && $("#conversion-controls").hidden);
  nextAction.hidden = !project; nextAction.disabled = busy || !project;
  document.body.dataset.workbenchView = view;
  dockNote.textContent = view === "convert" && $("#ollama-memory-status").textContent
    ? $("#ollama-memory-status").textContent : workbenchText(view === "convert" ? "empty" : "edit");
  $("#generate").textContent = workbenchText("create"); $("#conversion-run").textContent = workbenchText("convert");
  nextAction.textContent = workbenchText("next");
  for (const [node, key] of workbenchLabels) node.textContent = workbenchText(key);
  $("#conversion-results").dataset.empty = workbenchText("empty");
  $("#empty h3").textContent = workbenchText("emptyBoard");
}
const workbenchSetBusy = setBusy;
setBusy = function(value, message) {
  workbenchSetBusy(value, message); updateWorkbench();
  window.parent.postMessage({type: "storyboard:studio-busy", busy: !!value}, location.origin);
};
const workbenchRenderBoard = renderBoard;
renderBoard = function() { workbenchRenderBoard(); updateWorkbench(); };
const workbenchSwitchStudio = switchStudio;
switchStudio = async function(view) {
  const result = await workbenchSwitchStudio(view);
  updateWorkbench();
  window.parent.postMessage({type: "storyboard:studio-view", view}, location.origin);
  return result;
};
new MutationObserver(updateWorkbench).observe($("#conversion-controls"), {attributes: true, attributeFilter: ["hidden"]});
new MutationObserver(updateWorkbench).observe($("#ollama-memory-status"), {childList: true});
window.addEventListener("languagechange", updateWorkbench);
window.addEventListener("message", (event) => {
  if (event.origin !== location.origin || event.source !== window.parent) return;
  if (event.data?.type === "storyboard:studio-view" && ["create", "manage", "convert"].includes(event.data.view)) {
    libraryAction(() => switchStudio(event.data.view));
  }
});
updateWorkbench();
window.parent.postMessage({type: "storyboard:studio-view", view: studioView}, location.origin);
window.parent.postMessage({type: "storyboard:studio-busy", busy: !!busy}, location.origin);
