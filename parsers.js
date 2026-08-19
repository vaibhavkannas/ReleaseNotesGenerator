/* Parsing helpers for the paste-first workflow.
 * Kept in a separate, dependency-free module so it can be unit tested in Node
 * and reused by app.js in the browser.
 */

const MONTHS = ["january","february","march","april","may","june","july","august","september","october","november","december"];

function parseDateFlexible(raw) {
  if (!raw) return null;
  let s = raw.trim().toLowerCase();
  s = s.replace(/(\d+)(st|nd|rd|th)/g, "$1"); // strip ordinals
  s = s.replace(/[.,]/g, " ").replace(/\s+/g, " ").trim();

  // yyyy-mm-dd
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (m) return isoFrom(+m[1], +m[2], +m[3]);

  // dd month yyyy  (e.g. "5 aug 2026", "7 august 2026")
  m = s.match(/^(\d{1,2})\s+([a-z]+)\s+(\d{4})$/);
  if (m) {
    const mo = monthIndex(m[2]);
    if (mo !== -1) return isoFrom(+m[3], mo + 1, +m[1]);
  }

  // month dd yyyy (e.g. "august 5 2026")
  m = s.match(/^([a-z]+)\s+(\d{1,2})\s+(\d{4})$/);
  if (m) {
    const mo = monthIndex(m[1]);
    if (mo !== -1) return isoFrom(+m[3], mo + 1, +m[2]);
  }

  // dd/mm/yyyy or mm/dd/yyyy - assume dd/mm/yyyy (India context), fallback mm/dd
  m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (m) {
    let d = +m[1], mo = +m[2], y = +m[3];
    if (mo > 12) { const t = d; d = mo; mo = t; }
    return isoFrom(y, mo, d);
  }

  return null;
}

function monthIndex(name) {
  name = name.toLowerCase();
  for (let i = 0; i < MONTHS.length; i++) {
    if (MONTHS[i].startsWith(name) || name.startsWith(MONTHS[i].slice(0, 3))) return i;
  }
  return -1;
}

function isoFrom(y, mo, d) {
  const mm = String(mo).padStart(2, "0");
  const dd = String(d).padStart(2, "0");
  return `${y}-${mm}-${dd}`;
}

const PACKAGE_SYNONYMS = {
  LESSOR_PORTAL: ["lessorportal", "lessor"],
  WINDOWS_SERVICE: ["windowsservice", "windowservice", "winservice"],
  WEB_API: ["webapi", "web"],
  DATABASE: ["database", "db"],
  REPORTS: ["reports", "report"],
  APPSETTINGS_CONFIG: ["appsettingsconfig", "appsettings", "appsettingconfig", "appconfig"],
};

function normalizePkgToken(tok) {
  return tok.toLowerCase().replace(/[^a-z]/g, "");
}

function matchPackageKey(tok) {
  const norm = normalizePkgToken(tok);
  if (!norm) return null;
  for (const key of Object.keys(PACKAGE_SYNONYMS)) {
    for (const syn of PACKAGE_SYNONYMS[key]) {
      if (norm === syn || norm.includes(syn) || syn.includes(norm)) return key;
    }
  }
  return null;
}

function parsePackagesText(text) {
  const result = {};
  if (!text) return result;

  let working = text;

  // "rest ... yes/no" - find and remove for default-fill
  let restDefault = null;
  const restMatch = working.match(/rest[^a-zA-Z]{0,15}(yes|no)/i);
  if (restMatch) {
    restDefault = restMatch[1].toLowerCase() === "yes" ? "Yes" : "No";
    working = working.slice(0, restMatch.index);
  }

  // find segments like "<names list> (-|:|are|is) (yes|no)"
  const segRe = /([a-z ,\/&]+?)\s*(?:-|:|are|is)\s*(yes|no)\b/gi;
  let m;
  while ((m = segRe.exec(working)) !== null) {
    const names = m[1].split(/,|\/|&|\band\b/i).map(s => s.trim()).filter(Boolean);
    const val = m[2].toLowerCase() === "yes" ? "Yes" : "No";
    names.forEach(n => {
      const key = matchPackageKey(n);
      if (key) result[key] = val;
    });
  }

  if (restDefault) {
    Object.keys(PACKAGE_SYNONYMS).forEach(key => {
      if (!(key in result)) result[key] = restDefault;
    });
  }

  return result;
}

