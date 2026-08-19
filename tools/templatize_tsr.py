"""
Templatizes the Odessa Test Summary Report base docx.

Run against a fresh unzip of the base doc (word/document.xml already run
through merge_runs.py). Produces tokens:
  {{CURRENT_RELEASE_VERSION}} - e.g. "8.1.1" (same value as Release Notes' CD_VERSION)
  {{RELEASE_DATE_LONG}}       - "August 17, 2026" style (matches cover page's existing format)
  {{RELEASE_DATE_SHORT}}      - "17/08/2026" style (DD/MM/YYYY, matches pages 2-4's format)

Also handles the embedded Excel object's renaming (zip entry + relationship
target + internal title) -- see rename_embedded_excel() below, called
separately by the site's build step since it needs the actual release
version at generation time, not templatization time.
"""
import re

path = 'unpacked/word/document.xml'
data = open(path, encoding='utf-8').read()


def one(old, new, label=None):
    n = data.count(old)
    assert n == 1, f"{label or old[:60]!r}: expected 1 occurrence, got {n}"
    return data.replace(old, new, 1)


def take_one(text, old, new, label=None):
    """Like one(), but for values that legitimately repeat multiple times
    across the document (e.g. '139' or '0 / 0 /0' appearing in several rows)
    -- replaces just the next unconsumed occurrence, in document order,
    rather than requiring global uniqueness."""
    n = text.count(old)
    assert n >= 1, f"{label or old[:60]!r}: expected at least 1 remaining occurrence, got {n}"
    return text.replace(old, new, 1)


# ==== Cover page ====
data = one('<w:t>TIC - Release- PI7.31.3</w:t>', '<w:t>TIC - Release- PI{{CURRENT_RELEASE_VERSION}}</w:t>', 'cover version')
data = one(
    '<w:t xml:space="preserve">August 17, 2026</w:t>',
    '<w:t xml:space="preserve">{{RELEASE_DATE_LONG}}</w:t>',
    'cover date',
)

# ==== Page 2: Table 1 (Document version) + Table 2 (Document revision history) ====
# Both "Effective Date" and "Date" cells hold the identical literal text
# "17/08/2026" -- replace each occurrence in turn (positional, since the
# text and surrounding formatting are identical for both).
assert data.count('<w:t>17/08/2026</w:t>') == 3, f"expected 3 short-date occurrences before page-3 table, got {data.count('<w:t>17/08/2026</w:t>')}"
data = data.replace('<w:t>17/08/2026</w:t>', '<w:t>{{RELEASE_DATE_SHORT}}</w:t>', 1)  # Table 1: Effective Date
data = data.replace('<w:t>17/08/2026</w:t>', '<w:t>{{RELEASE_DATE_SHORT}}</w:t>', 1)  # Table 2: Date

# ==== Page 3: "1.1 Test Summary Report" sentence ("Release: PIx.y.z, DD/MM/YYYY.") ====
data = data.replace('<w:t>7.31.3</w:t>', '<w:t>{{CURRENT_RELEASE_VERSION}}</w:t>', 1)
data = one(
    '<w:t xml:space="preserve">, 17/08/2026.</w:t>',
    '<w:t xml:space="preserve">, {{RELEASE_DATE_SHORT}}.</w:t>',
    'page3 sentence date',
)

# ==== Page 3: "Types of Tests in Scope" table row ("Requirement/Bug: PIx.y.z" / "DD/MM/YYYY") ====
data = data.replace('<w:t>7.31.3</w:t>', '<w:t>{{CURRENT_RELEASE_VERSION}}</w:t>', 1)
data = one('<w:t>17/08/2026</w:t>', '<w:t>{{RELEASE_DATE_SHORT}}</w:t>', 'page3 table date')

# ==== Page 4: "Release Details" row ("PI x.y.z DD/MM/YYYY") ====
# Split across two runs with subtly different rPr (one has an extra
# <w:lang w:bidi="ar-SA"/>), which is why merge_runs.py didn't combine them.
# The whole version+date now lives in the first run; the second is emptied.
data = one(
    '<w:t xml:space="preserve">7.31.3 17</w:t>',
    '<w:t xml:space="preserve">{{CURRENT_RELEASE_VERSION}} {{RELEASE_DATE_SHORT}}</w:t>',
    'page4 release details version+date-day',
)
data = one('<w:t>/08/2026</w:t>', '<w:t></w:t>', 'page4 release details date-rest')

