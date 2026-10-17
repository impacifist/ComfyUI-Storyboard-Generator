"use strict";

// Ollama lifecycle belongs to the ComfyUI adapter, outside the pinned engine.
const ollamaMemoryCopy = {
  title: ["Ollama model memory", "Ollama 모델 메모리", "Ollamaモデルのメモリ"],
  auto: ["Unload Ollama after prompt conversion", "프롬프트 변환 후 Ollama 자동 언로드", "プロンプト変換後にOllamaを自動アンロード"],
  help: ["Releases the selected model after the full conversion and repairs finish. Other models and ComfyUI video models are untouched. Other apps using the same Ollama model may need to reload it.", "전체 변환과 내부 재시도가 끝난 뒤 선택한 모델만 해제합니다. 다른 모델과 ComfyUI 영상 모델은 건드리지 않습니다. 같은 Ollama 모델을 쓰는 다른 앱은 모델을 다시 로드해야 할 수 있습니다.", "変換と内部修正がすべて完了してから選択モデルだけを解放します。他のモデルやComfyUIの動画モデルは変更しません。同じOllamaモデルを使う他のアプリでは再ロードが必要になる場合があります。"],
  manual: ["Unload selected Ollama model now", "선택한 Ollama 모델 지금 언로드", "選択したOllamaモデルを今すぐアンロード"],
  unloaded: ["Ollama confirmed the model was unloaded. Saved prompts are ready to use.", "Ollama 모델 언로드를 확인했습니다. 저장된 프롬프트는 그대로 사용할 수 있습니다.", "Ollamaモデルのアンロードを確認しました。保存したプロンプトはそのまま使えます。"],
  failed: ["Could not confirm model unload. Saved prompts are preserved. Check Ollama and retry the unload button.", "모델 언로드를 확인하지 못했습니다. 저장된 프롬프트는 보존됩니다. Ollama 상태를 확인하고 언로드 버튼으로 다시 시도하세요.", "アンロードを確認できませんでした。保存したプロンプトは保持されます。Ollamaを確認し、アンロードボタンで再試行してください。"],
  waiting: ["Waiting for Ollama to unload…", "Ollama 모델 언로드 대기 중…", "Ollamaモデルのアンロード待ち…"],
  choose: ["Select Ollama and enter its model ID in creation or conversion settings first.", "제작 또는 변환 설정에서 Ollama를 선택하고 모델 ID를 입력하세요.", "制作または変換設定でOllamaを選び、モデルIDを入力してください。"],
};
const memoryText = (key) => ollamaMemoryCopy[key][I18n.language === "ko" ? 1 : I18n.language === "ja" ? 2 : 0];
const memorySection = el("section", "ollama-memory");
memorySection.id = "ollama-memory";
const memoryTitle = el("h4", "");
const memoryAuto = document.createElement("input"); memoryAuto.type = "checkbox"; memoryAuto.id = "ollama-auto-unload";
memoryAuto.checked = true;
try { memoryAuto.checked = localStorage.getItem("comfyui-storyboard.ollama-auto-unload") !== "false"; } catch { /* Optional persistence. */ }
memoryAuto.addEventListener("change", () => {
  try { localStorage.setItem("comfyui-storyboard.ollama-auto-unload", String(memoryAuto.checked)); } catch { /* Optional persistence. */ }
});
const memoryLabel = el("label", "check"); const memoryCaption = el("span", ""); memoryLabel.append(memoryAuto, memoryCaption);
const memoryHelp = el("p", "helper");
const memoryButton = el("button", "secondary"); memoryButton.type = "button"; memoryButton.id = "ollama-unload";
const memoryStatus = el("p", "helper"); memoryStatus.id = "ollama-memory-status"; memoryStatus.setAttribute("role", "status");
memorySection.append(memoryTitle, memoryLabel, memoryHelp, memoryButton, memoryStatus);
$("#conversion-run").after(memorySection);
let memoryOutcome = "";
function selectedOllamaModel() {
  const conversionModel = $("#conversion-ai-provider").value === "ollama" ? $("#conversion-ai-model").value.trim() : "";
  return conversionModel || ($("#provider").value === "ollama" ? $("#model").value.trim() : "");
}
function renderOllamaMemory() {
  memoryTitle.textContent = memoryText("title"); memoryCaption.textContent = memoryText("auto");
  memoryHelp.textContent = memoryText("help");
  memoryButton.textContent = memoryText("manual") + (selectedOllamaModel() ? ` · ${selectedOllamaModel()}` : "");
  if (memoryOutcome) memoryStatus.textContent = memoryText(memoryOutcome);
}
function showOllamaRelease(value) {
  memoryOutcome = value?.status === "unloaded" ? "unloaded" : "failed";
  renderOllamaMemory();
}
const storyboardAPI = api;
api = async function(path, body) {
  const conversion = path.endsWith("/conversion/compile") && body?.provider === "ollama";
  if (conversion) { memoryOutcome = ""; memoryStatus.textContent = ""; }
  const result = await storyboardAPI(path, conversion ? {...body, unload_ollama_after: memoryAuto.checked} : body);
  if (conversion) {
    memoryOutcome = ""; memoryStatus.textContent = "";
    if (result.ollama_release) showOllamaRelease(result.ollama_release);
  }
  return result;
};
memoryButton.addEventListener("click", async () => {
  if (busy) return;
  const model = selectedOllamaModel();
  if (!model) { memoryOutcome = "choose"; renderOllamaMemory(); return; }
  setBusy(true); memoryOutcome = "waiting"; renderOllamaMemory();
  try { showOllamaRelease((await api("/storyboard-generator/api/ollama/unload", {model})).ollama_release); }
  catch { memoryOutcome = "failed"; renderOllamaMemory(); }
  finally { setBusy(false); }
});
window.addEventListener("languagechange", renderOllamaMemory);
for (const selector of ["#conversion-ai-provider", "#conversion-ai-model", "#provider", "#model"]) {
  $(selector).addEventListener("input", renderOllamaMemory);
  $(selector).addEventListener("change", renderOllamaMemory);
}
renderOllamaMemory();

// Served as a classic script after the pinned Studio app. Never sends prompts or keys.
const storyboardRenderConversion = renderConversion;
renderConversion = function(result, date, remember, savedId) {
  storyboardRenderConversion(result, date, remember, savedId);
  if (savedId) window.parent.postMessage({type: "storyboard:conversion-ready", id: savedId}, window.location.origin);
};

window.addEventListener("message", (event) => {
  if (event.origin !== window.location.origin || event.source !== window.parent) return;
  if (event.data?.type === "storyboard:open-project" && /^[a-f0-9]{32}$/.test(event.data.id)) {
    libraryAction(async () => { await switchStudio("convert"); await loadSaved(event.data.id, true); });
  }
});

const storyboardLanguageChanged = () => window.parent.postMessage({type: "storyboard:language", language: document.documentElement.lang}, window.location.origin);
new MutationObserver(storyboardLanguageChanged).observe(document.documentElement, {attributes: true, attributeFilter: ["lang"]});
storyboardLanguageChanged();
