"use strict";

let diagnosticEntries = [];
let diagnosticTimer = null;
let diagnosticLoading = false;
const diagnosticHints = {
  length: "출력 한도나 컨텍스트 한계로 중단됐습니다. 토큰 사용량과 모델의 컨텍스트 설정을 확인하세요.",
  tool_call: "모델이 텍스트 JSON 대신 도구 호출로 종료했습니다. 모델과 출력 방식을 확인하세요.",
  refused: "모델이 응답을 거절하거나 필터링했습니다.",
  missing_finish: "서버가 정상 종료 사유를 보내지 않았습니다. 모델과 서버 버전을 확인하세요.",
  incomplete: "서버가 응답 완료를 확인하지 않았습니다.",
  http_error: "AI 서버가 HTTP 오류를 반환했습니다. 상태 코드와 서버 로그를 확인하세요.",
  connection_error: "AI 서버와의 연결에 실패하거나 연결이 끊겼습니다.",
  timeout: "AI 응답 대기 시간이 초과됐습니다. 로컬 주소의 앱 시간 제한은 없습니다.",
  invalid_json: "응답이 올바른 JSON이 아닙니다. 모델과 JSON 출력 방식을 확인하세요.",
  invalid_response: "AI 서버의 응답 형식이 올바르지 않습니다.",
  response_too_large: "응답이 앱의 수신 크기 한도를 초과했습니다.",
  stream_interrupted: "스트리밍이 정상 종료되기 전에 끊겼습니다.",
  stream_error: "스트리밍 서버가 오류를 반환했습니다.",
  empty_output: "사용할 수 있는 응답 본문이 없습니다. 추론 토큰과 모델의 출력을 확인하세요.",
  schema_error: "응답 JSON이 요구 양식과 다릅니다. 모델과 JSON 출력 방식을 확인하세요.",
  configuration_error: "API 설정이나 모델 ID를 확인하세요.",
  provider_error: "AI 요청을 완료하지 못했습니다. 서버 로그를 함께 확인하세요.",
  unexpected_error: "요청 처리 중 예기치 않은 오류가 발생했습니다.",
};
const diagnosticState = {running: "응답 대기 중", success: "요청 성공", error: "요청 실패"};
const diagnosticOperation = {generate: "콘티 제작", review: "AI 검수", conversion: "프롬프트 변환", ai: "AI 요청"};
const diagnosticValue = (value) => value === undefined || value === null ? tr("제공 안 됨") : String(value);

function renderDiagnostics() {
  const list = $("#diagnostics-list"); list.replaceChildren();
  if (!diagnosticEntries.length) {
    list.append(el("p", "helper diagnostics-empty", tr("아직 AI 요청 기록이 없습니다. 예시 모드는 AI를 호출하지 않습니다.")));
    return;
  }
  for (const entry of diagnosticEntries) {
    const card = el("article", `diagnostic-entry diagnostic-${entry.status}`);
    const header = el("div", "diagnostic-heading");
    header.append(el("strong", "", tr(diagnosticState[entry.status] || "AI 요청")),
      el("span", "", `${entry.provider} · ${entry.model || "—"}`),
      el("span", "", tr("{0}초", {0: (entry.elapsed_ms / 1000).toFixed(1)})));
    card.append(header, el("p", "helper", `${new Date(entry.started_at).toLocaleString(I18n.locale)} · ${tr(diagnosticOperation[entry.operation] || "AI 요청")} · ${entry.id}`));
    const metrics = el("dl", "diagnostic-metrics");
    const fields = [["종료 사유", entry.finish_reason], ["입력 토큰", entry.input_tokens], ["출력 토큰", entry.output_tokens],
      ["추론 토큰", entry.reasoning_tokens], ["요청 출력 한도", entry.output_limit], ["HTTP 상태", entry.http_status],
      ["응답 대기 제한", entry.local === undefined ? undefined : entry.timeout_seconds === null ? tr("없음 · 로컬 요청") : tr("{0}초", {0: entry.timeout_seconds})]];
    for (const [label, value] of fields) metrics.append(el("dt", "", tr(label)), el("dd", "", diagnosticValue(value)));
    card.append(metrics);
    if (diagnosticHints[entry.outcome]) card.append(el("p", "diagnostic-hint", tr(diagnosticHints[entry.outcome])));
    if (entry.outcome === "length" && entry.output_tokens > 0 && entry.reasoning_tokens >= entry.output_tokens * .9 && entry.reasoning_tokens <= entry.output_tokens) {
      card.append(el("p", "diagnostic-hint", tr("출력 토큰 대부분이 추론에 사용됐습니다. 컨텍스트를 늘리기 전에 모델의 추론 모드나 추론 예산을 확인하세요.")));
    }
    list.append(card);
  }
}

async function refreshDiagnostics() {
  if (diagnosticLoading) return;
  diagnosticLoading = true;
  try {
    diagnosticEntries = (await api("/api/diagnostics")).entries;
    renderDiagnostics();
  } catch (error) { $("#diagnostics-status").textContent = error.message; }
  finally { diagnosticLoading = false; }
}

async function openDiagnostics() {
  if (!$("#diagnostics-dialog").open) $("#diagnostics-dialog").showModal();
  $("#diagnostics-status").textContent = "";
  await refreshDiagnostics();
  if (!diagnosticTimer && $("#diagnostics-dialog").open) diagnosticTimer = setInterval(refreshDiagnostics, 2000);
}

function diagnosticReport() {
  const lines = ["AI REQUEST DIAGNOSTICS", "Session metadata only. No request/response bodies, API keys or endpoint URLs.", ""];
  for (const entry of diagnosticEntries) {
    lines.push(`[${entry.id}]`);
    for (const [key, value] of Object.entries(entry)) if (key !== "id") lines.push(`${key}: ${JSON.stringify(value)}`);
    lines.push("");
  }
  return lines.join("\r\n");
}

$("#diagnostics-open").addEventListener("click", openDiagnostics);
$("#diagnostics-error-open").addEventListener("click", openDiagnostics);
$("#diagnostics-close").addEventListener("click", () => $("#diagnostics-dialog").close());
$("#diagnostics-dialog").addEventListener("close", () => { clearInterval(diagnosticTimer); diagnosticTimer = null; });
$("#diagnostics-refresh").addEventListener("click", refreshDiagnostics);
$("#diagnostics-copy").addEventListener("click", async () => {
  try {
    await refreshDiagnostics(); await navigator.clipboard.writeText(diagnosticReport());
    $("#diagnostics-status").textContent = tr("진단 로그를 복사했습니다.");
  } catch { $("#diagnostics-status").textContent = tr("클립보드에 복사할 수 없습니다. 로그 TXT 저장을 사용하세요."); }
});
$("#diagnostics-download").addEventListener("click", async () => { await refreshDiagnostics(); download(diagnosticReport(), "ai-diagnostics.txt", "text/plain;charset=utf-8"); });
$("#diagnostics-clear").addEventListener("click", async () => {
  try {
    diagnosticEntries = (await api("/api/diagnostics/clear", {})).entries; renderDiagnostics();
    $("#diagnostics-status").textContent = tr("완료된 로그를 지웠습니다. 진행 중인 요청은 유지됩니다.");
  } catch (error) { $("#diagnostics-status").textContent = error.message; }
});
window.addEventListener("languagechange", renderDiagnostics);