function parseReleaseParagraph(text) {
  const out = {};
  if (!text) return out;
  const lines = text.split(/\n/).map(l => l.trim()).filter(Boolean);

  lines.forEach(line => {
    let m;
    if ((m = line.match(/^(?:release\s*)?version\s*[:\-]\s*(.+)$/i)) && !/product|fx|framework/i.test(line)) {
      out.cdVersion = m[1].trim();
    }
    if ((m = line.match(/product\s*version\s*[:\-]\s*(.+)$/i))) {
      out.productVersion = m[1].trim();
    }
    if ((m = line.match(/(?:fx|framework)\s*version\s*[:\-]\s*(.+)$/i))) {
      out.fxVersion = m[1].trim();
    }
    if ((m = line.match(/(?:release\s*)?date\s*[:\-]\s*(.+)$/i))) {
      const iso = parseDateFlexible(m[1]);
      if (iso) out.releaseDate = iso;
    }
    if ((m = line.match(/hotfix[^:\-]*[:\-]\s*(yes|no)/i))) {
      out.hotfix = m[1].toLowerCase() === "yes" ? "Yes" : "No";
    }
    if ((m = line.match(/type(?:\s*of\s*release)?\s*[:\-]\s*(.+)$/i))) {
      const raw = m[1].trim().toLowerCase();
      if (raw.includes("database")) out.releaseType = "Database Release";
      else if (raw.includes("patch")) out.releaseType = "Patch Release";
      else if (raw.includes("full")) out.releaseType = "Full Release";
    }
  });

  // Packages: look from the first line mentioning "package" onward; else whole text
  const pkgLineIdx = lines.findIndex(l => /packages?/i.test(l));
  const pkgText = pkgLineIdx !== -1 ? lines.slice(pkgLineIdx).join(", ") : text;
  const pkgResult = parsePackagesText(pkgText);
  if (Object.keys(pkgResult).length) out.rrp = pkgResult;

  // bare date anywhere, e.g. "7th august 2026" on its own line with no label
  if (!out.releaseDate) {
    for (const line of lines) {
      const iso = parseDateFlexible(line);
      if (iso) { out.releaseDate = iso; break; }
    }
  }

  return out;
}

// ---------------- Ticket paste parser ----------------

const HEADER_KEYWORDS = {
  issueType: ["issue type"],
  key: ["issue key", "key"],
  summary: ["summary"],
  priority: ["priority"],
  targetSection: ["release notes section", "notes section", "release section"],
  subType: ["ticket type", "type"], // only matched if "issue type"/"target section" didn't already match on the same cell
  sites: ["core/pp/cp", "core/cp/pp", "applies to", "environment", "site", "sites", "core"],
  datafix: ["datafix", "data fix"],
  assignee: ["assignee"],
  slno: ["sl no", "sl.no", "s.no", "sr no"],
  numTestCases: ["number of test cases", "num test cases", "# test cases", "# of test cases"],
  testCasesPassed: ["test cases passed", "tc passed", "# passed", "passed"],
  testCasesFailed: ["test cases failed", "tc failed", "# failed", "failed"],
  comments: ["comments", "comment", "remarks", "notes"],
};

function normalizeHeaderCell(cell) {
  return cell.trim().toLowerCase();
}

function detectDelimiter(line) {
  if (line.includes("\t")) return "\t";
  if (/ {2,}/.test(line)) return /\s{2,}/;
  return ",";
}

function splitLine(line, delim) {
  if (delim instanceof RegExp) return line.split(delim);
  return line.split(delim);
}

function mapHeaderRow(cells) {
  const map = {}; // index -> fieldName
  cells.forEach((cell, i) => {
    const norm = normalizeHeaderCell(cell);
    if (!norm) return;
    if (norm.includes("issue type")) { map[i] = "issueType"; return; }
    for (const field of Object.keys(HEADER_KEYWORDS)) {
      if (field === "issueType") continue;
      for (const kw of HEADER_KEYWORDS[field]) {
        if (norm === kw || norm.includes(kw)) { map[i] = field; return; }
      }
    }
  });
  return map;
}

