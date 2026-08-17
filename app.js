/* FOCUS Release Notes Generator — app logic */

const TEMPLATE_URL = "assets/master_template.docx";

const SITES = ["Core", "Partner Portal", "Customer Portal"];
const SITE_LABELS = {
  "Core": "Odessa Core",
  "Partner Portal": "Partner Portal",
  "Customer Portal": "Customer Portal",
};

const RRP_PACKAGES = [
  { key: "LESSOR_PORTAL", label: "Lessor Portal" },
  { key: "WINDOWS_SERVICE", label: "Windows Service" },
  { key: "WEB_API", label: "Web API" },
  { key: "DATABASE", label: "Database" },
  { key: "REPORTS", label: "Reports" },
  { key: "APPSETTINGS_CONFIG", label: "App Settings Config" },
];

const SECTION_CONFIG = {
  bizconfig: { rowFields: ["key", "summary", "type"], mapTo: { key: "ROW_KEY", summary: "ROW_SUMMARY", type: "ROW_TYPE" } },
  req:       { rowFields: ["key", "summary", "priority", "datafix"], mapTo: { key: "ROW_KEY", summary: "ROW_SUMMARY", priority: "ROW_PRIORITY", datafix: "ROW_DATAFIX" } },
  tasks:     { rowFields: ["key", "summary", "priority", "datafix"], mapTo: { key: "ROW_KEY", summary: "ROW_SUMMARY", priority: "ROW_PRIORITY", datafix: "ROW_DATAFIX" } },
  cdd:       { rowFields: ["key", "summary", "priority", "datafix"], mapTo: { key: "ROW_KEY", summary: "ROW_SUMMARY", priority: "ROW_PRIORITY", datafix: "ROW_DATAFIX" } },
};

const SECTION_LABELS = {
  bizconfig: "Business Configuration",
  req: "Requirements",
  tasks: "Tasks Completed",
  cdd: "Code Drop Defects",
};

const TICKET_PASTE_TEMPLATE = [
  "Issue Key\tSummary\tPriority\tRelease Notes Section\tType\tDatafix\tApplies To (Core/PP/CP)",
  "TIC04-166\tPhase2 | M2.1 | RBS changes\tMedium\tBusiness Configuration\tRBS\t\tCore",
  "TIC04-35\tContract Booking | Additional Details in Lease Assets\tMedium\tRequirements\t\tYes\tCore",
  "TIC04-145\tData Fix for TIC04-35\tMedium\tTasks Completed\t\tYes\tCore",
  "TIC03-2215\tMalformed Statement Invoice file for Billtrust\tHighest\tCode Drop Defects\t\tYes\tCore, PP",
].join("\n");

let uploadedTemplateBuffer = null;

// ---------- Storage abstraction (safe autosave; degrades to in-memory if localStorage is unavailable) ----------

const Store = (function () {
  let memory = {};
  let useLocal = true;
  try {
    const testKey = "__frng_test__";
    window.localStorage.setItem(testKey, "1");
    window.localStorage.removeItem(testKey);
  } catch (e) {
    useLocal = false;
  }
  return {
    get(key) {
      if (useLocal) { try { return window.localStorage.getItem(key); } catch (e) { /* fall through */ } }
      return memory[key] || null;
    },
    set(key, value) {
      if (useLocal) { try { window.localStorage.setItem(key, value); return; } catch (e) { /* fall through */ } }
      memory[key] = value;
    },
    remove(key) {
      if (useLocal) { try { window.localStorage.removeItem(key); return; } catch (e) { /* fall through */ } }
      delete memory[key];
    },
  };
})();

const AUTOSAVE_KEY = "frng_autosave_v1";
const CUSTOM_TEMPLATE_KEY = "frng_custom_template_v1";
const CUSTOM_TEMPLATE_NAME_KEY = "frng_custom_template_name_v1";

// ---------- Auto-fill visual marking ----------

function markAutoFilled(fieldWrapperEl, inputEl) {
  if (!fieldWrapperEl || !inputEl) return;
  fieldWrapperEl.classList.add("auto-filled");
  const clear = () => { fieldWrapperEl.classList.remove("auto-filled"); inputEl.removeEventListener("input", clear); inputEl.removeEventListener("change", clear); };
  inputEl.addEventListener("input", clear);
  inputEl.addEventListener("change", clear);
}

// ---------- UI bootstrap ----------