# ==== Page 4: Test Execution Summary second table -- clear all value cells ====
# The three columns "PI Functional / Defects Testing", "Smoke/Regression/E2E",
# and "Total" have 6 rows of numeric values below them. Every one of these
# gets tokenized so the site's build step can fill "PI Functional / Defects
# Testing" with computed totals (from the ticket data) while leaving
# "Smoke/Regression/E2E" and "Total" as blank for manual entry.
#
# Each row's 3 cells confirmed individually against the source (exact
# xml:space usage varies per cell, so exact snippets are used rather than
# inferring from the bare value) and replaced in top-to-bottom row order,
# since several values repeat identically across rows.
_p4_row_cells = [
    # (functional_cell_xml, smoke_cell_xml, total_cell_xml, token_base)
    ('<w:t>139</w:t>', '<w:t xml:space="preserve">32 / 143 / 17</w:t>', '<w:t>\xa0331</w:t>', 'TSR_TOTAL_TCS'),
    ('<w:t>139</w:t>', '<w:t>32 / 143 / 17</w:t>', '<w:t>\xa0331</w:t>', 'TSR_EXECUTED_TCS'),
    ('<w:t>139</w:t>', '<w:t xml:space="preserve">32/ 114 / 0</w:t>', '<w:t>\xa0285</w:t>', 'TSR_PASSED_TCS'),
    ('<w:t>0</w:t>', '<w:t xml:space="preserve">0 / 29 / 17</w:t>', '<w:t>47</w:t>', 'TSR_FAILED_TCS'),
    ('<w:t>0</w:t>', '<w:t>0 / 0 /0</w:t>', '<w:t>\xa00</w:t>', 'TSR_DEFERRED_TCS'),
    ('<w:t>0</w:t>', '<w:t>0 / 0 /0</w:t>', '<w:t>\xa00</w:t>', 'TSR_NA_TCS'),
]
for functional_cell, smoke_cell, total_cell, token_base in _p4_row_cells:
    data = take_one(data, functional_cell, f'<w:t>{{{{{token_base}_FUNCTIONAL}}}}</w:t>', f'{token_base} functional cell')
    data = take_one(data, smoke_cell, f'<w:t>{{{{{token_base}_SMOKE}}}}</w:t>', f'{token_base} smoke cell')
    data = take_one(data, total_cell, f'<w:t>{{{{{token_base}_TOTAL}}}}</w:t>', f'{token_base} total cell')

open(path, 'w', encoding='utf-8').write(data)
print("TSR templatization complete. Length:", len(data))

# ==== Embedded Excel's OLE icon: EMF -> dynamically-labeled PNG ====
# The original icon (media/image4.emf) has a filename caption baked directly
# into the image as vector text -- not editable via XML. Swapped for a PNG
# that the site's build step regenerates on every generation (icon graphic +
# a text label showing "Odessa_Test_Summary_Report_{version}.xlsx", wrapped
# to 2 lines) via an in-browser canvas, then injects into the docx zip by
# overwriting this exact file's bytes. The shape's on-page size is fixed
# here to match that composite's aspect ratio (~1.565:1) since it doesn't
# change between generations, only the version text inside the image does.
_old_shape_style = 'style="width:68.8pt;height:44.65pt"'
_new_shape_style = 'style="width:117.35pt;height:75pt"'
assert data.count(_old_shape_style) == 1, "OLE icon shape style not found in expected form"
data = data.replace(_old_shape_style, _new_shape_style)
open(path, 'w', encoding='utf-8').write(data)

rels_path = 'unpacked/word/_rels/document.xml.rels'
rels_data = open(rels_path, encoding='utf-8').read()
assert rels_data.count('Target="media/image4.emf"') == 1, "OLE icon relationship target not found"
rels_data = rels_data.replace('Target="media/image4.emf"', 'Target="media/image4.png"')
open(rels_path, 'w', encoding='utf-8').write(rels_data)