function looksLikeHeader(cells) {
  const norm = cells.map(normalizeHeaderCell);
  let hits = 0;
  norm.forEach(c => {
    Object.values(HEADER_KEYWORDS).flat().forEach(kw => {
      if (c === kw || c.includes(kw)) hits++;
    });
  });
  return hits >= 2;
}

function parseSitesToken(raw) {
  if (!raw) return [];
  const tokens = raw.split(/[,\/&]|\band\b/i).map(t => t.trim().toLowerCase()).filter(Boolean);
  const sites = new Set();
  tokens.forEach(t => {
    const n = t.replace(/[^a-z]/g, "");
    if (!n) return;
    if (n === "pp" || n.startsWith("partner")) sites.add("Partner Portal");
    else if (n === "cp" || n.startsWith("customer")) sites.add("Customer Portal");
    else if (n.length >= 3 && n.startsWith("cor")) sites.add("Core"); // tolerate truncation, e.g. "Cor"
    else if (n === "core") sites.add("Core");
  });
  return Array.from(sites);
}

function normalizeTargetSection(raw) {
  if (!raw) return null;
  const s = raw.toLowerCase();
  if (/defect|bug/.test(s)) return "cdd";
  if (/task/.test(s)) return "tasks";
  if (/requirement/.test(s)) return "req";
  if (/business|rbs|ebc|config/.test(s)) return "bizconfig";
  return null;
}

function decideSection(issueType, subType, targetSectionRaw) {
  const explicit = normalizeTargetSection(targetSectionRaw);
  if (explicit) return explicit;
  const it = (issueType || "").toLowerCase();
  const st = (subType || "").toLowerCase();
  if (it.includes("bug")) return "cdd";
  if (it.includes("requirement")) return "req";
  if (/rbs|ebc|portfolio config|user config/.test(st)) return "bizconfig";
  if (it.includes("task") || it === "") return "tasks";
  return "tasks";
}

const FALLBACK_FIELD_ORDER = ["issueType", "key", "summary", "assignee", "priority", "subType", "sites"];

function parseTicketPaste(text) {
  const lines = text.split(/\n/).map(l => l.replace(/\r$/, "")).filter(l => l.trim() !== "");
  if (lines.length === 0) return [];

  const delim = detectDelimiter(lines[0]);
  const rows = lines.map(l => splitLine(l, delim).map(c => c.trim()));

  let headerMap = null;
  let dataRows = rows;
  if (looksLikeHeader(rows[0])) {
    headerMap = mapHeaderRow(rows[0]);
    dataRows = rows.slice(1);
  }

  const results = [];
  dataRows.forEach(cells => {
    if (cells.every(c => c === "")) return;
    let rec = {};
    if (headerMap) {
      cells.forEach((cell, i) => {
        const field = headerMap[i];
        if (field) rec[field] = cell;
      });
    } else {
      // best-effort fixed order fallback: Issue Type, Key, Summary, Assignee, Priority, Type, Sites
      FALLBACK_FIELD_ORDER.forEach((field, i) => { if (cells[i] !== undefined) rec[field] = cells[i]; });
    }
    if (!rec.key && !rec.summary) return; // skip junk rows

    const section = decideSection(rec.issueType, rec.subType, rec.targetSection);
    results.push({
      section,
      issueType: rec.issueType || "",
      key: rec.key || "",
      summary: rec.summary || "",
      priority: rec.priority || "Medium",
      type: rec.subType || "",
      datafix: rec.datafix ? (/yes/i.test(rec.datafix) ? "Yes" : "No") : "No",
      sites: parseSitesToken(rec.sites || ""),
      numTestCases: rec.numTestCases || "",
      testCasesPassed: rec.testCasesPassed || "",
      testCasesFailed: rec.testCasesFailed || "",
      comments: rec.comments || "",
    });
  });

  return results;
}

if (typeof module !== "undefined") {
  module.exports = {
    parseDateFlexible, parsePackagesText, parseReleaseParagraph,
    parseTicketPaste, decideSection, parseSitesToken, FALLBACK_FIELD_ORDER,
  };
}
