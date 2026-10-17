"use strict";

window.I18n = (() => {
  const messages = window.UI_MESSAGES;
  const languages = ["ko", "en", "ja"];
  const storageKey = "persona-storyboard.ui-language";
  let language = "en";
  try {
    const stored = localStorage.getItem(storageKey);
    if (languages.includes(stored)) language = stored;
  } catch { /* Language switching also works when browser storage is blocked. */ }
  const bindings = [];
  const tracked = new WeakSet();
  const korean = window.UI_KOREAN || {};
  const valueFor = (key, lang) => lang === "ko" ? korean[key] ?? key : messages[key]?.[lang === "en" ? 0 : 1] ?? key;
  const format = (value, params = {}) => value.replace(/\{(\d+)\}/g, (match, key) => Object.hasOwn(params, key) ? String(params[key]) : match);
  const text = (key, params) => format(valueFor(key, language), params);
  const escape = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const patterns = [];
  for (const key of Object.keys(messages)) {
    for (const source of new Set([key, ...languages.map((lang) => valueFor(key, lang))])) {
      const indexes = [];
      const parts = source.split(/(\{\d+\})/).map((part) => {
        if (/^\{\d+\}$/.test(part)) { indexes.push(part.slice(1, -1)); return "([\\s\\S]*?)"; }
        return escape(part);
      });
      if (indexes.length) patterns.push({key, indexes, regex: new RegExp(`^${parts.join("")}$`)});
    }
  }
  // Specific messages first; an opaque parameter is never itself translated.
  patterns.sort((a, b) => b.key.replace(/\{\d+\}/g, "").length - a.key.replace(/\{\d+\}/g, "").length);
  function canonical(value) {
    if (Object.hasOwn(messages, value)) return value;
    return Object.keys(messages).find((key) => messages[key].includes(value) || korean[key] === value) ?? value;
  }
  function system(value) {
    if (typeof value !== "string") return String(value ?? "");
    const key = canonical(value);
    if (Object.hasOwn(messages, key)) return text(key);
    for (const pattern of patterns) {
      const match = pattern.regex.exec(value);
      if (!match) continue;
      const params = Object.fromEntries(pattern.indexes.map((index, i) => [index, match[i + 1]]));
      if (pattern.key === "{0} 항목을 입력해주세요." || pattern.key === "이전 컷의 종료 상태와 {0} 시작 상태가 다릅니다. 전환 의도를 확인해주세요.") {
        params[0] = text(canonical(params[0]));
      }
      return text(pattern.key, params);
    }
    return value;
  }
  function capture(root = document.body) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        return node.parentElement?.closest('script, style, textarea, input, svg, [data-language], [translate="no"]') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (tracked.has(node) || !node.nodeValue.trim()) continue;
      const source = canonical(node.nodeValue.trim());
      if (!Object.hasOwn(messages, source)) continue;
      bindings.push({node, source, prefix: node.nodeValue.match(/^\s*/)[0], suffix: node.nodeValue.match(/\s*$/)[0]});
      tracked.add(node);
    }
    for (const node of root.querySelectorAll("[placeholder], [aria-label], [title]")) {
      if (node.closest('[translate="no"]')) continue;
      if (tracked.has(node)) continue;
      for (const attr of ["placeholder", "aria-label", "title"]) {
        const source = canonical(node.getAttribute(attr));
        if (Object.hasOwn(messages, source)) bindings.push({node, source, attr});
      }
      tracked.add(node);
    }
  }
  function bindText(node, source) {
    if (!node || tracked.has(node)) return;
    bindings.push({node, source, prefix: "", suffix: ""});
    tracked.add(node);
  }
  function apply() {
    document.documentElement.lang = language;
    for (const binding of bindings) {
      if (!binding.node.isConnected) continue;
      if (binding.attr) binding.node.setAttribute(binding.attr, text(binding.source));
      else binding.node.nodeValue = binding.prefix + text(binding.source) + binding.suffix;
    }
    for (const button of document.querySelectorAll("[data-language]")) {
      button.setAttribute("aria-pressed", String(button.dataset.language === language));
    }
  }
  function select(value) {
    if (!languages.includes(value)) return;
    language = value;
    try { localStorage.setItem(storageKey, value); } catch { /* Optional persistence. */ }
    apply();
    window.dispatchEvent(new Event("languagechange"));
  }
  capture();
  return {text, system, capture, bindText, apply, select, get language() { return language; }, get locale() { return {ko: "ko-KR", en: "en-US", ja: "ja-JP"}[language]; }};
})();
const tr = window.I18n.text;
