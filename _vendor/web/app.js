"use strict";

const $ = (selector) => document.querySelector(selector);
const form = $("#brief-form");
let project = null;
let checks = null;
let aiReview = null;
let providers = [];
let busy = false;
let dirty = false;
let editing = null;
const models = new Map();
let config = null;
const settingFields = {
  OLLAMA_BASE_URL: "#settings-ollama-url", OLLAMA_MODEL: "#settings-ollama-model",
  OPENAI_MODEL: "#settings-openai-model", CLAUDE_MODEL: "#settings-claude-model",
  OPENAI_API_KEY: "#settings-openai-key", ANTHROPIC_API_KEY: "#settings-claude-key",
  OPENAI_BASE_URL: "#settings-openai-url", OPENAI_API_MODE: "#settings-openai-mode",
  OPENAI_OUTPUT_MODE: "#settings-openai-output",
  LMSTUDIO_BASE_URL: "#settings-lmstudio-url", LMSTUDIO_MODEL: "#settings-lmstudio-model",
  LMSTUDIO_API_KEY: "#settings-lmstudio-key", LMSTUDIO_OUTPUT_MODE: "#settings-lmstudio-output",
  LMSTUDIO_MAX_TOKENS: "#settings-lmstudio-max-tokens",
  OLLAMA_MAX_TOKENS: "#settings-ollama-max-tokens", OPENAI_LOCAL_MAX_TOKENS: "#settings-openai-local-max-tokens",
};
const providerSettingKeys = {
  ollama: ["OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_MAX_TOKENS"],
  openai: ["OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_MODE", "OPENAI_OUTPUT_MODE", "OPENAI_LOCAL_MAX_TOKENS"],
  claude: ["ANTHROPIC_API_KEY", "CLAUDE_MODEL"],
  lmstudio: ["LMSTUDIO_BASE_URL", "LMSTUDIO_MODEL", "LMSTUDIO_API_KEY", "LMSTUDIO_OUTPUT_MODE", "LMSTUDIO_MAX_TOKENS"],
};
const providerNames = {openai: "OpenAI", claude: "Claude", ollama: "Ollama", lmstudio: "LM Studio"};

function settingsKeyStatus(provider) {
  if (provider?.id === "lmstudio") return provider.key_configured ? tr("● API 키 등록됨 · 키 값은 표시하지 않습니다.") : tr("인증을 사용하지 않으면 API 키 없이 연결합니다.");
  return provider?.configured ? tr("● API 키 등록됨 · 키 값은 표시하지 않습니다.") : tr("○ API 키 미등록");
}

function showSettingsProvider() {
  const selected = $("#settings-provider").value;
  for (const id of Object.keys(providerSettingKeys)) $(`#settings-panel-${id}`).hidden = selected !== id;
  $("#settings-save").textContent = tr("{0} 설정 저장", {0: providerNames[selected]});
  $("#settings-error").textContent = "";
}

function settingsDisabled() {
  const managed = new Set(config?.environment_fields || []);
  for (const [key, selector] of Object.entries(settingFields)) $(selector).disabled = busy || managed.has(key);
  $("#settings-openai-clear").disabled = busy || managed.has("OPENAI_API_KEY");
  $("#settings-claude-clear").disabled = busy || managed.has("ANTHROPIC_API_KEY");
  $("#settings-lmstudio-clear").disabled = busy || managed.has("LMSTUDIO_API_KEY");
}

function applyConfig(value, defaults = false) {
  config = value;
  providers = value.providers;
  providers.forEach((p) => { if (defaults || !models.has(p.id)) models.set(p.id, p.model); });
  if (defaults) $("#model").value = models.get($("#provider").value) || "";
  updateProvider();
  settingsDisabled();
  updateConversionAI();
}

