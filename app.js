/* FOCUS Release Notes Generator
 * Fully client-side. Fetches a "master template" docx (base template with
 * {{TOKEN}} placeholders and <!--BLOCK:...--> / <!--ROW:...--> markers already
 * embedded in word/document.xml), fills it per release, and produces one
 * docx per selected site.
 */

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

let uploadedTemplateBuffer = null; // ArrayBuffer if user picked a custom template

// ---------- UI bootstrap ----------

document.addEventListener("DOMContentLoaded", () => {
  buildRrpUI();
  Object.keys(SECTION_CONFIG).forEach(refreshSiteTagsForSection);

  document.querySelectorAll("[data-add]").forEach(btn => {
    btn.addEventListener("click", () => addRow(btn.dataset.add));
  });

  document.querySelectorAll('input[name="site"]').forEach(cb => {
    cb.addEventListener("change", () => {
      Object.keys(SECTION_CONFIG).forEach(refreshSiteTagsForSection);
    });
  });

  document.getElementById("uploadTemplateBtn").addEventListener("click", () => {
    document.getElementById("templateFile").click();
  });
  document.getElementById("templateFile").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    uploadedTemplateBuffer = await file.arrayBuffer();
    const status = document.getElementById("templateStatus");
    status.innerHTML = `<span class="dot dot-ok"></span><span>Using: ${escapeHtml(file.name)}</span> <button type="button" id="resetTemplateBtn" class="link-btn">Use bundled template</button>`;
    document.getElementById("resetTemplateBtn").addEventListener("click", () => {
      uploadedTemplateBuffer = null;
      location.reload();
    });
  });

  document.getElementById("generateBtn").addEventListener("click", onGenerate);
});

function getSelectedSites() {
  return Array.from(document.querySelectorAll('input[name="site"]:checked')).map(cb => cb.value);
}

function buildRrpUI() {
  const grid = document.getElementById("rrpGrid");
  grid.innerHTML = "";
  RRP_PACKAGES.forEach(pkg => {
    const div = document.createElement("div");
    div.className = "field";
    div.innerHTML = `
      <label>${pkg.label}</label>
      <select data-rrp="${pkg.key}">
        <option value="No" selected>No</option>
        <option value="Yes">Yes</option>
      </select>
    `;
    grid.appendChild(div);
  });
}

function addRow(sectionKey) {
  const tpl = document.getElementById(`row-tpl-${sectionKey}`);
  const container = document.getElementById(`${sectionKey}-rows`);
  const node = tpl.content.cloneNode(true);
  container.appendChild(node);
  refreshSiteTagsForSection(sectionKey);
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
  // isoDate: yyyy-mm-dd -> "August 5, 2026"
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  return `${months[dt.getUTCMonth()]} ${dt.getUTCDate()}, ${dt.getUTCFullYear()}`;
}

function formatDateRev(isoDate) {
  // "August 5 - 2026"
  if (!isoDate) return "";
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  return `${months[dt.getUTCMonth()]} ${dt.getUTCDate()} - ${dt.getUTCFullYear()}`;
}

function splitVersion(full) {
  // "118.7.31.2" -> { full: "118.7.31.2", cd: "7.31.2" }
  const firstDot = full.indexOf(".");
  if (firstDot === -1) return { full, cd: full };
  return { full, cd: full.substring(firstDot + 1) };
}

// ---------- XML escaping ----------

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

  let combinedOld;
  let replacement;

  if (rows && rows.length > 0) {
    let cloned = "";
    rows.forEach((r, i) => {
      let rowXml = rowTplRaw;
      Object.keys(r).forEach(tokenKey => {
        rowXml = rowXml.split(`{{${tokenKey}}}`).join(xmlEscape(r[tokenKey]));
      });
      cloned += rowXml;
    });
    let newTableBlock = tableBlock.substring(0, rowStart) + cloned + tableBlock.substring(rowEnd);
    newTableBlock = newTableBlock.split(tableStartTag).join("").split(tableEndTag).join("");
    combinedOld = xml.substring(tStart, nEnd); // table block + na block together
    replacement = newTableBlock;
  } else {
    let newNaBlock = naBlock.split(naStartTag).join("").split(naEndTag).join("");
    combinedOld = xml.substring(tStart, nEnd);
    replacement = newNaBlock;
  }

  return xml.substring(0, tStart) + replacement + xml.substring(nEnd);
}

