# FOCUS Release Notes Generator

A fully client-side tool for generating Odessa FOCUS release notes `.docx` files, straight from the browser. No backend, no uploads — everything runs locally in JavaScript using [JSZip](https://stuk.github.io/jszip/).

**Live app:** enable GitHub Pages for this repo (Settings → Pages → Deploy from branch `main` / root), then visit `https://<your-username>.github.io/ReleaseNotesGenerator/`.

## How it works

- `assets/master_template.docx` is a version of the base Word template with the dynamic fields replaced by `{{TOKEN}}` placeholders, and each data section (Business Configuration, Requirements, Tasks Completed, Code Drop Defects) wrapped in HTML-style comment markers that mark a repeatable table row plus a fallback "NA" block.
- `app.js` fetches that template, unzips it in-browser with JSZip, clones the row markup once per ticket you enter, fills in every token, and re-zips it into a downloadable `.docx` — one per site you select.
- Nothing leaves your browser. The "Use a different template" option lets you swap in another docx, as long as it has the same token/marker structure (advanced use only).

## Sections & rules encoded in the app

- **Business Configuration** — Sl No, Issue Key, Summary, Type. Empty → "No RBS Impact".
- **Requirements** — Sl No, Issue Key, Summary, Priority, Datafix. Empty → "NA".
- **Migration / E2E Scenarios** — free text, defaults to "NA".
- **Tasks Completed** — Sl No, Issue Key, Summary, Priority, Datafix. Empty → "NA".
- **Code Drop Defects** — Sl No, Issue Key, Summary, Priority, Datafix. Empty → "NA".
- **Technical Configuration** — AppSettings.Config / Web Config free text, defaults to "NA".
- **Release Request Packages** — 6 fixed packages (Lessor Portal, Windows Service, Web API, Database, Reports, App Settings Config), each Yes/No.
- **Multi-site tickets** — each ticket row has "Applies to" site tags, so a ticket relevant to Core and Partner Portal appears in both generated files automatically.
- **File naming** — `FOCUS Code Drop {version} Release Notes {Site}.docx`, spaces between words, dots only in the version number.

## Regenerating the master template

If the base Word template ever changes structurally, `tools/templatize.py` rebuilds `assets/master_template.docx` from a fresh copy of the base template. It locates each section heading and Release Details field by text/structure search (not hardcoded positions) and inserts the token/marker structure.

```bash
mkdir work && cd work
cp /path/to/new/base_template.docx doc.docx
unzip doc.docx -d unpacked
python3 ../tools/templatize.py     # edits unpacked/word/document.xml in place
cd unpacked && zip -r -X ../master_template.docx . && cd ..
cp master_template.docx ../assets/master_template.docx
```

Note: `templatize.py` expects `unpacked/word/document.xml` relative to where it's run, and assumes the base template's internal structure (paragraph IDs, table layouts) matches the original FOCUS template this was built against. A structurally different template will need the anchor strings inside the script updated.

## Local development

Just open `index.html` in a browser, or serve the folder with any static file server:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.