document.addEventListener("DOMContentLoaded", () => {
  buildSiteDetailCards();
  Object.keys(SECTION_CONFIG).forEach(refreshSiteTagsForSection);
  updateSiteDetailVisibility();
  loadRememberedTemplateIfAny();

  document.querySelectorAll("[data-add]").forEach(btn => {
    btn.addEventListener("click", () => addRow(btn.dataset.add));
  });

  document.querySelectorAll('input[name="site"]').forEach(cb => {
    cb.addEventListener("change", () => {
      Object.keys(SECTION_CONFIG).forEach(refreshSiteTagsForSection);
      updateSiteDetailVisibility();
    });
  });

  document.getElementById("uploadTemplateBtn").addEventListener("click", () => {
    document.getElementById("templateFile").click();
  });
  document.getElementById("templateFile").addEventListener("change", onTemplateFileSelected);

  document.getElementById("parseBtn").addEventListener("click", onParseTickets);
  document.getElementById("copyTicketTemplateBtn").addEventListener("click", async () => {
    const statusEl = document.getElementById("copyTicketTemplateStatus");
    try {
      await navigator.clipboard.writeText(TICKET_PASTE_TEMPLATE);
      statusEl.className = "status-msg ok";
      statusEl.textContent = "Copied! Paste into a blank Excel sheet, fill it in, then copy your rows back here.";
    } catch (e) {
      statusEl.className = "status-msg error";
      statusEl.textContent = "Couldn't copy — your browser may be blocking clipboard access.";
    }
  });
  document.getElementById("screenshotBtn").addEventListener("click", () => {
    document.getElementById("screenshotFile").click();
  });
  document.getElementById("screenshotFile").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) runOcrIntoTextarea(file, document.getElementById("pasteArea"), document.getElementById("pasteStatus"));
  });
  document.getElementById("pasteArea").addEventListener("paste", (e) => {
    const items = e.clipboardData && e.clipboardData.items;
    if (!items) return;
    // Excel (and most spreadsheet apps) put BOTH a tab-separated text
    // representation AND a bitmap image of the selection on the clipboard.
    // Always prefer the text — it's exact, unlike OCR. Only fall back to
    // OCR when there is truly no text representation (a real screenshot).
    const hasText = Array.from(items).some(item => item.type === "text/plain" || item.type === "text/html");
    if (hasText) return; // let the browser perform the normal text paste
    for (const item of items) {
      if (item.type && item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          runOcrIntoTextarea(file, document.getElementById("pasteArea"), document.getElementById("pasteStatus"));
        }
        break;
      }
    }
  });

  document.getElementById("generateBtn").addEventListener("click", onGenerate);
  document.getElementById("downloadAllBtn").addEventListener("click", onDownloadAll);

  // Draft save/load/reset
  document.getElementById("saveDraftBtn").addEventListener("click", onSaveDraft);
  document.getElementById("loadDraftBtn").addEventListener("click", () => document.getElementById("loadDraftFile").click());
  document.getElementById("loadDraftFile").addEventListener("change", onLoadDraftFile);
  document.getElementById("resetBtn").addEventListener("click", onResetAll);
  document.getElementById("clearTicketsBtn").addEventListener("click", onClearAllTickets);

  // Live summary + validation + autosave on any change within the form
  const content = document.querySelector(".content");
  content.addEventListener("input", scheduleFormChangeHandlers);
  content.addEventListener("change", scheduleFormChangeHandlers);
  content.addEventListener("click", scheduleFormChangeHandlers);

  // Offer to restore an autosaved draft, if one exists
  const saved = Store.get(AUTOSAVE_KEY);
  if (saved) showRestoreBanner(saved);

  renderSummary();
  validateForm();
});

let formChangeTimer = null;
function scheduleFormChangeHandlers() {
  clearTimeout(formChangeTimer);
  formChangeTimer = setTimeout(() => {
    renderSummary();
    validateForm();
    autosaveDraft();
  }, 200);
}

function autosaveDraft() {
  try {
    Store.set(AUTOSAVE_KEY, JSON.stringify(serializeFormState()));
  } catch (e) { /* non-fatal */ }
}

function showRestoreBanner(savedJson) {
  const banner = document.getElementById("draftBanner");
  banner.classList.remove("hidden");
  banner.querySelector("[data-restore]").onclick = () => {
    try {
      restoreFormState(JSON.parse(savedJson));
      banner.classList.add("hidden");
    } catch (e) {
      alert("Couldn't restore that draft.");
    }
  };
  banner.querySelector("[data-discard]").onclick = () => {
    Store.remove(AUTOSAVE_KEY);
    banner.classList.add("hidden");
  };
}

function getSelectedSites() {
  return Array.from(document.querySelectorAll('input[name="site"]:checked')).map(cb => cb.value);
}

// ---------- Template selection (bundled default / session upload / remembered custom) ----------