async function buildDocxForSite(templateArrayBuffer, site, formValues) {
  const zip = await JSZip.loadAsync(templateArrayBuffer);
  const docPath = "word/document.xml";
  let xml = await zip.file(docPath).async("string");

  // Section rows filtered to this site
  Object.keys(SECTION_CONFIG).forEach(sectionKey => {
    const cfg = SECTION_CONFIG[sectionKey];
    const allRows = formValues.sections[sectionKey];
    const siteRows = allRows.filter(r => r.sites.includes(site));
    const tokenRows = siteRows.map((r, idx) => {
      const tokens = { ROW_SLNO: String(idx + 1) };
      cfg.rowFields.forEach(f => {
        tokens[cfg.mapTo[f]] = r.data[f] || "";
      });
      return tokens;
    });
    xml = fillSection(xml, sectionKey.toUpperCase(), tokenRows);
  });

  // Scalar tokens
  const scalarTokens = {
    CD_VERSION: formValues.version.cd,
    FULL_VERSION: formValues.version.full,
    REV_DATE: formValues.revDate,
    RELEASE_DATE: formValues.releaseDate,
    FX_VERSION: formValues.fxVersion,
    PRODUCT_VERSION: formValues.productVersion,
    RELEASE_TYPE: formValues.releaseType,
    SITE_LABEL: SITE_LABELS[site] || site,
    HOTFIX: formValues.hotfix,
    MIGRATION_TEXT: formValues.migrationText || "NA",
    E2E_TEXT: formValues.e2eText || "NA",
    APPSETTINGS_TEXT: formValues.appSettingsText || "NA",
    WEBCONFIG_TEXT: formValues.webConfigText || "NA",
  };
  RRP_PACKAGES.forEach(pkg => {
    scalarTokens[`RRP_${pkg.key}`] = formValues.rrp[pkg.key] || "No";
  });

  Object.keys(scalarTokens).forEach(k => {
    xml = xml.split(`{{${k}}}`).join(xmlEscape(scalarTokens[k]));
  });

  const remaining = xml.match(/\{\{[A-Z_]+\}\}/g);
  if (remaining) {
    console.warn("Unresolved tokens:", [...new Set(remaining)]);
  }

  zip.file(docPath, xml);
  const rawBlob = await zip.generateAsync({ type: "blob" });
  return new Blob([rawBlob], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
}

// ---------- Generate ----------

async function onGenerate() {
  const statusEl = document.getElementById("statusMsg");
  const btn = document.getElementById("generateBtn");
  statusEl.className = "status-msg";
  statusEl.textContent = "";

  const sites = getSelectedSites();
  const cdVersionRaw = document.getElementById("cdVersion").value.trim();
  const productVersion = document.getElementById("productVersion").value.trim();
  const fxVersion = document.getElementById("fxVersion").value.trim();
  const releaseDateIso = document.getElementById("releaseDate").value;

  if (sites.length === 0) { showError("Pick at least one site."); return; }
  if (!cdVersionRaw) { showError("Release / CodeDrop version is required."); return; }
  if (!productVersion) { showError("Product version is required."); return; }
  if (!fxVersion) { showError("Framework version is required."); return; }
  if (!releaseDateIso) { showError("Release date is required."); return; }

  const formValues = {
    version: splitVersion(cdVersionRaw),
    productVersion,
    fxVersion,
    releaseDate: formatDateLong(releaseDateIso),
    revDate: formatDateRev(releaseDateIso),
    releaseType: document.getElementById("releaseType").value,
    hotfix: document.getElementById("hotfix").value,
    migrationText: document.getElementById("migrationText").value.trim(),
    e2eText: document.getElementById("e2eText").value.trim(),
    appSettingsText: document.getElementById("appSettingsText").value.trim(),
    webConfigText: document.getElementById("webConfigText").value.trim(),
    rrp: {},
    sections: {
      bizconfig: collectRows("bizconfig"),
      req: collectRows("req"),
      tasks: collectRows("tasks"),
      cdd: collectRows("cdd"),
    },
  };
  RRP_PACKAGES.forEach(pkg => {
    const sel = document.querySelector(`[data-rrp="${pkg.key}"]`);
    formValues.rrp[pkg.key] = sel ? sel.value : "No";
  });

  btn.disabled = true;
  statusEl.textContent = "Generating…";

  try {
    const templateBuffer = uploadedTemplateBuffer || await (await fetch(TEMPLATE_URL)).arrayBuffer();

    for (const site of sites) {
      const blob = await buildDocxForSite(templateBuffer, site, formValues);
      const filename = `FOCUS Code Drop ${formValues.version.full} Release Notes ${site}.docx`;
      saveAs(blob, filename);
      // small delay so multiple downloads don't get blocked by the browser
      await new Promise(res => setTimeout(res, 350));
    }
    statusEl.className = "status-msg ok";
    statusEl.textContent = `Done — generated ${sites.length} file${sites.length > 1 ? "s" : ""}.`;
  } catch (err) {
    console.error(err);
    showError(err.message || "Something went wrong while generating the document.");
  } finally {
    btn.disabled = false;
  }
}

function showError(msg) {
  const statusEl = document.getElementById("statusMsg");
  statusEl.className = "status-msg error";
  statusEl.textContent = msg;
}
