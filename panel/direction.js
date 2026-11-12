"use strict";

// ComfyUI presentation only. Combines the two story direction fields and adds
// optional per-shot instructions without changing the pinned Studio snapshot.
(() => {
  const panel = document.getElementById("direction-panel");
  const briefForm = document.getElementById("brief-form");
  if (!panel || !briefForm) return;
  const intentInput = briefForm.elements.namedItem("intent");
  const endingInput = briefForm.elements.namedItem("ending");
  const shotCountInput = briefForm.elements.namedItem("shot_count");
  const titleInput = briefForm.elements.namedItem("title");
  const styleInput = briefForm.elements.namedItem("style");
  const intentLabel = intentInput?.closest("label");
  const endingLabel = endingInput?.closest("label");
  const styleLabel = styleInput?.closest("label");
  if (!intentInput || !endingInput || !shotCountInput || !intentLabel || !endingLabel) return;

  const copy = {
    direction: ["이야기 전개와 결말", "Story development and ending", "物語の展開と結末"],
    directionHelp: [
      "전개와 도달할 결말을 한 번에 적어주세요. 마지막 줄은 원하는 결말로도 전달됩니다.",
      "Describe the development and the ending together. The last line is also sent as the desired ending.",
      "展開と結末をまとめて書いてください。最後の行は希望する結末としても送信されます。"
    ],
    directionPlaceholder: [
      "인물 사이에 어떤 일이 일어나고, 장면이 끝났을 때 무엇이 달라져 있나요?",
      "What happens between the characters, and what has changed when the scene ends?",
      "人物の間で何が起こり、場面が終わったとき何が変わっているでしょうか？"
    ],
    advanced: ["컷별 연출 지시 · 고급", "Per-shot direction · advanced", "カット別演出指示・詳細"],
    advancedHelp: [
      "원하는 컷만 채우면 됩니다. 비워둔 컷은 AI가 자동으로 구성합니다. 이 지시는 다음 생성과 재생성에 반영됩니다. 인물이 많을 때 일부 컷에서 화면 밖 인물 상태가 빠지면 이전 컷 기준으로 자동 보완되며, 실제 등장은 화면·행동 설명을 따릅니다.",
      "Fill only the shots you want to control. Empty shots are composed by the AI. These notes apply to the next generation or regeneration. If off-screen character states are missing with a large cast, they are completed from the previous shot; on-screen appearance still follows the visual and actions.",
      "指示したいカットだけ入力してください。空のカットはAIが構成します。この指示は次の生成・再生成に反映されます。人物が多いとき画面外の人物状態が欠けても前のカットを基準に補完され、実際の登場は画面・行動の説明に従います。"
    ],
    shotPlaceholder: [
      "이 컷에서 원하는 내용",
      "What should happen in this shot",
      "このカットで望む内容"
    ],
    clear: ["작성한 컷 지시 지우기", "Clear shot directions", "カット指示を消去"],
    status: [
      "{n}개 컷 지시 작성됨 · 전체 {total}컷",
      "{n} of {total} shots directed",
      "{n}/{total}カット指示済み"
    ],
    emptyDirection: ["이야기 전개와 결말 항목을 입력해주세요.", "Enter the story development and ending.", "物語の展開と結末を入力してください。"]
  };
  const pick = (key) => copy[key][I18n.language === "ko" ? 0 : I18n.language === "ja" ? 2 : 1];

  intentLabel.hidden = true;
  endingLabel.hidden = true;

  const field = document.createElement("label");
  field.className = "sg-direction-field";
  const caption = document.createElement("span");
  caption.className = "sg-field-caption";
  const direction = document.createElement("textarea");
  direction.id = "sg-story-direction";
  direction.rows = 7;
  field.append(caption, direction);
  intentLabel.before(field);

  const directionHelp = document.createElement("p");
  directionHelp.className = "helper sg-direction-help";
  field.after(directionHelp);

  const box = document.createElement("details");
  box.className = "sg-shot-notes-box";
  const summary = document.createElement("summary");
  const help = document.createElement("p");
  help.className = "helper";
  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "quiet sg-shot-notes-clear";
  const status = document.createElement("p");
  status.className = "helper sg-shot-notes-status";
  status.setAttribute("role", "status");
  const list = document.createElement("div");
  list.className = "sg-shot-notes-list";
  box.append(summary, help, clear, status, list);
  (styleLabel || panel.lastElementChild || panel).after(box);

  const STORAGE_PREFIX = "comfyui-storyboard.shot-notes:";
  let notes = [];
  let notesTitle = String(titleInput?.value || "").trim();
  let saveTimer = 0;

  function readNotes(title) {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_PREFIX + title) || "[]");
      return Array.isArray(saved) ? saved.filter((value) => typeof value === "string").slice(0, 60) : [];
    } catch { return []; }
  }

  function saveNotes() {
    if (!notesTitle) return;
    clearTimeout(saveTimer);
    try { localStorage.setItem(STORAGE_PREFIX + notesTitle, JSON.stringify(notes)); } catch { /* Optional draft persistence. */ }
  }

  notes = readNotes(notesTitle);

  function targetCount() {
    const value = Number(shotCountInput.value);
    if (Number.isInteger(value) && value >= 3 && value <= 60) return value;
    return Math.max(3, Math.min(60, notes.length || 6));
  }

  function ensureLength(count) {
    while (notes.length < count) notes.push("");
  }

  function statusText() {
    const count = targetCount();
    const filled = notes.slice(0, count).filter((value) => value.trim()).length;
    return pick("status").replace("{n}", String(filled)).replace("{total}", String(count));
  }

  function updateStatus() {
    status.textContent = statusText();
  }

  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      if (!notesTitle) return;
      try { localStorage.setItem(STORAGE_PREFIX + notesTitle, JSON.stringify(notes)); } catch { /* Optional draft persistence. */ }
    }, 200);
  }

  function renderNotes() {
    const count = targetCount();
    ensureLength(count);
    list.replaceChildren();
    for (let index = 0; index < count; index++) {
      const row = document.createElement("label");
      row.className = "sg-shot-note";
      const badge = document.createElement("span");
      badge.className = "sg-shot-note-id";
      badge.textContent = `S${String(index + 1).padStart(2, "0")}`;
      const area = document.createElement("textarea");
      area.rows = 2;
      area.value = notes[index];
      area.placeholder = pick("shotPlaceholder");
      area.setAttribute("aria-label", `${badge.textContent} ${pick("shotPlaceholder")}`);
      area.addEventListener("input", () => { notes[index] = area.value; updateStatus(); scheduleSave(); });
      row.append(badge, area);
      list.append(row);
    }
    updateStatus();
  }

  function composeNotes() {
    const count = targetCount();
    ensureLength(count);
    return notes.slice(0, count).map((note, index) => note.trim()
      ? `S${String(index + 1).padStart(2, "0")}: ${note.trim()}` : "").filter(Boolean).join("\n");
  }

  function endingFrom(value) {
    const lines = String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    return lines.length ? lines[lines.length - 1] : "";
  }

  function directionFrom(brief) {
    const intent = String(brief?.intent || "").trim();
    const ending = String(brief?.ending || "").trim();
    if (!intent) return ending;
    if (!ending || ending === intent || intent.includes(ending)) return intent;
    return `${intent}\n${ending}`;
  }

  function syncHidden() {
    intentInput.value = direction.value;
    endingInput.value = endingFrom(direction.value);
  }

  function applyCopy() {
    caption.textContent = pick("direction");
    direction.placeholder = pick("directionPlaceholder");
    directionHelp.textContent = pick("directionHelp");
    summary.textContent = pick("advanced");
    help.textContent = pick("advancedHelp");
    clear.textContent = pick("clear");
    renderNotes();
  }

  const BLOCK_HEADER = "[컷별 연출 지시]";
  function combine(revision, shotNotes) {
    if (!shotNotes) return revision;
    const block = `${BLOCK_HEADER}\n${shotNotes}\n각 컷 지시를 해당 컷의 화면·행동·대사에 우선 반영하고, 모든 컷의 시작·종료 상태에는 화면에 보이지 않는 캐릭터도 포함하세요.`;
    if (revision.includes(BLOCK_HEADER)) return revision;
    return revision.trim() ? `${revision.trim()}\n\n${block}` : block;
  }

  const previousApi = api;
  api = async function(path, body) {
    if (typeof path === "string" && path.endsWith("/api/generate") && body && typeof body === "object") {
      const title = String(titleInput?.value || "").trim();
      if (title) notesTitle = title;
      saveNotes();
      const shotNotes = composeNotes();
      if (shotNotes) body = {...body, revision: combine(String(body.revision || ""), shotNotes)};
    }
    return previousApi(path, body);
  };

  const previousFillBrief = fillBrief;
  fillBrief = function(brief) {
    const result = previousFillBrief(brief);
    direction.value = directionFrom(brief);
    notesTitle = String(brief?.title || "").trim();
    notes = readNotes(notesTitle);
    renderNotes();
    return result;
  };

  const previousValidate = validateBriefInputs;
  validateBriefInputs = function() {
    if (!direction.value.trim()) {
      activateTab("direction");
      direction.focus();
      direction.scrollIntoView({block: "center"});
      throw new Error(pick("emptyDirection"));
    }
    syncHidden();
    return previousValidate();
  };

  direction.addEventListener("input", () => { syncHidden(); dirty = true; });
  shotCountInput.addEventListener("input", () => {
    const value = Number(shotCountInput.value);
    if (Number.isInteger(value) && value >= 3 && value <= 60) renderNotes();
  });
  shotCountInput.addEventListener("change", renderNotes);
  titleInput?.addEventListener("change", () => {
    const title = String(titleInput.value || "").trim();
    if (title === notesTitle) return;
    saveNotes();
    notesTitle = title;
    saveNotes();
  });
  clear.addEventListener("click", () => { notes = []; scheduleSave(); renderNotes(); });
  window.addEventListener("languagechange", applyCopy);

  try { direction.value = directionFrom(readBrief()); } catch { /* The empty draft has no characters yet. */ }
  applyCopy();
})();