async function openSettings() {
  if (busy) return;
  setBusy(true);
  try {
    applyConfig(await api("/api/config"));
    if (!Object.hasOwn(config, "openai_base_url")) {
      throw new Error(tr("연결 지원이 업데이트되었습니다. 실행 중인 서버를 종료하고 start.bat로 다시 실행한 뒤 새로고침해주세요."));
    }
    $("#settings-ollama-url").value = config.ollama_base_url;
    $("#settings-openai-url").value = config.openai_base_url || "https://api.openai.com/v1";
    $("#settings-openai-mode").value = config.openai_api_mode || "responses";
    $("#settings-openai-output").value = config.openai_output_mode || "json_schema";
    $("#settings-lmstudio-url").value = config.lmstudio_base_url || "http://127.0.0.1:1234/v1";
    $("#settings-lmstudio-output").value = config.lmstudio_output_mode || "json_schema";
    $("#settings-lmstudio-max-tokens").value = config.lmstudio_max_tokens ?? 16000;
    $("#settings-ollama-max-tokens").value = config.ollama_max_tokens ?? 16000;
    $("#settings-openai-local-max-tokens").value = config.openai_local_max_tokens ?? 16000;
    for (const id of Object.keys(providerSettingKeys)) {
      const provider = providers.find((p) => p.id === id);
      $(`#settings-${id}-model`).value = provider?.model || "";
      if (id !== "ollama") {
        $(`#settings-${id}-key`).value = "";
        $(`#settings-${id}-clear`).checked = false;
        $(`#settings-${id}-status`).textContent = settingsKeyStatus(provider);
      }
    }
    $("#settings-error").textContent = "";
    $("#settings-provider").value = $("#provider").value === "demo" ? "openai" : $("#provider").value;
    showSettingsProvider();
    $("#settings-dialog").showModal();
    $("#settings-dialog").scrollTop = 0;
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}

async function saveSettings(event) {
  event.preventDefault();
  if (busy) return;
  const values = {};
  const selected = $("#settings-provider").value;
  for (const [key, selector] of Object.entries(settingFields)) {
    if (!providerSettingKeys[selected].includes(key)) continue;
    if ($(selector).disabled) continue;
    const value = $(selector).value.trim();
    if (key === "OLLAMA_BASE_URL" && !value) continue;
    if (!key.endsWith("API_KEY") || value) values[key] = value;
  }
  const clear_keys = [];
  if (selected === "openai" && $("#settings-openai-clear").checked && !$("#settings-openai-clear").disabled) clear_keys.push("OPENAI_API_KEY");
  if (selected === "claude" && $("#settings-claude-clear").checked && !$("#settings-claude-clear").disabled) clear_keys.push("ANTHROPIC_API_KEY");
  if (selected === "lmstudio" && $("#settings-lmstudio-clear").checked && !$("#settings-lmstudio-clear").disabled) clear_keys.push("LMSTUDIO_API_KEY");
  setBusy(true);
  try {
    applyConfig(await api("/api/settings", {values, clear_keys}), true);
    $("#settings-dialog").close();
    notice(tr("API 설정을 저장했습니다. 기본 모델과 키 설정을 바로 적용했으며 AI는 호출하지 않았습니다."));
  } catch (error) { $("#settings-error").textContent = error.message; }
  finally { setBusy(false); }
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function notice(message, error = false) {
  $("#notice").textContent = message;
  $("#notice").className = error ? "notice error" : "notice";
  $("#notice").hidden = !message;
  $("#diagnostics-error-open").hidden = !message || !error;
}

async function api(path, body) {
  let response;
  try {
    response = await fetch(path, body === undefined ? {} : {
      method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
    });
  } catch { throw new Error(tr("서버에 연결할 수 없습니다. 서버 실행 상태를 확인해주세요.")); }
  let result;
  try { result = await response.json(); }
  catch { throw new Error(tr("서버 응답을 읽을 수 없습니다. 페이지를 새로고침해주세요.")); }
  if (!response.ok) throw new Error(I18n.system(result.error || tr("요청을 처리하지 못했습니다.")));
  return result;
}

function parseJSON(value) {
  try { return JSON.parse(value); }
  catch { throw new Error(tr("JSON 형식이 올바르지 않습니다. 파일 또는 상태 데이터를 확인해주세요.")); }
}

function setBusy(value, message = "") {
  busy = value;
  document.body.classList.toggle("busy", value);
  document.querySelectorAll("button, input, textarea, select").forEach((node) => { node.disabled = value; });
  document.querySelectorAll("#diagnostics-open, #diagnostics-error-open, #diagnostics-dialog button").forEach((node) => { node.disabled = false; });
  if (!value) updateProvider(false);
  updateCastControls();
  settingsDisabled();
  if (message) notice(message);
}

function inputField(label, name, multiline = false, required = false) {
  const wrapper = el("label", "", label);
  const input = el(multiline ? "textarea" : "input");
  input.name = name;
  input.required = required;
  input.maxLength = 12000;
  if (multiline) input.rows = 2;
  wrapper.append(input);
  I18n.capture(wrapper);
  return wrapper;
}

function readCharacters() {
  return [...$("#characters").children].map((card) => Object.fromEntries(
    [...card.querySelectorAll("input, textarea")].map((input) => [input.name.replace(/^c\d+_/, ""), input.value])));
}

function updateCastControls() {
  const count = $("#characters").children.length;
  $("#tab-cast span").textContent = String(count).padStart(2, "0");
  $("#cast-count").textContent = tr("{0} / 5명", {0: count});
  $("#add-character").disabled = busy || count >= 5;
  document.querySelectorAll(".remove-character").forEach((button) => { button.disabled = busy || count <= 1; });
}

function buildCharacters(characters = [{id: "girl_1"}, {id: "girl_2"}]) {
  $("#characters").replaceChildren();
  characters.forEach((character, i) => {
    const card = el("fieldset", "character");
    card.append(el("legend", "", `CHARACTER 0${i + 1}`));
    const id = el("input");
    id.type = "hidden";
    id.name = `c${i}_id`;
    id.value = character.id;
    const top = el("div", "character-top");
    top.append(el("span", "avatar", String(i + 1)), inputField(tr("이름"), `c${i}_name`, false, true));
    card.append(id, top, inputField(tr("성격 · 상대를 대하는 태도"), `c${i}_personality`, true, true),
      inputField(tr("말투"), `c${i}_speech`, true));
    const traits = el("div", "form-grid");
    traits.append(inputField(tr("성별 · 선택"), `c${i}_gender`), inputField(tr("연령 · 선택"), `c${i}_age`));
    card.insertBefore(traits, top.nextSibling);
    card.append(el("p", "helper", tr("말투에 대사 언어, 인칭, 존댓말 여부와 예시를 적으면 더 정확해집니다.")));
    if (i === 0) card.append(el("p", "helper", tr("일본어 대사는 생성 후 한 번 더 교정하며 API 사용량이 늘어납니다.")));
    const details = el("details");
    details.append(el("summary", "", tr("욕구 · 두려움 · 습관 · 고정 설정")));
    for (const [key, label] of [["desire", tr("원하는 것")], ["fear", tr("두려운 것")], ["habit", tr("행동 습관")], ["fixed", tr("외형 · 과거 · 바뀌면 안 되는 설정")]]) {
      details.append(inputField(label, `c${i}_${key}`, true));
    }
    card.append(details);
    const remove = el("button", "text-button remove-character", tr("캐릭터 삭제"));
    remove.type = "button";
    remove.addEventListener("click", () => {
      if (busy || characters.length <= 1) return;
      const current = readCharacters();
      if (Object.entries(current[i]).some(([key, value]) => key !== "id" && value.trim()) &&
          !window.confirm(tr("이 캐릭터를 삭제할까요? 입력한 설정이 사라집니다."))) return;
      current.splice(i, 1);
      buildCharacters(current);
      dirty = true;
    });
    card.append(remove);
    $("#characters").append(card);
    for (const [key, value] of Object.entries(character)) {
      const input = form.elements.namedItem(`c${i}_${key}`);
      if (input) input.value = value;
    }
  });
  markRequired($("#characters"));
  I18n.capture($("#characters"));
  updateCastControls();
}

function readBrief() {
  const text = (name) => String(form.elements.namedItem(name)?.value || "").trim();
  const brief = {};
  for (const name of ["title", "relationship", "location", "time", "atmosphere", "situation", "intent", "ending", "required", "excluded", "style"]) {
    brief[name] = text(name);
  }
  brief.duration = Number(text("duration"));
  brief.shot_count = Number(text("shot_count"));
  brief.characters = readCharacters().map((_, i) => Object.fromEntries(
    ["id", "name", "personality", "speech", "desire", "fear", "habit", "fixed"].map((k) => [k, text(`c${i}_${k}`)])));
  brief.characters.forEach((character, i) => {
    for (const key of ["gender", "age"]) if (text(`c${i}_${key}`)) character[key] = text(`c${i}_${key}`);
  });
  return brief;
}

function validateBriefInputs() {
  const fields = [["title", tr("프로젝트 이름"), "cast"],
    ...readCharacters().flatMap((_, i) => [
      [`c${i}_name`, tr("캐릭터 {0} 이름", {0: i + 1}), "cast"],
      [`c${i}_personality`, tr("캐릭터 {0} 성격", {0: i + 1}), "cast"]]),
    ["location", tr("장소"), "world"], ["situation", tr("시작 상황"), "world"],
    ["intent", tr("원하는 상호작용"), "direction"], ["ending", tr("원하는 결말"), "direction"]];
  for (const [name, label, tab] of fields) {
    const input = form.elements.namedItem(name);
    if (!input.value.trim()) {
      activateTab(tab);
      input.focus();
      input.scrollIntoView({block: "center"});
      throw new Error(tr("{0} 항목을 입력해주세요.", {0: label}));
    }
  }
  for (const [name, label] of [["duration", tr("목표 길이")], ["shot_count", tr("컷 수")]]) {
    const input = form.elements.namedItem(name);
    const min = Number(input.min), max = Number(input.max);
    const value = Number(input.value);
    if (!Number.isFinite(value) || value < min || value > max || (name === "shot_count" && !Number.isInteger(value))) {
      input.focus();
      throw new Error(tr("{0}는 {1}~{2}{3}로 입력해주세요.", {0: label, 1: min, 2: max, 3: name === "shot_count" ? tr("개의 정수") : tr("초")}));
    }
  }
}

function sameData(left, right) {
  const canonical = (value) => {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
    return value;
  };
  return JSON.stringify(canonical(left)) === JSON.stringify(canonical(right));
}

function updateShotRecommendation() {
  const durationInput = form.elements.namedItem("duration");
  const duration = Number(durationInput.value);
  const countInput = form.elements.namedItem("shot_count");
  const hint = $("#shot-recommendation");
  $("#large-story-note").hidden = Number(countInput.value) <= 12 || !Number.isFinite(Number(countInput.value));
  if (!durationInput.value || !Number.isFinite(duration) || duration < Number(durationInput.min) || duration > Number(durationInput.max)) {
    hint.textContent = tr("유효한 목표 길이를 입력하면 권장 컷 수를 표시합니다.");
    return;
  }
  const lower = Math.max(Number(countInput.min), Math.floor(duration / 6));
  const upper = Math.max(lower, Math.ceil(duration / 4));
  hint.textContent = lower === upper ? tr("권장 컷 수: 약 {0}컷", {0: lower}) : tr("권장 컷 수: 약 {0}~{1}컷", {0: lower, 1: upper});
  if (upper > Number(countInput.max)) hint.textContent += " " + tr("현재 최대 {0}컷입니다. 긴 호흡으로 구성하거나 여러 콘티로 나누세요.", {0: countInput.max});
}

function fillBrief(brief) {
  buildCharacters(brief.characters);
  for (const [key, value] of Object.entries(brief)) {
    if (key !== "characters" && form.elements.namedItem(key)) form.elements.namedItem(key).value = value;
  }
  updateShotRecommendation();
}

function activateTab(name) {
  for (const tab of ["cast", "world", "direction"]) {
    $(`#tab-${tab}`).classList.toggle("active", tab === name);
    $(`#tab-${tab}`).setAttribute("aria-selected", String(tab === name));
    $(`#${tab}-panel`).hidden = tab !== name;
  }
}

function updateProvider(resetConsent = true) {
  const selected = providers.find((p) => p.id === $("#provider").value);
  if (!selected) return;
  $("#provider-note").textContent = I18n.system(selected.destination);
  $("#key-note").textContent = selected.configured ?
    (selected.id === "demo" ? tr("입력의 의미를 해석하지 않는 화면 체험용 템플릿입니다.") : tr("모델 ID를 확인해주세요. 연결과 모델 지원 여부는 요청 시 확인합니다.")) :
    tr("{0} 키가 설정되지 않았습니다. 상단 API 설정에서 등록해주세요.", {0: selected.name});
  $("#consent-label").hidden = selected.id === "demo";
  $("#model-required").hidden = selected.id === "demo";
  if (resetConsent) $("#consent").checked = false;
  $("#model").disabled = busy || selected.id === "demo";
  $("#model").placeholder = selected.id === "demo" ? tr("템플릿") : tr("정확한 모델 ID");
}

function aiSelection(requireAI = false) {
  const provider = $("#provider").value;
  const model = $("#model").value.trim();
  if (requireAI && provider === "demo") throw new Error(tr("의미 검수에는 Ollama, OpenAI 또는 Claude를 선택해주세요."));
  if (provider !== "demo") {
    if (!model) throw new Error(tr("모델 ID를 입력해주세요."));
    if (!$("#consent").checked) throw new Error(tr("제작 엔진에서 선택한 제공자로 전송하는 항목을 확인해주세요."));
    if (!providers.find((p) => p.id === provider)?.configured) throw new Error(tr("상단 API 설정에서 선택한 제공자의 키를 등록해주세요."));
  }
  return {provider, model};
}

function touch(doc, event) {
  doc.provenance.updated_at = new Date().toISOString();
  doc.history = doc.history.slice(-98);
  doc.history.push({at: doc.provenance.updated_at, event});
}

function renderReview() {
  const root = $("#review");
  root.replaceChildren();
  if (checks) {
    root.append(el("p", "review-summary", tr("형식 검증 완료 · 예상 {0}초 · 아래 항목을 검토하세요", {0: checks.total_duration})));
    for (const finding of checks.findings) root.append(findingNode(finding, true));
  }
  const ai = $("#ai-result");
  ai.replaceChildren();
  if (aiReview) {
    ai.append(el("p", "review-summary", tr("{0} · {1} 의미 검수", {0: aiReview.provider, 1: aiReview.model})),
      el("p", "helper", aiReview.result.summary));
    for (const finding of aiReview.result.findings) ai.append(findingNode(finding));
    ai.append(el("p", "helper", tr("AI 검수는 참고 의견입니다. 생성·편집·불러오기 후에는 다시 검수해야 합니다.")));
  } else ai.append(el("p", "helper", tr("현재 콘티에 대한 AI 의미 검수는 아직 실행하지 않았습니다.")));
}

function findingNode(finding, local = false) {
  const node = el("div", `finding ${finding.severity}`);
  node.append(el("strong", "", tr("{0} · {1}", {0: finding.shot_id || tr("전체"), 1: local ? I18n.system(finding.category) : finding.category})), el("span", "", local ? I18n.system(finding.message) : finding.message));
  return node;
}

function renderBoard() {
  $("#empty").hidden = !!project;
  $("#board").hidden = !project;
  if (!project) return;
  const {brief, story, provenance, history} = project;
  const names = Object.fromEntries(brief.characters.map((c) => [c.id, c.name]));
  $("#board-title").textContent = brief.title;
  $("#source").textContent = provenance.provider === "demo" ? tr("예시 템플릿") : provenance.provider.toUpperCase();
  $("#stats").textContent = tr("{0} CUTS · {1}초 · 고정 {2}컷", {0: story.shots.length, 1: story.shots.reduce((sum, s) => sum + s.duration, 0).toFixed(1), 2: story.shots.filter((s) => s.locked).length});
  $("#summary").textContent = story.summary;
  $("#beats").replaceChildren(...story.beats.map((b, i) => el("span", "beat", `${i + 1}. ${b}`)));
  $("#assumptions").replaceChildren(...story.assumptions.map((a) => el("p", "", `• ${a}`)));
  $("#provenance").textContent = tr("{0} / {1} · 생성 {2} · 수정 {3} · 불러온 파일의 출처 정보는 작성자 제공 값입니다.", {0: provenance.provider, 1: provenance.model, 2: provenance.created_at, 3: provenance.updated_at});
  const cards = story.shots.map((shot, index) => {
    const card = el("article", `shot${shot.locked ? " locked" : ""}`);
    const header = el("div", "shot-header");
    header.append(el("span", "shot-number", shot.id), el("span", "", tr("{0}초 · {1}", {0: shot.duration, 1: shot.scene_id})));
    const frame = el("div", "shot-frame");
    frame.append(el("span", "camera-tag", shot.camera.size), el("p", "", shot.visual),
      el("span", "frame-note", tr("TEXT BOARD · 패널 이미지 생성 전")));
    const body = el("div", "shot-body");
    body.append(el("p", "shot-purpose", shot.purpose));
    const actions = el("ol", "shot-actions");
    actions.append(...shot.actions.map((a) => el("li", "", a)));
    body.append(actions);
    for (const line of shot.dialogue) {
      const dialogue = el("p", "dialogue");
      dialogue.append(el("strong", "", names[line.speaker]), document.createTextNode(`“${line.text}”`), el("small", "", line.delivery));
      body.append(dialogue);
    }
    body.append(el("div", "shot-camera", `${shot.camera.angle} · ${shot.camera.movement} · ${shot.camera.transition}`));
    const state = el("details");
    state.append(el("summary", "", tr("상태와 연속성 보기")), el("p", "", shot.continuity),
      el("pre", "state-json", JSON.stringify({[tr("시작")]: shot.start_state, [tr("종료")]: shot.end_state}, null, 2)));
    body.append(state);
    const footer = el("div", "shot-footer");
    const lock = el("button", "lock-button", shot.locked ? tr("● 고정됨") : tr("○ 컷 고정"));
    lock.type = "button";
    lock.setAttribute("aria-pressed", String(shot.locked));
    lock.setAttribute("aria-label", tr("{0} {1}", {0: shot.id, 1: shot.locked ? tr("고정 해제") : tr("고정")}));
    lock.addEventListener("click", () => toggleLock(index));
    const edit = el("button", "quiet", tr("편집 ↗"));
    edit.type = "button";
    edit.setAttribute("aria-label", tr("{0} 편집", {0: shot.id}));
    edit.addEventListener("click", () => openEditor(index));
    footer.append(lock, edit);
    card.append(header, frame, body, footer);
    return card;
  });
  $("#shots").replaceChildren(...cards);
  $("#history").replaceChildren(...history.map((h) => el("li", "", `${h.at} · ${h.event}`)));
  renderReview();
}

async function toggleLock(index) {
  if (busy) return;
  const next = structuredClone(project);
  next.story.shots[index].locked = !next.story.shots[index].locked;
  touch(next, tr("{0} {1}", {0: next.story.shots[index].id, 1: next.story.shots[index].locked ? tr("고정") : tr("고정 해제")}));
  setBusy(true);
  try {
    const result = await api("/api/validate", {document: next});
    project = next; checks = result.review; aiReview = null; dirty = true;
    renderBoard();
    notice(tr("컷 고정 상태를 변경했습니다. JSON 저장으로 프로젝트를 보관하세요."));
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}

async function generate(regenerate = false) {
  if (busy) return;
  try {
    validateBriefInputs();
    const selection = aiSelection();
    const brief = readBrief();
    setBusy(true, tr("설정을 확인하고 있습니다…"));
    await api("/api/validate", {brief});
    if (project && !regenerate && !window.confirm(tr("현재 콘티를 새로 만듭니다. 필요한 경우 먼저 JSON으로 저장하세요. 계속할까요?"))) return;
    setBusy(true, selection.provider === "demo" ? tr("예시 템플릿을 준비하고 있습니다…") : brief.shot_count > 12
      ? tr("{0}에서 전체 흐름을 설계한 뒤 최대 6컷씩 생성하고 있습니다. 여러 API 호출로 시간이 더 걸릴 수 있습니다…", {0: selection.provider})
      : tr("{0}에서 콘티를 만들고 있습니다. 최대 약 3분이 걸릴 수 있습니다…", {0: selection.provider}));
    const result = await api("/api/generate", {brief, ...selection,
      previous: regenerate ? project : null, revision: regenerate ? $("#revision").value.trim() : ""});
    project = result.document; checks = result.review; aiReview = null; dirty = true;
    renderBoard();
    try {
      await api("/api/library/save", {document: project});
      dirty = false;
    } catch (error) {
      notice(tr("콘티는 생성됐지만 보관함 저장에 실패했습니다. JSON으로 저장해주세요. {0}", {0: error.message}), true);
      return;
    }
    notice(selection.provider === "demo" ? tr("예시 콘티입니다. 보관함에 저장했습니다. AI 생성과 페르소나 해석은 수행하지 않았습니다.") : tr("콘티 초안을 보관함에 저장했습니다. 검수 후 편집한 내용은 ‘보관함에 저장’으로 새 사본을 저장하세요."));
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}

function openEditor(index) {
  if (project.story.shots[index].locked) {
    notice(tr("고정 컷을 편집하려면 먼저 고정을 해제해주세요."), true);
    return;
  }
  editing = index;
  const shot = project.story.shots[index];
  $("#editor-title").textContent = tr("{0} · 컷 편집", {0: shot.id});
  $("#edit-error").textContent = "";
  for (const key of ["duration", "purpose", "visual", "continuity"]) $(`#edit-${key}`).value = shot[key];
  $("#edit-scene").value = shot.scene_id;
  $("#edit-actions").value = shot.actions.join("\n");
  for (const key of ["size", "angle", "movement", "transition"]) $(`#edit-${key}`).value = shot.camera[key];
  $("#edit-dialogue").replaceChildren();
  shot.dialogue.forEach(addDialogue);
  $("#edit-json").value = JSON.stringify({start_state: shot.start_state, end_state: shot.end_state}, null, 2);
  $("#editor").showModal();
}

function addDialogue(line = null) {
  const row = el("div", "edit-line");
  const speakerLabel = el("label", "", tr("말하는 인물"));
  I18n.bindText(speakerLabel.firstChild, "말하는 인물");
  const speaker = el("select", "line-speaker");
  for (const character of project.brief.characters) {
    const option = el("option", "", character.name);
    option.value = character.id;
    speaker.append(option);
  }
  if (line) speaker.value = line.speaker;
  speakerLabel.append(speaker);
  const text = inputField(tr("대사"), "", true, true);
  text.lastChild.className = "line-text";
  text.lastChild.value = line?.text || "";
  const delivery = inputField(tr("말하는 방식"), "");
  delivery.lastChild.className = "line-delivery";
  delivery.lastChild.value = line?.delivery || "";
  const remove = el("button", "quiet", tr("대사 삭제"));
  I18n.bindText(remove.firstChild, "대사 삭제");
  remove.type = "button";
  remove.addEventListener("click", () => row.remove());
  row.append(speakerLabel, text, delivery, remove);
  $("#edit-dialogue").append(row);
}

async function saveEdit(event) {
  event.preventDefault();
  if (busy || editing === null) return;
  try {
    const shot = structuredClone(project.story.shots[editing]);
    for (const key of ["purpose", "visual", "continuity"]) shot[key] = $(`#edit-${key}`).value.trim();
    shot.duration = Number($("#edit-duration").value);
    shot.scene_id = $("#edit-scene").value.trim();
    shot.actions = $("#edit-actions").value.split("\n").map((v) => v.trim()).filter(Boolean);
    for (const key of ["size", "angle", "movement", "transition"]) shot.camera[key] = $(`#edit-${key}`).value.trim();
    shot.dialogue = [...document.querySelectorAll(".edit-line")].map((row) => ({
      speaker: row.querySelector(".line-speaker").value, text: row.querySelector(".line-text").value.trim(),
      delivery: row.querySelector(".line-delivery").value.trim(),
    }));
    const states = parseJSON($("#edit-json").value);
    if (!states || typeof states !== "object" || Object.keys(states).sort().join(",") !== "end_state,start_state") throw new Error(tr("상태 데이터에는 start_state와 end_state만 있어야 합니다."));
    shot.start_state = states.start_state;
    shot.end_state = states.end_state;
    const next = structuredClone(project);
    next.story.shots[editing] = shot;
    touch(next, tr("{0} 수동 편집 · 모든 컷 연결 재검수", {0: shot.id}));
    setBusy(true);
    const result = await api("/api/validate", {document: next});
    project = next; checks = result.review; aiReview = null; dirty = true;
    renderBoard();
    $("#editor").close();
    notice(tr("컷을 저장하고 모든 컷의 연결을 재검수했습니다. AI 의미 검수는 다시 실행해주세요."));
  } catch (error) { $("#edit-error").textContent = error.message; }
  finally { setBusy(false); }
}

function download(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], {type}));
  const link = el("a");
  link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function exportProject(asMarkdown = false) {
  if (!project || busy) return;
  const pendingInput = !sameData(readBrief(), project.brief);
  setBusy(true);
  try {
    await api("/api/validate", {document: project});
    if (asMarkdown) {
      const result = await api("/api/export", {document: project});
      download(result.markdown, "storyboard.md", "text/markdown;charset=utf-8");
    } else {
      download(JSON.stringify(project, null, 2), "storyboard.project.json", "application/json");
      dirty = pendingInput;
    }
    notice((asMarkdown ? tr("콘티 문서를 내보냈습니다. 이어서 편집하려면 프로젝트 JSON도 저장하세요.") : tr("프로젝트 JSON 다운로드를 요청했습니다. 저장된 파일로 이어서 작업할 수 있습니다.")) +
      (pendingInput ? tr(" 현재 수정 중인 입력은 기존 콘티와 다릅니다. 입력 저장으로 따로 보관하거나 다시 생성하세요.") : ""));
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}

async function importFile(event) {
  const file = event.target.files[0];
  if (!file || busy) return;
  try {
    if (file.size > 16000000) throw new Error(tr("JSON 파일은 16MB 이내여야 합니다."));
    const value = parseJSON((await file.text()).replace(/^\uFEFF/, ""));
    const isProject = value && Object.hasOwn(value, "schema_version");
    const result = await api("/api/validate", isProject ? {document: value} : {brief: value});
    if ((project || dirty) && !window.confirm(tr("현재 입력과 콘티를 불러온 파일로 바꿉니다. 계속할까요?"))) return;
    fillBrief(isProject ? value.brief : value);
    project = isProject ? value : null; checks = isProject ? result.review : null; aiReview = null;
    dirty = !isProject;
    if (!isProject) { $("#board-title").textContent = tr("첫 장면을 기다리고 있어요"); $("#source").textContent = tr("DRAFT"); }
    renderBoard();
    notice(isProject ? tr("프로젝트를 불러왔습니다. AI 의미 검수는 다시 실행해주세요.") : tr("캐릭터와 장면 설정을 불러왔습니다."));
  } catch (error) { notice(tr("불러오기 실패: {0}", {0: error.message}), true); }
  finally { event.target.value = ""; }
}

async function loadExample() {
  if (busy) return false;
  if ((project || dirty) && !window.confirm(tr("현재 입력을 예시 설정으로 바꿉니다. 기존 콘티는 새 생성 전까지 유지됩니다. 계속할까요?"))) return false;
  const brief = await api("/api/example");
  fillBrief(brief); dirty = true;
  notice(tr("예시 설정을 채웠습니다. 제공자를 선택해 콘티를 만들어보세요."));
  return true;
}

function markRequired(root) {
  root.querySelectorAll("[required]").forEach((input) => {
    const label = input.closest("label");
    if (!label || label.querySelector(".required-mark")) return;
    const marker = el("span", "required-mark", " # ");
    marker.setAttribute("aria-label", tr("필수 입력"));
    label.insertBefore(marker, input);
  });
}
buildCharacters();
markRequired(form);
updateShotRecommendation();
$("#add-character").addEventListener("click", () => {
  if (busy) return;
  const characters = readCharacters();
  if (characters.length >= 5) return;
  let next = 1;
  while (characters.some((character) => character.id === `character_${next}`)) next++;
  characters.push({id: `character_${next}`});
  buildCharacters(characters);
  dirty = true;
  form.elements.namedItem(`c${characters.length - 1}_name`).focus();
});
// Hidden required controls are validated by the API, so tabs never block submission.
form.noValidate = true;
form.addEventListener("submit", (event) => { event.preventDefault(); generate(); });
form.addEventListener("input", (event) => {
  if (["duration", "shot_count"].includes(event.target.name)) updateShotRecommendation();
  if (event.target.name) dirty = true;
  if (event.target.id === "model") models.set($("#provider").value, event.target.value);
});
for (const name of ["cast", "world", "direction"]) {
  $(`#tab-${name}`).addEventListener("click", () => activateTab(name));
}
$("#provider").addEventListener("change", () => {
  const selected = providers.find((p) => p.id === $("#provider").value);
  $("#model").value = models.get(selected?.id) ?? selected?.model ?? "";
  updateProvider();
});
$("#example").addEventListener("click", () => loadExample().catch((e) => notice(e.message, true)));
$("#try-demo").addEventListener("click", async () => {
  try {
    if (!await loadExample()) return;
    $("#provider").value = "demo"; updateProvider();
    await generate();
  } catch (error) { notice(error.message, true); }
});
$("#regenerate").addEventListener("click", () => generate(true));
$("#export-json").addEventListener("click", () => exportProject());
$("#export-md").addEventListener("click", () => exportProject(true));
$("#import").addEventListener("click", () => $("#file").click());
$("#file").addEventListener("change", importFile);
$("#save-input").addEventListener("click", async () => {
  try {
    validateBriefInputs();
    const brief = readBrief();
    await api("/api/validate", {brief});
    download(JSON.stringify(brief, null, 2), "storyboard.input.json", "application/json");
    if (!project) dirty = false;
    notice(tr("입력 JSON 다운로드를 요청했습니다. 콘티는 프로젝트 JSON으로 따로 저장하세요."));
  } catch (error) { notice(error.message, true); }
});
$("#validate").addEventListener("click", async () => {
  if (!project || busy) return;
  setBusy(true);
  try { checks = (await api("/api/validate", {document: project})).review; renderReview(); notice(tr("모든 컷의 형식과 상태 연결을 다시 검사했습니다.")); }
  catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
});
$("#ai-review").addEventListener("click", async () => {
  if (!project || busy) return;
  try {
    const selection = aiSelection(true);
    setBusy(true, tr("{0}에서 현재 콘티의 의미를 검수하고 있습니다…", {0: selection.provider}));
    aiReview = (await api("/api/review", {document: project, ...selection})).ai_review;
    renderReview(); notice(tr("AI 검수 의견을 받았습니다. 검수 결과를 참고해 최종 판단해주세요."));
  } catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
});
$("#close-editor").addEventListener("click", () => $("#editor").close());
$("#add-line").addEventListener("click", () => addDialogue());
$("#edit-form").addEventListener("submit", saveEdit);
window.addEventListener("beforeunload", (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });

$("#settings-open").addEventListener("click", openSettings);
$("#settings-close").addEventListener("click", () => $("#settings-dialog").close());
$("#settings-form").addEventListener("submit", saveSettings);
$("#settings-provider").addEventListener("change", showSettingsProvider);
$("#settings-dialog").addEventListener("close", () => {
  $("#settings-openai-key").value = "";
  $("#settings-claude-key").value = "";
  $("#settings-lmstudio-key").value = "";
});
api("/api/config").then((value) => applyConfig(value))
  .catch((error) => notice(tr("설정을 불러오지 못했습니다: {0}", {0: error.message}), true));

let studioView = "create";
let libraryItems = [];
let conversionBoard = null;
let conversionBoardId = null;
let conversionResult = null;
let visiblePlan = null;
let clipLengths = {};
let conversionEntries = [];

async function switchStudio(view) {
  studioView = view;
  document.querySelector("main").dataset.studio = view;
  if ($("#conversion-picker").open) $("#conversion-picker").close();
  (view === "convert" ? $("#conversion-picker-content") : $("#library-home")).append($("#library-view"));
  $("#creation-view").hidden = view !== "create";
  $("#library-view").hidden = view === "create";
  $("#conversion-view").hidden = view !== "convert";
  for (const name of ["create", "manage", "convert"]) {
    const button = $(`#nav-${name}`);
    button.className = "studio-tab";
    if (name === view) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
  $("#library-title").textContent = view === "convert" ? tr("변환할 콘티 선택") : tr("저장한 콘티");
  if (view !== "create") await refreshLibrary();
  if (view === "convert" && !conversionBoard) $("#conversion-picker").showModal();
}

async function refreshLibrary() {
  libraryItems = (await api("/api/library/list", {deleted: $("#library-filter").value === "trash"})).items;
  renderLibrary();
}

function renderLibrary() {
  const container = $("#library-items");
  container.replaceChildren();
  const query = $("#library-search").value.trim().toLocaleLowerCase();
  const items = libraryItems.filter((item) => item.title.toLocaleLowerCase().includes(query));
  const sort = $("#library-sort").value;
  items.sort((a, b) => sort === "title" ? a.title.localeCompare(b.title, I18n.locale) :
    sort === "oldest" ? a.saved_at.localeCompare(b.saved_at) : b.saved_at.localeCompare(a.saved_at));
  $("#library-count").textContent = tr("{0}개 표시 / 전체 {1}개", {0: items.length, 1: libraryItems.length});
  if (!items.length) {
    const empty = el("div", "library-empty");
    empty.append(el("h3", "", tr(query ? "검색 결과가 없습니다." : $("#library-filter").value === "trash" ? "휴지통이 비어 있습니다." : "저장한 콘티가 없습니다.")),
      el("p", "helper", tr(query ? "다른 제목으로 검색하거나 검색어를 지워주세요." : $("#library-filter").value === "trash" ? "삭제한 콘티가 이곳에 표시됩니다." : "콘티를 제작하거나 JSON을 불러온 후 보관함에 저장하세요.")));
    container.append(empty);
  }
  for (const item of items) {
    const card = el("article", "library-card library-row");
    const identity = el("div", "library-identity");
    const symbol = el("span", "library-symbol", "▤"); symbol.setAttribute("aria-hidden", "true");
    identity.append(symbol, el("h3", "", item.title));
    const date = el("time", "library-date", new Date(item.saved_at).toLocaleString(I18n.locale, {year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"}));
    date.dateTime = item.saved_at;
    card.append(identity, el("span", "library-shot-count", tr("{0}컷", {0: item.shots})), el("span", "library-duration", tr("{0}초", {0: item.duration})), date);
    const buttons = el("div", "header-actions library-row-actions");
    const action = (label, callback, className = "quiet") => {
      const button = el("button", className, label);
      button.addEventListener("click", () => libraryAction(callback));
      buttons.append(button);
    };
    if ($("#library-filter").value === "trash") {
      action(tr("복원"), async () => { await api("/api/library/restore", {id: item.id}); await refreshLibrary(); }, "secondary");
    } else {
      action(tr("내용 미리보기"), async () => {
        const saved = await api("/api/library/load", {id: item.id});
        previewDocument = saved.document;
        renderSavedPreview(); $("#saved-preview").showModal();
      });
      action(studioView === "convert" ? tr("이 콘티 선택") : tr("불러오기"), () => loadSaved(item.id, studioView === "convert"), studioView === "convert" ? "secondary library-main-action" : "quiet");
      if (studioView !== "convert") action(tr("프롬프트로 변환"), async () => { await switchStudio("convert"); await loadSaved(item.id, true); }, "secondary library-main-action");
      action(tr("삭제"), async () => {
        if (!window.confirm(tr("‘{0}’ 콘티를 휴지통으로 이동할까요? 복원할 수 있습니다.", {0: item.title}))) return;
        await api("/api/library/delete", {id: item.id});
        if (conversionBoardId === item.id) clearConversion();
        await refreshLibrary();
        notice(tr("휴지통으로 이동했습니다. 보관함에서 휴지통을 선택하면 복원할 수 있습니다."));
      }, "quiet library-delete");
    }
    card.append(buttons); container.append(card);
  }
}

async function libraryAction(callback) {
  if (busy) return;
  setBusy(true);
  try { await callback(); }
  catch (error) { notice(error.message, true); }
  finally { setBusy(false); }
}

async function loadSaved(id, forConversion) {
  if (!forConversion && dirty && !window.confirm(tr("저장하지 않은 변경을 불러올 콘티로 바꿀까요?"))) return;
  const result = await api("/api/library/load", {id});
  if (forConversion) {
    clearConversion();
    conversionBoardId = id; conversionBoard = result.document;
    referenceItems = result.references || [];
    await ensureGuides();
    renderOverview($("#conversion-overview"), conversionBoard);
    renderReferences();
    applyGuide();
    updateConversionAI();
    $("#conversion-source").textContent = tr("선택한 콘티: {0}", {0: conversionBoard.brief.title});
    $("#conversion-controls").hidden = false;
    $("#conversion-preview").hidden = false;
    if ($("#conversion-picker").open) $("#conversion-picker").close();
    for (const shot of conversionBoard.story.shots) {
      const row = el("div", "conversion-shot-row");
      const label = el("label", "check library-card");
      const checkbox = el("input"); checkbox.type = "checkbox"; checkbox.value = shot.id; checkbox.checked = true;
      checkbox.addEventListener("change", invalidateConversion);
      label.append(checkbox, document.createTextNode(tr("{0} · {1}초 · {2}", {0: shot.id, 1: shot.duration, 2: shot.purpose})));
      row.append(label, shotDetails(shot));
      $("#conversion-shots").append(row);
    }
    updateConversionSelection();
    for (const saved of [...result.conversions].reverse()) renderConversion(saved.result, saved.created_at, true, saved.id);
    $("#conversion-source").scrollIntoView({behavior: "smooth", block: "start"});
  } else {
    project = result.document; checks = result.review; aiReview = null; dirty = false;
    fillBrief(project.brief); renderBoard(); await switchStudio("create");
  }
  notice(forConversion ? tr("콘티를 불러왔습니다. 컷과 가이드를 설정하세요.") : tr("저장한 콘티를 불러왔습니다."));
}

function clearConversion() {
  conversionBoard = null; conversionBoardId = null; conversionResult = null;
  referenceItems = [];
  visiblePlan = null; conversionEntries = [];
  clipLengths = {};
  $("#conversion-controls").hidden = true;
  $("#conversion-preview").hidden = true;
  $("#conversion-selection").textContent = "";
  $("#conversion-source").textContent = tr("관리 목록에서 변환할 콘티를 선택하세요.");
  $("#conversion-shots").replaceChildren();
  $("#conversion-plan-result").replaceChildren();
  $("#conversion-results").replaceChildren();
}

function invalidateConversion() {
  clipLengths = {};
  updateConversionSelection();
  $("#conversion-consent").checked = false;
  conversionResult = null;
  visiblePlan = null;
  $("#conversion-plan-result").replaceChildren();
}

function updateConversionSelection() {
  if (!conversionBoard) return;
  const selected = new Set([...document.querySelectorAll("#conversion-shots input:checked")].map((input) => input.value));
  const shots = conversionBoard.story.shots.filter((shot) => selected.has(shot.id));
  $("#conversion-selection").textContent = tr("{0} / {1}컷 선택 · {2}초", {0: shots.length, 1: conversionBoard.story.shots.length, 2: Number(shots.reduce((sum, shot) => sum + shot.duration, 0).toFixed(2))});
}

function updateConversionAI() {
  const provider = providers.find((item) => item.id === $("#conversion-ai-provider").value);
  $("#conversion-ai-model").value = provider?.model || "";
  $("#conversion-ai-note").textContent = provider ? tr("{0} · {1}", {0: provider.label || provider.id, 1: I18n.system(provider.destination || tr("API 설정의 연결 사용"))}) : tr("상단 API 설정에서 연결을 등록하세요.");
  $("#conversion-consent").checked = false;
  if (!$("#conversion-ai-model").value) $("#conversion-ai-model").closest("details").open = true;
}

function conversionPayload() {
  if (!conversionBoardId) throw new Error(tr("변환할 콘티를 선택해주세요."));
  return {id: conversionBoardId,
    selected: [...document.querySelectorAll("#conversion-shots input:checked")].map((node) => node.value),
    limit: Number($("#clip-limit").value), split_mode: $("#split-mode").value, clip_durations: clipLengths, target_model: $("#target-model").value.trim(),
    guide_source: $("#guide-source").value.trim(), guide: $("#conversion-guide").value.trim(),
    guide_id: $("#video-family").value === "custom" ? null : `${$("#video-family").value === "minimax" ? "minimax-h3" : "seedance-2"}-${$("#video-guide").value}`,
    references: $("#video-family").value !== "custom" && $("#video-guide").value === "reference" ? referenceItems : []};
}

function renderPlan(plan) {
  visiblePlan = plan;
  const container = $("#conversion-plan-result"); container.replaceChildren();
  container.append(el("h3", "", tr("{0}개 클립 · 각 {1}초 이내", {0: plan.clips.length, 1: plan.max_seconds})));
  if (plan.split_mode === "auto") container.append(el("p", "helper plan-total", tr("원본 {0}초 → 영상 {1}초 · 길이 추천은 추정치입니다.", {0: plan.original_selected_duration, 1: Number(plan.clips.reduce((sum, c) => sum + c.duration, 0).toFixed(2))})));
  if (plan.split_mode === "speech") container.append(el("p", "helper", tr("대사 시간 확보: 원본 {0}초 → 계획 {1}초 · 추정치이며 원본은 유지됩니다.", {0: plan.original_selected_duration, 1: plan.clips.reduce((sum, c) => sum + c.duration, 0)})));
  if (plan.notes?.length) {
    const notes = el("details", "plan-notes"); notes.append(el("summary", "", tr("검토 메모 ({0})", {0: plan.notes.length})));
    for (const note of plan.notes) notes.append(el("p", "helper", I18n.system(note)));
    container.append(notes);
  }
  for (const clip of plan.clips) {
    const card = el("article", "library-card");
    card.append(el("h4", "", tr("{0} · {1}초", {0: clip.id, 1: clip.duration})),
      el("p", "", plan.split_mode === "auto" ? clip.shots.map((shot) => shot.id).join(" · ") : clip.shots.map((shot) => tr("{0}–{1}초 {2}", {0: shot.start, 1: shot.end, 2: shot.id})).join(" / ")));
    if (plan.split_mode === "auto") {
      const label = el("label", "clip-duration-control", tr("클립 길이 · 초")), input = el("input");
      input.type = "number"; input.min = $("#video-family").value === "custom" ? "1" : "4";
      input.max = plan.max_seconds; input.step = $("#video-family").value === "custom" ? "0.1" : "1";
      input.value = clip.duration; input.dataset.clipDuration = clip.id;
      input.setAttribute("aria-label", tr("{0} 클립 길이 · 초", {0: clip.id}));
      input.addEventListener("change", async () => {
        clipLengths[clip.id] = input.value === "" ? null : Number(input.value);
        $("#conversion-consent").checked = false; conversionResult = null;
        await libraryAction(async () => renderPlan((await api("/api/conversion/plan", conversionPayload())).plan));
        document.querySelector(`[data-clip-duration='${clip.id}']`)?.focus({preventScroll: true});
      });
      label.append(input); card.append(label);
      card.append(el("p", "helper", tr("추천 {0}초 · {1}", {0: clip.recommended_duration, 1: tr(clip.break_reason === "continuation" ? "긴 컷의 동작 이어가기" : "컷 끝에서 연결")})));
      const estimate = Number(clip.shots.reduce((sum, shot) => sum + shot.speech_estimate_seconds, 0).toFixed(1));
      if (estimate) card.append(el("p", estimate > clip.duration ? "plan-pacing-warning" : "helper", tr("대사 예상 약 {0}초 · 실제 낭독으로 확인하세요.", {0: estimate})));
    }
    const detail = el("details", "plan-detail"); detail.append(el("summary", "", tr("대사와 연결 확인")));
    if (["fixed", "auto"].includes(plan.split_mode)) {
      const range = el("p", "helper", tr("원본 {0}–{1}초", {0: clip.timeline_start, 1: clip.timeline_end}));
      (plan.split_mode === "auto" ? detail : card).append(range);
      for (const shot of clip.shots) {
        if (shot.continues_from_previous || shot.continues_in_next) detail.append(el("p", "helper", tr("{0}: 원본 컷의 {1}–{2}초 부분 · 앞뒤 구간과 동작 연결", {0: shot.id, 1: shot.source_offset, 2: shot.source_end})));
        for (const line of shot.source.dialogue) detail.append(el("p", "", `${shot.id} · ${line.speaker}: ${line.text}`));
      }
    }
    if (plan.split_mode === "speech") for (const shot of clip.shots) for (const line of shot.source.dialogue) detail.append(el("p", "", `${shot.id} · ${line.speaker}: ${line.text}`));
    if (detail.childElementCount > 1) card.append(detail);
    container.append(card);
  }
}

async function copyPromptText(text) {
  try {
    if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(text); return; }
  } catch { /* Try the browser's selection-based copy in the same user action. */ }
  const field = document.createElement("textarea");
  field.value = text; field.style.cssText = "position:fixed;left:-9999px;top:0";
  const focused = document.activeElement;
  (focused?.closest("dialog[open]") || document.body).append(field);
  try {
    field.select();
    if (!document.execCommand("copy")) throw new Error("Clipboard unavailable");
  } finally { field.remove(); focused?.focus({preventScroll: true}); }
}

function renderConversion(result, date = "", remember = true, savedId = null) {
  if (remember) conversionEntries.push({result, date, savedId});
  const section = el("details", "library-card conversion-result"); section.open = true;
  const heading = el("summary", "result-heading");
  heading.append(el("h3", "", tr("{0} · {1}", {0: result.target_model, 1: date ? new Date(date).toLocaleString(I18n.locale) : tr("방금 변환")})));
  const metadata = el("details", "result-metadata"); metadata.append(el("summary", "", tr("생성 정보와 가이드 출처")), el("p", "helper", tr("가이드 출처: {0}", {0: result.guide_source})));
  section.append(heading, el("p", "helper", I18n.system(result.review_note)), metadata);
  if (result.validation_report?.repaired) metadata.append(el("p", "helper", tr("출력 오류를 1회 자동 교정한 뒤 다시 검증하여 저장했습니다.")));
  if (result.output.notes?.length) {
    const notes = el("details", "conversion-notes"); notes.append(el("summary", "", tr("검토 메모")));
    for (const note of result.output.notes) notes.append(el("p", "helper", I18n.system(note)));
    section.append(notes);
  }
  for (const clip of result.output.clips) {
    const detail = el("details", "prompt-clip"); detail.open = clip === result.output.clips[0];
    const planned = result.plan.clips.find((item) => item.id === clip.id);
    detail.append(el("summary", "", tr("{0} · {1}초", {0: clip.id, 1: planned.duration})), el("pre", "prompt-output", clip.prompt));
    const row = el("div", "prompt-clip-row");
    const copy = el("button", "secondary prompt-copy", tr("프롬프트 복사")); copy.type = "button";
    copy.setAttribute("aria-label", tr("{0} 프롬프트 복사", {0: clip.id}));
    const status = el("span", "helper prompt-copy-status"); status.setAttribute("role", "status");
    copy.addEventListener("click", async () => {
      copy.disabled = true;
      try { await copyPromptText(clip.prompt); status.textContent = tr("복사했습니다."); }
      catch { status.textContent = tr("복사하지 못했습니다. 프롬프트 본문을 선택해 복사해주세요."); }
      finally { copy.disabled = false; }
    });
    const actions = el("div", "prompt-copy-actions"); actions.append(status, copy);
    row.append(detail, actions); section.append(row);
  }
  const downloads = el("div", "result-downloads"); section.insertBefore(downloads, section.children[1]);
  const exportButton = el("button", "secondary", tr("프롬프트 JSON 저장"));
  exportButton.addEventListener("click", () => download(JSON.stringify(result, null, 2), "video-prompts.json", "application/json"));
  document.querySelectorAll("#conversion-results > details").forEach((previous) => { previous.open = false; });
  $("#conversion-results").prepend(section);
  const textButton = el("button", "secondary", tr("전체 프롬프트 TXT 저장"));
  textButton.addEventListener("click", () => {
    try { download(promptText(result), "video-prompts.txt", "text/plain;charset=utf-8"); }
    catch (error) { notice(error.message, true); }
  });
  textButton.className = "primary";
  downloads.append(textButton, exportButton);
  if (result.references?.length) {
    const list = el("ol", "reference-manifest");
    for (const item of result.references) list.append(el("li", "", `${item.label} · ${item.role === "environment" ? tr("배경") : item.character_id} · ${tr(referenceRoles[item.role])} · ${item.name} · ${item.note}`));
    const detail = el("details", "result-references"); detail.append(el("summary", "", tr("참조 이미지 첨부 순서")), list); section.append(detail);
  }
  if (savedId) {
    const link = el("a", "secondary", tr("프롬프트와 참조 이미지 ZIP 저장"));
    link.href = `/api/conversion/package/${savedId}`; link.download = "video-production.zip";
    downloads.append(link);
  }
}

function promptText(result) {
  if (result.output_language !== "english_except_dialogue") throw new Error(tr("영어 전용 규칙 적용 전 결과입니다. 콘티를 다시 변환해주세요."));
  const model = /^[\x20-\x7e]+$/.test(result.target_model) ? result.target_model : "Custom video model";
  const lines = ["VIDEO PROMPTS", "=".repeat(60), model, ""];
  if (result.output.english_notes?.length) lines.push("REVIEW NOTES", ...result.output.english_notes, "");
  if (result.references?.length) {
    lines.push("REFERENCE ATTACHMENT ORDER");
    for (const item of result.references) {
      const translated = result.english_reference_notes.find((note) => note.label === item.label);
      lines.push(`${item.order}. ${item.label} | ${item.role === "environment" ? "Background" : result.render_labels[item.character_id]} | ${item.role}${translated.note ? ` | ${translated.note}` : ""}`);
    }
    lines.push("");
  }
  for (const clip of result.output.clips) {
    const planned = result.plan.clips.find((item) => item.id === clip.id);
    lines.push("-".repeat(60), `${clip.id} | ${planned.duration}s`);
    if (planned.timeline_start !== undefined) lines.push(`Source ${planned.timeline_start}–${planned.timeline_end}s`);
    lines.push("-".repeat(60), "", clip.prompt.trim(), "");
  }
  return lines.join("\n").replace(/\r?\n/g, "\r\n");
}

for (const view of ["create", "manage", "convert"]) {
  $(`#nav-${view}`).addEventListener("click", () => libraryAction(() => switchStudio(view)));
}
$("#library-refresh").addEventListener("click", () => libraryAction(refreshLibrary));
$("#library-search").addEventListener("input", renderLibrary);
$("#library-sort").addEventListener("change", renderLibrary);
$("#library-filter").addEventListener("change", () => libraryAction(refreshLibrary));
$("#library-save").addEventListener("click", () => libraryAction(async () => {
  if (!project) throw new Error(tr("먼저 콘티를 제작하거나 불러오세요."));
  await api("/api/library/save", {document: project});
  dirty = !sameData(readBrief(), project.brief);
  notice(tr("현재 콘티를 보관함에 새 사본으로 저장했습니다. 변경 중인 입력은 콘티에 자동 반영되지 않습니다."));
}));
$("#conversion-choose").addEventListener("click", () => libraryAction(async () => { await refreshLibrary(); $("#conversion-picker").showModal(); }));
$("#conversion-picker-close").addEventListener("click", () => $("#conversion-picker").close());
$("#conversion-select-all").addEventListener("click", () => {
  document.querySelectorAll("#conversion-shots input").forEach((input) => { input.checked = true; }); invalidateConversion();
});
$("#conversion-preview").addEventListener("click", () => { previewDocument = conversionBoard; renderSavedPreview(); $("#saved-preview").showModal(); });
for (const selector of ["#clip-limit", "#split-mode", "#target-model", "#guide-source", "#conversion-guide"]) {
  $(selector).addEventListener("input", invalidateConversion);
}
$("#conversion-plan").addEventListener("click", () => libraryAction(async () => {
  $("#split-mode").value = "auto";
  invalidateConversion();
  renderPlan((await api("/api/conversion/plan", conversionPayload())).plan);
}));
$("#conversion-split-apply").addEventListener("click", () => libraryAction(async () => {
  invalidateConversion();
  renderPlan((await api("/api/conversion/plan", conversionPayload())).plan);
}));
$("#conversion-auto-split").addEventListener("click", () => libraryAction(async () => {
  $("#clip-limit").value = "15"; $("#split-mode").value = "fixed";
  document.querySelectorAll("#conversion-shots input[type='checkbox']").forEach((input) => { input.checked = true; });
  invalidateConversion();
  renderPlan((await api("/api/conversion/plan", conversionPayload())).plan);
  notice(tr("전체 콘티를 15초 기준으로 나눴습니다. 구간과 대사 배치를 확인한 뒤 프롬프트를 변환하세요."));
  $("#conversion-plan-result").scrollIntoView({behavior: "smooth", block: "start"});
}));
$("#conversion-speech-plan").addEventListener("click", () => libraryAction(async () => {
  $("#clip-limit").value = "15"; $("#split-mode").value = "speech";
  invalidateConversion();
  renderPlan((await api("/api/conversion/plan", conversionPayload())).plan);
  notice(tr("대사 시간을 확보하도록 계획했습니다. 늘어난 전체 길이와 클립 수를 확인하세요."));
  $("#conversion-plan-result").scrollIntoView({behavior: "smooth", block: "start"});
}));
$("#conversion-run").addEventListener("click", () => libraryAction(async () => {
  const payload = conversionPayload();
  if (!payload.target_model || !payload.guide_source || !payload.guide) throw new Error(tr("대상 영상 모델과 가이드 출처·본문을 입력해주세요."));
  const selection = {provider: $("#conversion-ai-provider").value, model: $("#conversion-ai-model").value.trim()};
  if (!selection.model) { $("#conversion-ai-model").closest("details").open = true; $("#conversion-ai-model").focus(); throw new Error(tr("변환 AI 모델 ID를 입력해주세요.")); }
  if (!$("#conversion-consent").checked) throw new Error(tr("콘티와 가이드의 AI 전송에 동의해주세요."));
  renderPlan((await api("/api/conversion/plan", payload)).plan);
  notice(tr("선택한 AI에 콘티와 가이드를 전송해 변환하고 있습니다…"));
  const response = await api("/api/conversion/compile", {...payload, ...selection});
  conversionResult = response.result;
  renderPlan(conversionResult.plan);
  renderConversion(conversionResult, "", true, response.id);
  $("#conversion-results").scrollIntoView({behavior: "smooth", block: "start"});
  notice(tr("프롬프트를 변환해 보관했습니다. 영상 제작 전에 의미와 가이드 준수 여부를 검토해주세요."));
}));
$("#conversion-ai-provider").addEventListener("change", updateConversionAI);
$("#conversion-ai-model").addEventListener("input", () => { $("#conversion-consent").checked = false; });
for (const selector of ["#clip-limit", "#target-model", "#guide-source", "#conversion-guide", "#conversion-ai-model", "#conversion-consent"]) {
  const input = $(selector);
  const marker = el("span", "required-mark", " # ");
  marker.setAttribute("aria-label", tr("필수 입력"));
  input.closest("label").insertBefore(marker, input);
}
document.querySelectorAll("label:not(.check)").forEach((label) => {
  if (![...label.children].some((node) => node.classList.contains("required-mark"))) return;
  const caption = el("span", "field-label");
  for (const node of [...label.childNodes]) {
    if (node.nodeType === Node.TEXT_NODE || node.classList?.contains("required-mark")) caption.append(node);
  }
  label.prepend(caption);
});

function closeLanguageMenu(focus = false) {
  $("#language-menu").hidden = true;
  $("#language-toggle").setAttribute("aria-expanded", "false");
  if (focus) $("#language-toggle").focus();
}
$("#language-toggle").addEventListener("click", () => {
  const open = $("#language-menu").hidden;
  $("#language-menu").hidden = !open;
  $("#language-toggle").setAttribute("aria-expanded", String(open));
  if (open) $("#language-menu [aria-pressed='true']").focus();
});
document.querySelectorAll("[data-language]").forEach((button) => {
  button.addEventListener("click", () => { I18n.select(button.dataset.language); closeLanguageMenu(true); });
});
document.addEventListener("click", (event) => {
  if (!event.target.closest(".language-control")) closeLanguageMenu();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !$("#language-menu").hidden) { event.preventDefault(); closeLanguageMenu(true); }
});
$(".language-control").addEventListener("focusout", (event) => {
  if (event.relatedTarget && !$(".language-control").contains(event.relatedTarget)) closeLanguageMenu();
});

window.addEventListener("languagechange", () => {
  updateShotRecommendation();
  updateCastControls();
  // Re-render UI chrome only. Never call generation, overwrite a form, or translate stored content.
  $("#notice").textContent = I18n.system($("#notice").textContent);
  for (const selector of ["#settings-error", "#edit-error"]) $(selector).textContent = I18n.system($(selector).textContent);
  if (project) renderBoard();
  else { $("#board-title").textContent = tr("첫 장면을 기다리고 있어요"); $("#source").textContent = tr("DRAFT"); }
  renderLibrary();
  $("#library-title").textContent = studioView === "convert" ? tr("변환할 콘티 선택") : tr("저장한 콘티");
  updateProvider(false);
  const selectedSettings = $("#settings-provider").value;
  $("#settings-save").textContent = tr("{0} 설정 저장", {0: providerNames[selectedSettings]});
  for (const id of ["openai", "claude", "lmstudio"]) {
    const provider = providers.find((item) => item.id === id);
    $(`#settings-${id}-status`).textContent = settingsKeyStatus(provider);
  }
  if ($("#editor").open && editing !== null) $("#editor-title").textContent = tr("{0} · 컷 편집", {0: project.story.shots[editing].id});
  if (conversionBoard) {
    $("#conversion-source").textContent = tr("선택한 콘티: {0}", {0: conversionBoard.brief.title});
    [...document.querySelectorAll("#conversion-shots label")].forEach((label, index) => {
      const shot = conversionBoard.story.shots[index];
      label.lastChild.nodeValue = tr("{0} · {1}초 · {2}", {0: shot.id, 1: shot.duration, 2: shot.purpose});
    });
    renderOverview($("#conversion-overview"), conversionBoard);
    renderReferences();
    applyGuide(false);
    updateConversionSelection();
    [...document.querySelectorAll("#conversion-shots details")].forEach((details, index) => {
      const replacement = shotDetails(conversionBoard.story.shots[index]); replacement.open = details.open; details.replaceWith(replacement);
    });
  } else $("#conversion-source").textContent = tr("관리 목록에서 변환할 콘티를 선택하세요.");
  $("#conversion-ai-note").textContent = I18n.system($("#conversion-ai-note").textContent);
  if (visiblePlan) renderPlan(visiblePlan);
  $("#conversion-results").replaceChildren();
  for (const entry of conversionEntries) renderConversion(entry.result, entry.date, false, entry.savedId);
  if (previewDocument) renderSavedPreview();
});
let guideCatalog = [], referenceItems = [], previewDocument = null;
const referenceRoles = {face: "얼굴", body: "전신", outfit: "의상", expression: "표정", detail: "세부 특징", environment: "배경 구조"};

function readOnlyField(container, label, value) {
  container.append(el("h4", "", tr(label)), el("pre", "source-text", sourceText(value)));
}

function sourceText(value, depth = 0) {
  const fields = {id: "ID", name: "이름", personality: "성격 · 상대를 대하는 태도", speech: "말투", desire: "원하는 것", fear: "두려운 것", habit: "행동 습관", fixed: "고정 설정", character_id: "캐릭터", characters: "캐릭터", props: "소품", position: "위치", pose: "자세", gaze: "시선", emotion: "감정", holder: "소유자", speaker: "말하는 인물", text: "대사", delivery: "대사 표현", size: "샷 크기", angle: "앵글", movement: "카메라 움직임", transition: "전환", beats: "이야기 흐름", assumptions: "가정"};
  fields.gender = "성별";
  fields.age = "연령";
  if (typeof value === "string") return value || "—";
  if (Array.isArray(value)) return value.length ? value.map((item, i) => `${i + 1}. ${sourceText(item, depth + 1)}`).join("\n\n") : "—";
  if (value && typeof value === "object") return Object.entries(value).map(([key, item]) => `${"  ".repeat(depth)}${tr(fields[key] || key)}: ${sourceText(item, depth + 1)}`).join("\n");
  return String(value ?? "—");
}

function renderOverview(container, doc) {
  container.replaceChildren(el("h3", "", doc.brief.title));
  readOnlyField(container, "이야기 요약", doc.story.summary);
  for (const [key, label] of Object.entries({location: "장소", time: "시간대", atmosphere: "분위기", situation: "시작 상황 · 위치 · 소품", relationship: "두 사람의 관계", intent: "원하는 상호작용", ending: "원하는 결말", required: "반드시 포함", excluded: "제외할 요소", style: "표현 스타일"})) readOnlyField(container, label, doc.brief[key]);
  readOnlyField(container, "캐릭터 페르소나", doc.brief.characters);
  readOnlyField(container, "스토리 비트와 가정", {beats: doc.story.beats, assumptions: doc.story.assumptions});
}

function shotDetails(shot) {
  const details = el("details", "source-shot");
  details.append(el("summary", "", tr("{0} 내용 펼치기", {0: shot.id})));
  for (const [key, label] of Object.entries({visual: "화면", actions: "행동", dialogue: "대사", camera: "카메라", start_state: "시작 상태", end_state: "종료 상태", continuity: "연속성"})) readOnlyField(details, label, shot[key]);
  return details;
}

function renderSavedPreview() {
  const container = $("#saved-preview-content");
  renderOverview(container, previewDocument);
  for (const shot of previewDocument.story.shots) {
    container.append(el("h3", "", `${shot.id} · ${shot.duration}s · ${shot.purpose}`), shotDetails(shot));
  }
}
$("#saved-preview-close").addEventListener("click", () => $("#saved-preview").close());
$("#saved-preview").addEventListener("close", () => { previewDocument = null; });

async function ensureGuides() {
  if (!guideCatalog.length) guideCatalog = (await api("/api/guides")).guides;
}

function guideSourceTitle(url) {
  const titles = {
    "seedance-2-0-prompt-guide": "Seedance · 프롬프트 가이드",
    "video-generation-tutorial": "Seedance · 영상 생성 안내",
    "video_gen_enhanced": "BytePlus · 영상 생성 문서",
    "MiniMax-H3": "MiniMax H3 · 공식 저장소",
    "VIDEO_PROMPT_WRITING_GUIDE_base_en.md": "MiniMax H3 · 텍스트 프롬프트 가이드",
    "VIDEO_PROMPT_WRITING_GUIDE_ref_en.md": "MiniMax H3 · 이미지 참조 가이드",
    "SKILL.md": "MiniMax H3 · 애니메이션 제작 스킬",
    "shot-table-spec.md": "MiniMax H3 · 샷 구성 규격",
    "storyboard-guidelines.md": "MiniMax H3 · 스토리보드 연출 지침",
    "model-selection.md": "MiniMax H3 · 모델 선택 안내",
    "qc-checklist.md": "MiniMax H3 · 품질 검수 목록",
  };
  const source = new URL(url);
  const filename = source.pathname.split("/").filter(Boolean).pop();
  return tr(titles[filename] || `${source.hostname} · ${filename}`);
}

function applyGuide(reset = true) {
  const family = $("#video-family").value;
  const custom = family === "custom";
  $("#clip-limit").min = custom ? "1" : "4";
  $("#clip-limit").step = custom ? "0.1" : "1";
  $("#custom-guide-fields").hidden = !custom;
  $("#official-guide-preview").hidden = custom;
  $("#reference-panel").hidden = custom || $("#video-guide").value === "text";
  $("#video-guide").closest("label").hidden = custom;
  for (const selector of ["#target-model", "#guide-source", "#conversion-guide"]) $(selector).readOnly = !custom;
  if (custom) {
    $("#official-guide-status").textContent = tr("직접 입력 가이드는 공식 규칙의 자동 검사를 제공하지 않습니다.");
    if (reset) for (const selector of ["#target-model", "#guide-source", "#conversion-guide"]) $(selector).value = "";
  } else {
    const id = `${family === "minimax" ? "minimax-h3" : "seedance-2"}-${$("#video-guide").value}`;
    const guide = guideCatalog.find((g) => g.id === id);
    if (!guide) return;
    $("#target-model").value = guide.target_model;
    $("#guide-source").value = guide.guide_source;
    $("#conversion-guide").value = guide.guide;
    $("#official-guide-body").textContent = guide.guide;
    $("#official-system-body").textContent = guide.system_prompt;
    $("#official-guide-status").textContent = tr("공식 자료 확인: {0} · 정수 4~15초 · 참조 이미지 최대 {1}장", {0: guide.checked_at, 1: guide.max_images});
    $("#official-guide-links").replaceChildren();
    for (const url of [...new Set(guide.guide_source.split("\n").map((value) => value.trim()).filter(Boolean))]) {
      const link = el("a", "guide-link", guideSourceTitle(url)); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
      const item = el("li"); item.append(link);
      $("#official-guide-links").append(item);
    }
  }
  if (reset) { invalidateConversion(); $("#conversion-consent").checked = false; }
  renderReferences();
}

function renderReferences() {
  const characters = $("#reference-characters"), backgrounds = $("#reference-background"), list = $("#reference-list");
  characters.replaceChildren(); backgrounds.replaceChildren(); list.replaceChildren();
  if (!conversionBoard) return;
  for (const character of [...conversionBoard.brief.characters, {id: "", name: tr("배경")}]) {
    const background = character.id === "";
    const label = el("label", "reference-upload", background ? tr("배경 이미지 추가") : tr("{0} · 이미지 추가", {0: character.name}));
    const input = el("input"); input.type = "file"; input.accept = "image/png,image/jpeg,image/webp"; input.multiple = true;
    input.addEventListener("change", () => libraryAction(async () => {
      const files = [...input.files];
      if (referenceItems.length + files.length > 9) throw new Error(tr("캐릭터와 배경 참조 이미지는 합쳐서 9장 이내로 선택해주세요."));
      for (const file of files) {
        if (file.size > 5000000) throw new Error(tr("이미지 형식과 5MB 이하 크기를 확인해주세요."));
      }
      for (const file of files) {
        const data = await new Promise((resolve, reject) => {
          const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error(tr("이미지를 읽을 수 없습니다."))); reader.readAsDataURL(file);
        });
        const uploaded = await api("/api/references/upload", {id: conversionBoardId, character_id: character.id, kind: background ? "background" : "character", name: file.name, data});
        referenceItems.push(uploaded.asset);
        // Save after each upload so a subsequent failure cannot lose successful additions.
        await api("/api/references/save", {id: conversionBoardId, references: referenceItems});
      }
      renderReferences(); invalidateConversion(); $("#conversion-consent").checked = false;
    }));
    label.append(input); (background ? backgrounds : characters).append(label);
  }
  referenceItems.forEach((item, index) => {
    const card = el("article", "reference-card");
    const img = el("img"); img.src = `/api/references/image/${item.id}`; img.alt = item.name; img.loading = "lazy";
    const controls = el("div", "reference-controls");
    const background = item.role === "environment";
    const name = background ? tr("배경") : conversionBoard.brief.characters.find((c) => c.id === item.character_id)?.name || item.character_id;
    const tag = $("#video-family").value === "minimax" ? `<Picture ${index + 1}>` : `Image ${index + 1}`;
    controls.append(el("strong", "", `${tag} · ${name}`), el("p", "helper", item.name));
    const roleLabel = el("label", "", tr("참조 용도")), role = el("select");
    for (const [value, label] of Object.entries(referenceRoles).filter(([value]) => background ? value === "environment" : value !== "environment")) { const option = el("option", "", tr(label)); option.value = value; role.append(option); }
    role.value = item.role;
    const noteLabel = el("label", "", tr("참조할 특징 설명")), note = el("textarea"); note.rows = 2; note.maxLength = 1000; note.value = item.note;
    const changed = () => { invalidateConversion(); $("#conversion-consent").checked = false; };
    role.addEventListener("change", () => { item.role = role.value; changed(); });
    note.addEventListener("input", () => { item.note = note.value; changed(); });
    roleLabel.append(role); noteLabel.append(note); controls.append(roleLabel, noteLabel);
    const buttons = el("div", "header-actions");
    for (const [label, delta] of [["앞으로", -1], ["뒤로", 1], ["목록에서 제외", 0]]) {
      const button = el("button", "quiet", tr(label));
      button.disabled = (delta === -1 && index === 0) || (delta === 1 && index === referenceItems.length - 1);
      button.addEventListener("click", () => {
        if (busy) return;
        if (!delta) referenceItems.splice(index, 1);
        else if (index + delta >= 0 && index + delta < referenceItems.length) [referenceItems[index], referenceItems[index + delta]] = [referenceItems[index + delta], referenceItems[index]];
        changed(); renderReferences();
      }); buttons.append(button);
    }
    controls.append(buttons); card.append(img, controls); list.append(card);
  });
}
for (const id of ["video-family", "video-guide"]) $(`#${id}`).addEventListener("change", () => applyGuide());
$("#references-save").addEventListener("click", () => libraryAction(async () => {
  await api("/api/references/save", {id: conversionBoardId, references: referenceItems});
  notice(tr("참조 설정을 저장했습니다."));
}));

// This capture runs before any imported/generated data is rendered. Values are never captured.
I18n.capture();
I18n.apply();