function arrayBufferToBase64(buf) {
  let binary = "";
  const bytes = new Uint8Array(buf);
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

function base64ToArrayBuffer(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function setTemplateStatus(html) {
  document.getElementById("templateStatus").innerHTML = html;
}

function renderBundledTemplateStatus() {
  setTemplateStatus(`<span class="dot dot-ok"></span><span>Using bundled template</span>`);
  document.getElementById("forgetTemplateBtn").classList.add("hidden");
}

function renderCustomTemplateStatus(name, remembered) {
  const rememberedNote = remembered ? " (remembered in this browser)" : "";
  setTemplateStatus(`<span class="dot dot-ok"></span><span>Using: ${escapeHtml(name)}${rememberedNote}</span>`);
  document.getElementById("forgetTemplateBtn").classList.remove("hidden");
}

function loadRememberedTemplateIfAny() {
  document.getElementById("forgetTemplateBtn").addEventListener("click", () => {
    uploadedTemplateBuffer = null;
    Store.remove(CUSTOM_TEMPLATE_KEY);
    Store.remove(CUSTOM_TEMPLATE_NAME_KEY);
    renderBundledTemplateStatus();
  });

  const b64 = Store.get(CUSTOM_TEMPLATE_KEY);
  const name = Store.get(CUSTOM_TEMPLATE_NAME_KEY);
  if (b64) {
    try {
      uploadedTemplateBuffer = base64ToArrayBuffer(b64);
      renderCustomTemplateStatus(name || "custom template.docx", true);
      return;
    } catch (e) { /* fall through to bundled */ }
  }
  renderBundledTemplateStatus();
}

async function onTemplateFileSelected(e) {
  const file = e.target.files[0];
  if (!file) return;
  uploadedTemplateBuffer = await file.arrayBuffer();

  const remember = confirm(`Remember "${file.name}" as your default template in this browser?\n\nOK = remember it here (used automatically next time you open this app on this device).\nCancel = use it for this session only.`);
  if (remember) {
    try {
      Store.set(CUSTOM_TEMPLATE_KEY, arrayBufferToBase64(uploadedTemplateBuffer));
      Store.set(CUSTOM_TEMPLATE_NAME_KEY, file.name);
    } catch (err) {
      console.warn("Could not remember template (storage limit?)", err);
    }
  }
  renderCustomTemplateStatus(file.name, remember);
}

// ---------- Per-site release detail cards ----------

function siteSlug(site) { return site.replace(/\s+/g, "-"); }

function buildSiteDetailCards() {
  const container = document.getElementById("siteDetailCards");
  const tpl = document.getElementById("site-detail-tpl");
  container.innerHTML = "";
  SITES.forEach(site => {
    const node = tpl.content.cloneNode(true);
    const card = node.querySelector("[data-site-card]");
    card.dataset.site = site;
    card.querySelector("[data-site-title]").textContent = `${site} — Release Details`;

    const rrpGrid = card.querySelector("[data-rrp-grid]");
    RRP_PACKAGES.forEach(pkg => {
      const div = document.createElement("div");
      div.className = "rrp-toggle";
      div.innerHTML = `
        <span class="rrp-toggle-label">${pkg.label}</span>
        <label class="switch">
          <input type="checkbox" data-rrp="${pkg.key}">
          <span class="switch-slider"></span>
        </label>
      `;
      rrpGrid.appendChild(div);
    });

    card.querySelector('[data-field="releaseDate"]').addEventListener("change", (e) => {
      const value = e.target.value;
      if (!value) return;
      SITES.forEach(otherSite => {
        if (otherSite === site) return;
        const otherCard = document.querySelector(`[data-site-card][data-site="${otherSite}"]`);
        if (!otherCard) return;
        const otherInput = otherCard.querySelector('[data-field="releaseDate"]');
        if (otherInput && !otherInput.value) {
          otherInput.value = value;
          markAutoFilled(otherInput.closest(".field"), otherInput);
        }
      });
    });

    card.querySelector("[data-parse-details]").addEventListener("click", () => {
      const textarea = card.querySelector("[data-paste-details]");
      const statusEl = card.querySelector("[data-parse-status]");
      const parsed = parseReleaseParagraph(textarea.value);
      applyParsedReleaseDetails(card, parsed);
      const filled = Object.keys(parsed).filter(k => k !== "rrp").length + (parsed.rrp ? Object.keys(parsed.rrp).length : 0);
      statusEl.className = "status-msg ok";
      statusEl.textContent = filled > 0 ? `Filled ${filled} field(s) — please review.` : "Couldn't recognize any fields — fill in manually.";
    });

    card.querySelector("[data-generate-chat]").addEventListener("click", () => {
      const text = buildChatMessageText(site);
      card.querySelector("[data-chat-output-wrap]").classList.remove("hidden");
      card.querySelector("[data-chat-output]").value = text;
    });
    card.querySelector("[data-copy-chat]").addEventListener("click", async () => {
      const out = card.querySelector("[data-chat-output]");
      const statusEl = card.querySelector("[data-copy-status]");
      try {
        await navigator.clipboard.writeText(out.value);
      } catch (e) {
        out.removeAttribute("readonly");
        out.select();
        document.execCommand("copy");
        out.setAttribute("readonly", "readonly");
      }
      statusEl.className = "status-msg ok";
      statusEl.textContent = "Copied!";
    });

    container.appendChild(node);
  });
}

function buildChatMessageText(site) {
  const v = getSiteFormValues(site);
  const lines = [];
  lines.push(`Release Version : ${v.cdVersionRaw || "—"}`);
  lines.push(`Product Version : ${v.productVersion || "—"}`);
  lines.push(`Fx Version : ${v.fxVersion || "—"}`);
  lines.push(`Release date - ${v.releaseDateIso ? formatDateLong(v.releaseDateIso) : "—"}`);
  lines.push(`Hotfix - ${v.hotfix || "No"}`);
  lines.push(`Type - ${v.releaseType || "Full Release"}`);

  const yesPkgs = RRP_PACKAGES.filter(p => v.rrp[p.key] === "Yes").map(p => p.label);
  const noPkgs = RRP_PACKAGES.filter(p => v.rrp[p.key] !== "Yes").map(p => p.label);
  if (yesPkgs.length === 0) lines.push(`Packages - all No`);
  else if (noPkgs.length === 0) lines.push(`Packages - all Yes`);
  else lines.push(`Packages - ${yesPkgs.join(", ")} are yes, rest no`);

  lines.push("");

  const sections = {
    bizconfig: collectRows("bizconfig"),
    req: collectRows("req"),
    tasks: collectRows("tasks"),
    cdd: collectRows("cdd"),
  };
  Object.keys(SECTION_CONFIG).forEach(sec => {
    const rows = sections[sec].filter(r => r.sites.includes(site));
    lines.push(`${SECTION_LABELS[sec]}:`);
    if (rows.length === 0) {
      lines.push(sec === "bizconfig" ? "  No RBS Impact" : "  NA");
    } else {
      rows.forEach(r => {
        if (sec === "bizconfig") {
          lines.push(`  - ${r.data.key} : ${r.data.summary} (${r.data.type || "—"})`);
        } else {
          lines.push(`  - ${r.data.key} : ${r.data.summary} (${r.data.priority}, Datafix: ${r.data.datafix})`);
        }
      });
    }
    lines.push("");
  });

  return lines.join("\n").trim();
}

function applyParsedReleaseDetails(card, parsed) {
  const setAndMark = (fieldName, value) => {
    const input = card.querySelector(`[data-field="${fieldName}"]`);
    if (!input || value === undefined) return;
    input.value = value;
    markAutoFilled(input.closest(".field"), input);
  };
  setAndMark("cdVersion", parsed.cdVersion);
  setAndMark("productVersion", parsed.productVersion);
  setAndMark("fxVersion", parsed.fxVersion);
  setAndMark("releaseDate", parsed.releaseDate);
  setAndMark("releaseType", parsed.releaseType);
  setAndMark("hotfix", parsed.hotfix);
  if (parsed.rrp) {
    Object.keys(parsed.rrp).forEach(pkgKey => {
      const sel = card.querySelector(`[data-rrp="${pkgKey}"]`);
      if (sel) {
        sel.checked = parsed.rrp[pkgKey] === "Yes";
        markAutoFilled(sel.closest(".rrp-toggle"), sel);
      }
    });
  }
}

function updateSiteDetailVisibility() {
  const selected = new Set(getSelectedSites());
  document.querySelectorAll("[data-site-card]").forEach(card => {
    card.classList.toggle("hidden", !selected.has(card.dataset.site));
  });
}

function getSiteFormValues(site) {
  const card = document.querySelector(`[data-site-card][data-site="${site}"]`);
  const val = (f) => card.querySelector(`[data-field="${f}"]`).value.trim();
  const rrp = {};
  RRP_PACKAGES.forEach(pkg => {
    const sel = card.querySelector(`[data-rrp="${pkg.key}"]`);
    rrp[pkg.key] = sel && sel.checked ? "Yes" : "No";
  });
  return {
    cdVersionRaw: val("cdVersion"),
    productVersion: val("productVersion"),
    fxVersion: val("fxVersion"),
    releaseDateIso: val("releaseDate"),
    releaseType: val("releaseType"),
    hotfix: val("hotfix"),
    rrp,
  };
}

// ---------- Ticket rows (manual add + paste import) ----------

function addRow(sectionKey) {
  const tpl = document.getElementById(`row-tpl-${sectionKey}`);
  const container = document.getElementById(`${sectionKey}-rows`);
  const node = tpl.content.cloneNode(true);
  container.appendChild(node);
  const rowEl = container.lastElementChild;
  refreshSiteTagsForSection(sectionKey);
  wireMoveSelect(rowEl, sectionKey);
  return rowEl;
}

function wireMoveSelect(rowEl, sectionKey) {
  const moveSelect = rowEl.querySelector("[data-move]");
  if (!moveSelect) return;
  moveSelect.innerHTML = '<option value="">Move to…</option>';
  Object.keys(SECTION_CONFIG).filter(k => k !== sectionKey).forEach(k => {
    const opt = document.createElement("option");
    opt.value = k;
    opt.textContent = SECTION_LABELS[k];
    moveSelect.appendChild(opt);
  });
  moveSelect.addEventListener("change", () => {
    if (!moveSelect.value) return;
    moveTicketRow(rowEl, sectionKey, moveSelect.value);
  });
}

function moveTicketRow(rowEl, fromKey, toKey) {
  const fromCfg = SECTION_CONFIG[fromKey];
  const record = {};
  fromCfg.rowFields.forEach(f => {
    const input = rowEl.querySelector(`[data-field="${f}"]`);
    if (input) record[f] = input.value;
  });
  record.sites = Array.from(rowEl.querySelectorAll("[data-site-tags] input:checked")).map(i => i.value);
  rowEl.remove();
  addRowWithData(toKey, record, false);
  renderSummary();
  validateForm();
  autosaveDraft();
}

function refreshSiteTagsForSection(sectionKey) {
  const sites = getSelectedSites();
  const container = document.getElementById(`${sectionKey}-rows`);
  if (!container) return;
  container.querySelectorAll(".ticket-row").forEach(row => {
    const tagsDiv = row.querySelector("[data-site-tags]");
    const existing = {};
    tagsDiv.querySelectorAll("input").forEach(inp => { existing[inp.value] = inp.checked; });
    tagsDiv.innerHTML = "";
    sites.forEach(site => {
      const label = document.createElement("label");
      label.className = "site-tag";
      const checked = existing.hasOwnProperty(site) ? existing[site] : (sites.length === 1);
      label.innerHTML = `<input type="checkbox" value="${escapeHtml(site)}" ${checked ? "checked" : ""}><span>${escapeHtml(site)}</span>`;
      tagsDiv.appendChild(label);
    });
    row.querySelector(".row-remove").onclick = () => row.remove();
  });
}

function setRowSites(rowEl, sites) {
  const wanted = new Set(sites);
  rowEl.querySelectorAll("[data-site-tags] input").forEach(inp => {
    inp.checked = wanted.size === 0 ? inp.checked : wanted.has(inp.value);
  });
}

function addRowWithData(sectionKey, record, mark = true) {
  const rowEl = addRow(sectionKey);
  const cfg = SECTION_CONFIG[sectionKey];
  cfg.rowFields.forEach(f => {
    const input = rowEl.querySelector(`[data-field="${f}"]`);
    if (!input) return;
    let value = record[f] !== undefined ? record[f] : "";
    if (input.tagName === "SELECT") {
      const opt = Array.from(input.options).find(o => o.value.toLowerCase() === String(value).toLowerCase());
      if (opt) input.value = opt.value;
    } else {
      input.value = value;
    }
    if (mark) markAutoFilled(input.closest(".field"), input);
  });
  if (record.sites && record.sites.length) setRowSites(rowEl, record.sites);
  if (mark) rowEl.classList.add("auto-filled-row");
  return rowEl;
}

function collectAllExistingKeys() {
  const keys = new Set();
  Object.keys(SECTION_CONFIG).forEach(sec => {
    document.querySelectorAll(`#${sec}-rows [data-field="key"]`).forEach(inp => {
      const v = inp.value.trim().toUpperCase();
      if (v) keys.add(v);
    });
  });
  return keys;
}

function onParseTickets() {
  const textarea = document.getElementById("pasteArea");
  const statusEl = document.getElementById("pasteStatus");
  const text = textarea.value;
  if (!text.trim()) {
    statusEl.className = "status-msg error";
    statusEl.textContent = "Paste some rows first.";
    return;
  }
  let records;
  try {
    records = parseTicketPaste(text);
  } catch (err) {
    console.error(err);
    statusEl.className = "status-msg error";
    statusEl.textContent = "Couldn't parse that — check the format and try again.";
    return;
  }
  if (records.length === 0) {
    statusEl.className = "status-msg error";
    statusEl.textContent = "No recognizable ticket rows found.";
    return;
  }
  const existingKeys = collectAllExistingKeys();
  const seenInBatch = new Set();
  const skipped = [];
  const counts = { bizconfig: 0, req: 0, tasks: 0, cdd: 0 };
  records.forEach(rec => {
    const normKey = (rec.key || "").trim().toUpperCase();
    if (normKey && (existingKeys.has(normKey) || seenInBatch.has(normKey))) {
      skipped.push(rec.key);
      return;
    }
    if (normKey) seenInBatch.add(normKey);
    addRowWithData(rec.section, rec);
    counts[rec.section]++;
  });
  const addedTotal = records.length - skipped.length;
  let msg = `Added ${addedTotal} ticket(s): ${counts.bizconfig} Business Config, ${counts.req} Requirements, ${counts.tasks} Tasks, ${counts.cdd} Defects.`;
  if (skipped.length) msg += ` Skipped ${skipped.length} duplicate(s) already present: ${skipped.join(", ")}.`;
  statusEl.className = "status-msg ok";
  statusEl.textContent = msg;
}

// ---------- OCR (screenshot -> text) ----------

async function runOcrIntoTextarea(file, textarea, statusEl) {
  statusEl.className = "status-msg";
  statusEl.textContent = "Reading image… this can take a few seconds.";
  try {
    const { data } = await Tesseract.recognize(file, "eng");
    const text = (data && data.text || "").trim();
    if (!text) {
      statusEl.className = "status-msg error";
      statusEl.textContent = "Couldn't read any text from that image.";
      return;
    }
    textarea.value = textarea.value ? `${textarea.value}\n${text}` : text;
    statusEl.className = "status-msg ok";
    statusEl.textContent = "Text extracted — please check it over (OCR on tables isn't perfect), then hit Parse.";
  } catch (err) {
    console.error(err);
    statusEl.className = "status-msg error";
    statusEl.textContent = "Couldn't read that image.";
  }
}

// ---------- Data collection ----------

function collectRows(sectionKey) {
  const cfg = SECTION_CONFIG[sectionKey];
  const container = document.getElementById(`${sectionKey}-rows`);
  const rows = [];
  container.querySelectorAll(".ticket-row").forEach(rowEl => {
    const data = {};
    cfg.rowFields.forEach(f => {
      const input = rowEl.querySelector(`[data-field="${f}"]`);
      data[f] = input ? input.value.trim() : "";
    });
    const sites = Array.from(rowEl.querySelectorAll("[data-site-tags] input:checked")).map(i => i.value);
    if (data.key || data.summary) {
      rows.push({ data, sites });
    }
  });
  return rows;
}

function formatDateLong(isoDate) {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  return `${months[dt.getUTCMonth()]} ${dt.getUTCDate()}, ${dt.getUTCFullYear()}`;
}

function formatDateRev(isoDate) {
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  return `${months[dt.getUTCMonth()]} ${dt.getUTCDate()} - ${dt.getUTCFullYear()}`;
}

function splitVersion(full) {
  const firstDot = full.indexOf(".");
  if (firstDot === -1) return { full, cd: full };
  return { full, cd: full.substring(firstDot + 1) };
}

function xmlEscape(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// ---------- Template engine ----------

function fillSection(xml, key, rows) {
  const tableStartTag = `<!--BLOCK:${key}:TABLE_START-->`;
  const tableEndTag = `<!--BLOCK:${key}:TABLE_END-->`;
  const naStartTag = `<!--BLOCK:${key}:NA_START-->`;
  const naEndTag = `<!--BLOCK:${key}:NA_END-->`;

  const tStart = xml.indexOf(tableStartTag);
  const tEnd = xml.indexOf(tableEndTag) + tableEndTag.length;
  const nStart = xml.indexOf(naStartTag);
  const nEnd = xml.indexOf(naEndTag) + naEndTag.length;

  if (tStart === -1 || nStart === -1) {
    throw new Error(`Template markers for section "${key}" not found. The uploaded template may not be compatible.`);
  }

  const tableBlock = xml.substring(tStart, tEnd);
  const naBlock = xml.substring(nStart, nEnd);

  const rowStartTag = `<!--ROW:${key}-->`;
  const rowEndTag = `<!--/ROW:${key}-->`;
  const rowStart = tableBlock.indexOf(rowStartTag);
  const rowEnd = tableBlock.indexOf(rowEndTag) + rowEndTag.length;
  const rowTplRaw = tableBlock.substring(rowStart + rowStartTag.length, tableBlock.indexOf(rowEndTag));

  let replacement;
  if (rows && rows.length > 0) {
    let cloned = "";
    rows.forEach((r) => {
      let rowXml = rowTplRaw;
      Object.keys(r).forEach(tokenKey => {
        rowXml = rowXml.split(`{{${tokenKey}}}`).join(xmlEscape(r[tokenKey]));
      });
      cloned += rowXml;
    });
    let newTableBlock = tableBlock.substring(0, rowStart) + cloned + tableBlock.substring(rowEnd);
    newTableBlock = newTableBlock.split(tableStartTag).join("").split(tableEndTag).join("");
    replacement = newTableBlock;
  } else {
    replacement = naBlock.split(naStartTag).join("").split(naEndTag).join("");
  }

  return xml.substring(0, tStart) + replacement + xml.substring(nEnd);
}

async function buildDocxForSite(templateArrayBuffer, site, sections, siteValues, globalValues) {
  const zip = await JSZip.loadAsync(templateArrayBuffer);
  const docPath = "word/document.xml";
  let xml = await zip.file(docPath).async("string");

  Object.keys(SECTION_CONFIG).forEach(sectionKey => {
    const cfg = SECTION_CONFIG[sectionKey];
    const allRows = sections[sectionKey];
    const siteRows = allRows.filter(r => r.sites.includes(site));
    const tokenRows = siteRows.map((r, idx) => {
      const tokens = { ROW_SLNO: String(idx + 1) };
      cfg.rowFields.forEach(f => { tokens[cfg.mapTo[f]] = r.data[f] || ""; });
      return tokens;
    });
    xml = fillSection(xml, sectionKey.toUpperCase(), tokenRows);
  });

  const version = splitVersion(siteValues.cdVersionRaw);
  const scalarTokens = {
    CD_VERSION: version.cd,
    FULL_VERSION: version.full,
    REV_DATE: formatDateRev(siteValues.releaseDateIso),
    RELEASE_DATE: formatDateLong(siteValues.releaseDateIso),
    FX_VERSION: siteValues.fxVersion,
    PRODUCT_VERSION: siteValues.productVersion,
    RELEASE_TYPE: siteValues.releaseType,
    SITE_LABEL: SITE_LABELS[site] || site,
    HOTFIX: siteValues.hotfix,
    MIGRATION_TEXT: globalValues.migrationText || "NA",
    E2E_TEXT: globalValues.e2eText || "NA",
    APPSETTINGS_TEXT: globalValues.appSettingsText || "NA",
    WEBCONFIG_TEXT: globalValues.webConfigText || "NA",
  };
  RRP_PACKAGES.forEach(pkg => {
    scalarTokens[`RRP_${pkg.key}`] = siteValues.rrp[pkg.key] || "No";
  });

  Object.keys(scalarTokens).forEach(k => {
    xml = xml.split(`{{${k}}}`).join(xmlEscape(scalarTokens[k]));
  });

  const remaining = xml.match(/\{\{[A-Z_]+\}\}/g);
  if (remaining) console.warn("Unresolved tokens:", [...new Set(remaining)]);

  zip.file(docPath, xml);
  const rawBlob = await zip.generateAsync({ type: "blob" });
  return new Blob([rawBlob], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
}

// ---------- Generate ----------

let lastGeneratedFiles = [];

async function onGenerate() {
  const statusEl = document.getElementById("statusMsg");
  const btn = document.getElementById("generateBtn");
  statusEl.className = "status-msg";
  statusEl.textContent = "";
  clearGeneratedFilesPanel();

  const sites = getSelectedSites();
  if (sites.length === 0) { showError("Pick at least one site."); return; }

  validateForm();
  const untaggedRow = findFirstUntaggedRow();
  if (untaggedRow) {
    showError('A ticket has no site selected under "Applies to" — fix the highlighted row before generating.');
    untaggedRow.classList.add("row-warning");
    untaggedRow.scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }

  const siteValuesMap = {};
  for (const site of sites) {
    const v = getSiteFormValues(site);
    const card = document.querySelector(`[data-site-card][data-site="${site}"]`);
    if (!v.cdVersionRaw) { showError(`${site}: Release/CodeDrop version is required.`); highlightAndFocusField(card.querySelector('[data-field="cdVersion"]')); return; }
    if (!v.productVersion) { showError(`${site}: Product version is required.`); highlightAndFocusField(card.querySelector('[data-field="productVersion"]')); return; }
    if (!v.fxVersion) { showError(`${site}: Framework version is required.`); highlightAndFocusField(card.querySelector('[data-field="fxVersion"]')); return; }
    if (!v.releaseDateIso) { showError(`${site}: Release date is required.`); highlightAndFocusField(card.querySelector('[data-field="releaseDate"]')); return; }
    siteValuesMap[site] = v;
  }

  const globalValues = {
    migrationText: document.getElementById("migrationText").value.trim(),
    e2eText: document.getElementById("e2eText").value.trim(),
    appSettingsText: document.getElementById("appSettingsText").value.trim(),
    webConfigText: document.getElementById("webConfigText").value.trim(),
  };

  const sections = {
    bizconfig: collectRows("bizconfig"),
    req: collectRows("req"),
    tasks: collectRows("tasks"),
    cdd: collectRows("cdd"),
  };

  btn.disabled = true;
  statusEl.textContent = "Generating…";

  try {
    const templateBuffer = uploadedTemplateBuffer || await (await fetch(TEMPLATE_URL)).arrayBuffer();
    const files = [];

    for (const site of sites) {
      const blob = await buildDocxForSite(templateBuffer, site, sections, siteValuesMap[site], globalValues);
      const filename = `FOCUS Code Drop ${siteValuesMap[site].cdVersionRaw} Release Notes ${site}.docx`;
      files.push({ site, filename, blob });
    }

    lastGeneratedFiles = files;
    renderGeneratedFilesPanel(files);
    statusEl.className = "status-msg ok";
    statusEl.textContent = `Ready — ${files.length} file${files.length > 1 ? "s" : ""} generated below.`;
  } catch (err) {
    console.error(err);
    showError(err.message || "Something went wrong while generating the document.");
  } finally {
    btn.disabled = false;
  }
}

function renderGeneratedFilesPanel(files) {
  const panel = document.getElementById("generatedFilesPanel");
  panel.innerHTML = "";
  panel.classList.remove("hidden");
  files.forEach(f => {
    const row = document.createElement("div");
    row.className = "generated-file-row";
    row.innerHTML = `<span class="generated-file-name">${escapeHtml(f.filename)}</span>`;
    const dlBtn = document.createElement("button");
    dlBtn.type = "button";
    dlBtn.className = "btn btn-secondary btn-sm";
    dlBtn.textContent = "Download";
    dlBtn.addEventListener("click", () => saveAs(f.blob, f.filename));
    row.appendChild(dlBtn);
    panel.appendChild(row);
  });
  document.getElementById("downloadAllBtn").classList.toggle("hidden", files.length <= 1);
}

function clearGeneratedFilesPanel() {
  lastGeneratedFiles = [];
  const panel = document.getElementById("generatedFilesPanel");
  panel.innerHTML = "";
  panel.classList.add("hidden");
  document.getElementById("downloadAllBtn").classList.add("hidden");
}

async function onDownloadAll() {
  for (const f of lastGeneratedFiles) {
    saveAs(f.blob, f.filename);
    await new Promise(res => setTimeout(res, 350));
  }
}

function showError(msg) {
  const statusEl = document.getElementById("statusMsg");
  statusEl.className = "status-msg error";
  statusEl.textContent = msg;
}

function highlightAndFocusField(inputEl) {
  if (!inputEl) return;
  inputEl.classList.add("field-error");
  inputEl.scrollIntoView({ behavior: "smooth", block: "center" });
  inputEl.focus();
  const clear = () => {
    inputEl.classList.remove("field-error");
    inputEl.removeEventListener("input", clear);
    inputEl.removeEventListener("change", clear);
  };
  inputEl.addEventListener("input", clear);
  inputEl.addEventListener("change", clear);
}

function findFirstUntaggedRow() {
  for (const sec of Object.keys(SECTION_CONFIG)) {
    const rows = document.querySelectorAll(`#${sec}-rows .ticket-row`);
    for (const rowEl of rows) {
      const keyInput = rowEl.querySelector('[data-field="key"]');
      const summaryInput = rowEl.querySelector('[data-field="summary"]');
      const hasContent = (keyInput && keyInput.value.trim()) || (summaryInput && summaryInput.value.trim());
      if (!hasContent) continue;
      const checked = rowEl.querySelectorAll("[data-site-tags] input:checked").length;
      if (checked === 0) return rowEl;
    }
  }
  return null;
}

// ---------- Inline validation warnings ----------

function clearFlag(rowEl) {
  rowEl.classList.remove("row-warning");
  const msg = rowEl.querySelector(".row-warning-msg");
  if (msg) msg.remove();
}

function flagRow(rowEl, message) {
  rowEl.classList.add("row-warning");
  let msgEl = rowEl.querySelector(".row-warning-msg");
  if (!msgEl) {
    msgEl = document.createElement("div");
    msgEl.className = "row-warning-msg";
    rowEl.appendChild(msgEl);
  }
  const line = `⚠ ${message}`;
  msgEl.textContent = msgEl.textContent ? `${msgEl.textContent}  ${line}` : line;
}

function validateForm() {
  document.querySelectorAll(".ticket-row").forEach(clearFlag);

  document.querySelectorAll(".ticket-row").forEach(rowEl => {
    const keyInput = rowEl.querySelector('[data-field="key"]');
    const hasContent = keyInput && keyInput.value.trim();
    if (!hasContent) return; // don't warn on freshly-added empty rows
    const checked = rowEl.querySelectorAll("[data-site-tags] input:checked").length;
    if (checked === 0) {
      flagRow(rowEl, "Not tagged to any site — won't appear in any generated file.");
    }
    const missingSelects = [];
    const prioritySel = rowEl.querySelector('[data-field="priority"]');
    if (prioritySel && !prioritySel.value) missingSelects.push("Priority");
    const datafixSel = rowEl.querySelector('[data-field="datafix"]');
    if (datafixSel && !datafixSel.value) missingSelects.push("Datafix");
    if (missingSelects.length) {
      flagRow(rowEl, `${missingSelects.join(" and ")} not selected.`);
    }
  });

  const keyMap = {};
  Object.keys(SECTION_CONFIG).forEach(sec => {
    document.querySelectorAll(`#${sec}-rows .ticket-row`).forEach(rowEl => {
      const keyInput = rowEl.querySelector('[data-field="key"]');
      const norm = keyInput ? keyInput.value.trim().toUpperCase() : "";
      if (!norm) return;
      if (!keyMap[norm]) keyMap[norm] = [];
      keyMap[norm].push({ section: SECTION_LABELS[sec], rowEl });
    });
  });
  Object.keys(keyMap).forEach(key => {
    const entries = keyMap[key];
    if (entries.length > 1) {
      entries.forEach(({ rowEl }) => {
        const others = entries.filter(e => e.rowEl !== rowEl).map(e => e.section);
        const uniqueOthers = [...new Set(others)];
        flagRow(rowEl, `${key} also appears in: ${uniqueOthers.join(", ")}${uniqueOthers.length === 0 ? " (duplicate in this section)" : ""}`);
      });
    }
  });
}

// ---------- Reset ----------

function onClearAllTickets() {
  const totalTickets = Object.keys(SECTION_CONFIG).reduce(
    (sum, sec) => sum + document.getElementById(`${sec}-rows`).children.length,
    0
  );
  if (totalTickets === 0 && !document.getElementById("pasteArea").value.trim()) return;

  const confirmed = confirm(
    `This clears all ${totalTickets} parsed ticket(s) across Business Configuration, Requirements, Tasks Completed, and Code Drop Defects, plus the paste box above. Release details, sites, and the other notes fields are left untouched. Continue?`
  );
  if (!confirmed) return;

  Object.keys(SECTION_CONFIG).forEach(sec => {
    document.getElementById(`${sec}-rows`).innerHTML = "";
  });

  document.getElementById("pasteArea").value = "";
  document.getElementById("pasteStatus").textContent = "";
}

function onResetAll() {
  const confirmed = confirm("This clears everything you've entered (release details, tickets, notes) and starts a fresh release. Continue?");
  if (!confirmed) return;

  document.querySelectorAll('input[name="site"]').forEach(cb => { cb.checked = cb.value === "Core"; });
  updateSiteDetailVisibility();

  SITES.forEach(site => {
    const card = document.querySelector(`[data-site-card][data-site="${site}"]`);
    if (!card) return;
    card.querySelector("[data-paste-details]").value = "";
    card.querySelector('[data-field="cdVersion"]').value = "";
    card.querySelector('[data-field="productVersion"]').value = "";
    card.querySelector('[data-field="fxVersion"]').value = "";
    card.querySelector('[data-field="releaseDate"]').value = "";
    card.querySelector('[data-field="releaseType"]').value = "Full Release";
    card.querySelector('[data-field="hotfix"]').value = "No";
    RRP_PACKAGES.forEach(pkg => {
      const sel = card.querySelector(`[data-rrp="${pkg.key}"]`);
      if (sel) sel.checked = false;
    });
    card.querySelectorAll(".auto-filled").forEach(el => el.classList.remove("auto-filled"));
    const chatOut = card.querySelector("[data-chat-output]");
    if (chatOut) chatOut.value = "";
  });

  Object.keys(SECTION_CONFIG).forEach(sec => {
    document.getElementById(`${sec}-rows`).innerHTML = "";
  });

  document.getElementById("migrationText").value = "";
  document.getElementById("e2eText").value = "";
  document.getElementById("appSettingsText").value = "";
  document.getElementById("webConfigText").value = "";
  document.getElementById("pasteArea").value = "";
  document.getElementById("pasteStatus").textContent = "";
  document.getElementById("statusMsg").textContent = "";
  document.getElementById("statusMsg").className = "status-msg";

  clearGeneratedFilesPanel();
  Store.remove(AUTOSAVE_KEY);
  renderSummary();
  validateForm();
}

// ---------- Draft serialization (autosave + manual save/load) ----------

function serializeFormState() {
  const state = {
    sites: getSelectedSites(),
    siteDetails: {},
    sections: {},
    migrationText: document.getElementById("migrationText").value,
    e2eText: document.getElementById("e2eText").value,
    appSettingsText: document.getElementById("appSettingsText").value,
    webConfigText: document.getElementById("webConfigText").value,
    pasteAreaText: document.getElementById("pasteArea").value,
  };
  SITES.forEach(site => {
    const card = document.querySelector(`[data-site-card][data-site="${site}"]`);
    if (!card) return;
    const v = getSiteFormValues(site);
    state.siteDetails[site] = { ...v, pasteText: card.querySelector("[data-paste-details]").value };
  });
  Object.keys(SECTION_CONFIG).forEach(sec => {
    state.sections[sec] = collectRows(sec).map(r => ({ ...r.data, sites: r.sites }));
  });
  return state;
}

function restoreFormState(state) {
  if (!state) return;
  document.querySelectorAll('input[name="site"]').forEach(cb => {
    cb.checked = (state.sites || []).includes(cb.value);
  });
  updateSiteDetailVisibility();

  SITES.forEach(site => {
    const d = state.siteDetails && state.siteDetails[site];
    const card = document.querySelector(`[data-site-card][data-site="${site}"]`);
    if (!d || !card) return;
    card.querySelector("[data-paste-details]").value = d.pasteText || "";
    card.querySelector('[data-field="cdVersion"]').value = d.cdVersionRaw || "";
    card.querySelector('[data-field="productVersion"]').value = d.productVersion || "";
    card.querySelector('[data-field="fxVersion"]').value = d.fxVersion || "";
    card.querySelector('[data-field="releaseDate"]').value = d.releaseDateIso || "";
    if (d.releaseType) card.querySelector('[data-field="releaseType"]').value = d.releaseType;
    if (d.hotfix) card.querySelector('[data-field="hotfix"]').value = d.hotfix;
    RRP_PACKAGES.forEach(pkg => {
      const sel = card.querySelector(`[data-rrp="${pkg.key}"]`);
      if (sel) sel.checked = !!(d.rrp && d.rrp[pkg.key] === "Yes");
    });
    // Restored data is user-confirmed (from a save), not a fresh unverified parse
    card.querySelectorAll(".field.auto-filled, .rrp-field.auto-filled").forEach(el => el.classList.remove("auto-filled"));
  });

  Object.keys(SECTION_CONFIG).forEach(sec => {
    const container = document.getElementById(`${sec}-rows`);
    container.innerHTML = "";
    (state.sections && state.sections[sec] || []).forEach(rec => addRowWithData(sec, rec, false));
  });

  document.getElementById("migrationText").value = state.migrationText || "";
  document.getElementById("e2eText").value = state.e2eText || "";
  document.getElementById("appSettingsText").value = state.appSettingsText || "";
  document.getElementById("webConfigText").value = state.webConfigText || "";
  if (state.pasteAreaText) document.getElementById("pasteArea").value = state.pasteAreaText;

  renderSummary();
}

function onSaveDraft() {
  const state = serializeFormState();
  const firstSite = state.sites[0];
  const version = (firstSite && state.siteDetails[firstSite] && state.siteDetails[firstSite].cdVersionRaw) || "draft";
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  saveAs(blob, `Release Notes Draft ${version}.json`);
}

async function onLoadDraftFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const text = await file.text();
    const state = JSON.parse(text);
    restoreFormState(state);
    const statusEl = document.getElementById("statusMsg");
    statusEl.className = "status-msg ok";
    statusEl.textContent = `Loaded draft from ${file.name}.`;
  } catch (err) {
    console.error(err);
    alert("Couldn't read that draft file — is it a JSON file saved from this app?");
  } finally {
    e.target.value = "";
  }
}

// ---------- Live summary ----------

function renderSummary() {
  const panel = document.getElementById("summaryPanel");
  if (!panel) return;
  const sites = getSelectedSites();
  if (sites.length === 0) {
    panel.innerHTML = `<p class="hint">Pick at least one site above to see a summary here.</p>`;
    return;
  }
  const sections = {
    bizconfig: collectRows("bizconfig"),
    req: collectRows("req"),
    tasks: collectRows("tasks"),
    cdd: collectRows("cdd"),
  };
  let html = "";
  sites.forEach(site => {
    const v = getSiteFormValues(site);
    const counts = {};
    Object.keys(sections).forEach(k => { counts[k] = sections[k].filter(r => r.sites.includes(site)).length; });
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    html += `
      <div class="summary-site">
        <div class="summary-site-name">${escapeHtml(site)}</div>
        <div class="summary-meta">${escapeHtml(v.cdVersionRaw || "no version yet")} &middot; ${escapeHtml(v.releaseDateIso || "no date yet")} &middot; ${escapeHtml(v.releaseType || "")} &middot; Hotfix ${escapeHtml(v.hotfix || "No")}</div>
        <div class="summary-counts">${counts.bizconfig} Business Config &middot; ${counts.req} Requirements &middot; ${counts.tasks} Tasks &middot; ${counts.cdd} Defects
          ${total === 0 ? '<span class="summary-empty-note">— no tickets, sections will read NA / No RBS Impact</span>' : ""}
        </div>
      </div>`;
  });
  panel.innerHTML = html;
}