import os, shutil
_script_dir = os.path.dirname(os.path.abspath(__file__))
os.remove('unpacked/word/media/image4.emf')
shutil.copy(os.path.join(_script_dir, 'tsr_icon_placeholder.png'), 'unpacked/word/media/image4.png')

ct_path = 'unpacked/[Content_Types].xml'
ct_data = open(ct_path, encoding='utf-8').read()
if 'Extension="png"' not in ct_data:
    ct_data = ct_data.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>')
    open(ct_path, 'w', encoding='utf-8').write(ct_data)
print("OLE icon swapped to PNG placeholder (image4.png), shape resized.")

# ==== Embedded Excel package: rename to a predictable placeholder path ====
# Renamed here (build time) to a fixed, greppable path containing a
# "PLACEHOLDER" marker; the site's build step does the FINAL rename to
# "Odessa_Test_Summary_Report_{version}.xlsx" at generation time, once the
# actual release version is known (not available yet at template-build time).
# Doing the bulk of the rename here means the build step only has to find
# and adjust one predictable, already-known path rather than parse rels
# looking for "whatever Microsoft named it originally".
_old_embed_path = 'unpacked/word/embeddings/Microsoft_Excel_Worksheet.xlsx'
_new_embed_filename = 'Odessa_Test_Summary_Report_PLACEHOLDER.xlsx'
_new_embed_path = f'unpacked/word/embeddings/{_new_embed_filename}'
assert os.path.exists(_old_embed_path), "embedded Excel package not found at expected path"
shutil.move(_old_embed_path, _new_embed_path)

rels_data = open(rels_path, encoding='utf-8').read()
_old_embed_target = 'Target="embeddings/Microsoft_Excel_Worksheet.xlsx"'
_new_embed_target = f'Target="embeddings/{_new_embed_filename}"'
assert rels_data.count(_old_embed_target) == 1, "embedded Excel relationship target not found"
rels_data = rels_data.replace(_old_embed_target, _new_embed_target)
open(rels_path, 'w', encoding='utf-8').write(rels_data)
print(f"Embedded Excel package renamed to {_new_embed_filename}.")

# ==== Footer's subject-property content control + docProps/core.xml ====
# The running footer (word/footer1.xml) shows "TIC - Release- PIx.y.z" via a
# Word content control bound to the document's dc:subject property (an XPath-
# bound SDT, not a plain run) -- its cached display text is a completely
# separate literal copy from the cover page's, living in a different file, and
# won't update just because document.xml did. docProps/core.xml's own
# <dc:subject> holds the same value as the property's backing store. Both
# need the identical literal-text treatment as everywhere else.
footer_path = 'unpacked/word/footer1.xml'
footer_data = open(footer_path, encoding='utf-8').read()
_old_subject_run = '<w:t>TIC - Release- PI7.31.3</w:t>'
_new_subject_run = '<w:t>TIC - Release- PI{{CURRENT_RELEASE_VERSION}}</w:t>'
n_footer_subject = footer_data.count(_old_subject_run)
assert n_footer_subject == 2, f"footer1.xml: expected 2 occurrences of the subject SDT content, got {n_footer_subject}"
footer_data = footer_data.replace(_old_subject_run, _new_subject_run)
open(footer_path, 'w', encoding='utf-8').write(footer_data)

core_path = 'unpacked/docProps/core.xml'
core_data = open(core_path, encoding='utf-8').read()
_old_core_subject = '<dc:subject>TIC - Release- PI7.31.3</dc:subject>'
_new_core_subject = '<dc:subject>TIC - Release- PI{{CURRENT_RELEASE_VERSION}}</dc:subject>'
assert core_data.count(_old_core_subject) == 1, "core.xml: dc:subject not found in expected form"
core_data = core_data.replace(_old_core_subject, _new_core_subject)
open(core_path, 'w', encoding='utf-8').write(core_data)
print("Footer + core.xml subject property updated.")
