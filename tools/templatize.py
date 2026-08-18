import re

path = 'unpacked/word/document.xml'
data = open(path, encoding='utf-8').read()

def one(old, new):
    global data
    n = data.count(old)
    assert n == 1, f"expected 1 occurrence, got {n}: {old[:80]!r}"
    data = data.replace(old, new)

# ---- Cover / version tokens ----
one('<w:t>7.30.2</w:t>', '<w:t>{{CD_VERSION}}</w:t>')
one('<w:t>CodeDrop7.30.2</w:t>', '<w:t>CodeDrop{{CD_VERSION}}</w:t>')
one('<w:t>118.7.30.2</w:t>', '<w:t>{{FULL_VERSION}}</w:t>')
# NOTE: this template phrases the two "as part of CD X" sentences differently
# ("...are released as part of CD 7.30.2" for Tasks Completed, vs "...are
# Delivered as part of CD 7.30.2" for Code Drop Defects), so we match on the
# "as part of CD X" tail rather than hardcoding the verb.
n_cd_sentences = len(re.findall(r'as part of CD 7\.30\.2', data))
assert n_cd_sentences == 2, f"expected 2 'as part of CD' sentences, got {n_cd_sentences}"
data = re.sub(r'as part of CD 7\.30\.2', 'as part of CD {{CD_VERSION}}', data)

# ---- Dates ----
n_release_date = data.count('<w:t>August 14, 2026</w:t>')
assert n_release_date == 3, f"expected 3 RELEASE_DATE occurrences, got {n_release_date}"
data = data.replace('<w:t>August 14, 2026</w:t>', '<w:t>{{RELEASE_DATE}}</w:t>')
one('<w:t xml:space="preserve">August 14 - 2026</w:t>', '<w:t xml:space="preserve">{{REV_DATE}}</w:t>')

# ---- Release Details table ----
one('<w:t>4.24.12.47</w:t>', '<w:t>{{FX_VERSION}}</w:t>')
one('<w:t>5.81.2.7423</w:t>', '<w:t>{{PRODUCT_VERSION}}</w:t>')
one('<w:t>Full Release</w:t>', '<w:t>{{RELEASE_TYPE}}</w:t>')
one('<w:t>Odessa Core</w:t>', '<w:t>{{SITE_LABEL}}</w:t>')

one(
    'w14:paraId="3BF050D0" w14:textId="77777777" w:rsidR="00591FC1" w:rsidRPr="00952A74" w:rsidRDefault="00FF61EE" w:rsidP="003E783B"><w:pPr><w:widowControl/><w:autoSpaceDE/><w:autoSpaceDN/><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>Yes</w:t>',
    'w14:paraId="3BF050D0" w14:textId="77777777" w:rsidR="00591FC1" w:rsidRPr="00952A74" w:rsidRDefault="00FF61EE" w:rsidP="003E783B"><w:pPr><w:widowControl/><w:autoSpaceDE/><w:autoSpaceDN/><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>{{HOTFIX}}</w:t>',
)

# ==== Business Configuration (table <-> "No RBS Impact") ====
# second occurrence is the real body heading (first is the TOC entry)
_bc_idx1 = data.find('Business Configuration</w:t>')
idx = data.find('Business Configuration</w:t>', _bc_idx1 + 1)
tbl_start = data.find('<w:tbl>', idx)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
table = data[tbl_start:tbl_end]
rows = re.findall(r'<w:tr .*?</w:tr>', table, re.S)
assert len(rows) == 2, f"expected header+1 row, got {len(rows)}"
header, row1 = rows[0], rows[1]
prefix = table[:table.find(header)]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC03-2245</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace('<w:t xml:space="preserve">PI 7.30.2 | RBS Changes</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row = new_row.replace('<w:t>RBS</w:t>', '<w:t>{{ROW_TYPE}}</w:t>')
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_TYPE}}'):
    assert tok in new_row, f"BIZCONFIG row: {tok} substitution silently no-op'd"
templated_row = '<!--ROW:BIZCONFIG-->' + new_row + '<!--/ROW:BIZCONFIG-->'
new_table = prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:BIZCONFIG:TABLE_START-->' + new_table + '<!--BLOCK:BIZCONFIG:TABLE_END-->'
# No naturally-occurring "NA" alternative exists for this section in the source
# doc (Business Config always ships with real content) -- hand-authored, as before.
na_para = '<w:p w:rsidRPr="00860B61" w:rsidR="001C6D58" w:rsidP="007E756C" w:rsidRDefault="001C6D58" w14:paraId="62FB2601" w14:textId="0F9C7601"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>No RBS Impact</w:t></w:r></w:p>'
na_block = '<!--BLOCK:BIZCONFIG:NA_START-->' + na_para + '<!--BLOCK:BIZCONFIG:NA_END-->'
assert data.count(table) == 1
data = data.replace(table, table_block + na_block)

# ==== Code Drop Defects (bullet + table <-> NA) ====
# Do this BEFORE Requirements, so we can reuse its pristine table structure
# (Requirements has no example table of its own in this base doc -- see below).
cdd_seg_start = data.find('<w:p w14:paraId="39595F28"')
tbl_start = data.find('<w:tbl>', cdd_seg_start)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
cdd_segment = data[cdd_seg_start:tbl_end]
cdd_source_table = cdd_segment[cdd_segment.find('<w:tbl>'):]  # save pristine copy for Requirements

rows = re.findall(r'<w:tr .*?</w:tr>', cdd_segment, re.S)
header, row1 = rows[0], rows[1]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC03-2170</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace('<w:t xml:space="preserve">Same-day exposure display incorrect - TIC03-2170</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row = new_row.replace('<w:t>Critical</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_row = re.sub(r'<w:t>No</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_row)
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_PRIORITY}}', '{{ROW_DATAFIX}}'):
    assert tok in new_row, f"CDD row: {tok} substitution silently no-op'd"
templated_row = '<!--ROW:CDD-->' + new_row + '<!--/ROW:CDD-->'
bullet_end = cdd_segment.find('<w:tbl>')
bullet_para = cdd_segment[:bullet_end]
# Reduce "Below Defects are Delivered as part of CD..." from 11pt to 10pt.
assert bullet_para.count('<w:sz w:val="22"/>') == 2, "expected exactly 2 sz=22 runs in CDD bullet paragraph"
bullet_para = bullet_para.replace('<w:sz w:val="22"/>', '<w:sz w:val="20"/>')
# Shrink the blank spacer line before the table from its default ~10.5pt down
# to 5pt, so there's still a visible gap but a much smaller one.
_cdd_spacer_old = '<w:p w14:paraId="5D0CB30A" w14:textId="77777777" w:rsidR="002216C2" w:rsidRPr="002216C2" w:rsidRDefault="002216C2" w:rsidP="002216C2"/>'
_cdd_spacer_new = '<w:p w14:paraId="5D0CB30A" w14:textId="77777777" w:rsidR="002216C2" w:rsidRPr="002216C2" w:rsidRDefault="002216C2" w:rsidP="002216C2"><w:pPr><w:rPr><w:sz w:val="10"/><w:szCs w:val="10"/></w:rPr></w:pPr></w:p>'
assert bullet_para.count(_cdd_spacer_old) == 1, "CDD spacer paragraph not found in expected form"
bullet_para = bullet_para.replace(_cdd_spacer_old, _cdd_spacer_new)
table_part = cdd_segment[bullet_end:]
tbl_prefix = table_part[:table_part.find(header)]
new_table = tbl_prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:CDD:TABLE_START-->' + bullet_para + new_table + '<!--BLOCK:CDD:TABLE_END-->'
# No naturally-occurring "NA" alternative for CDD either -- hand-authored.
na_para = '<w:p w:rsidRPr="00860B61" w:rsidR="001C6D58" w:rsidP="007E756C" w:rsidRDefault="001C6D58" w14:paraId="62FB2603" w14:textId="0F9C7603"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:CDD:NA_START-->' + na_para + '<!--BLOCK:CDD:NA_END-->'
assert data.count(cdd_segment) == 1
data = data.replace(cdd_segment, table_block + na_block)

# ==== Requirements (bullet + table <-> NA) ====
# UNLIKE the previous base template, this doc's Requirements section ships as
# a bare "NA" paragraph with no example table -- there's nothing to derive a
# row template from directly. We synthesize the block by cloning the Code
# Drop Defects table structure (same 5-column schema: SlNo/Key/Summary/
# Priority/Datafix -- confirmed against app.js SECTION_CONFIG) and re-minting
# fresh paraIds so they don't collide with the CDD copy. The genuine NA
# paragraph in this doc becomes the real BLOCK:REQ:NA_START content.
#
# Requirements doesn't need a Datafix column (per request), so after cloning
# CDD's 5-column structure, the 5th column is dropped from both the header
# and the row template, and its width (1018 dxa) is folded into Summary so
# the table still totals 9926 dxa, matching every other ticket table.
req_rows = re.findall(r'<w:tr .*?</w:tr>', cdd_source_table, re.S)
req_header, req_row1 = req_rows[0], req_rows[1]
req_prefix = cdd_source_table[:cdd_source_table.find(req_header)]

def drop_last_cell(row_xml, label):
    cells = re.findall(r'<w:tc>.*?</w:tc>', row_xml, re.S)
    assert len(cells) == 5, f"{label}: expected 5 cells before dropping Datafix, got {len(cells)}"
    last_cell = cells[-1]
    assert row_xml.count(last_cell) == 1, f"{label}: last cell isn't uniquely identifiable"
    return row_xml.replace(last_cell, '', 1)

req_header = drop_last_cell(req_header, 'REQ header')
req_row1 = drop_last_cell(req_row1, 'REQ row1')
# Fold the dropped column's width into Summary (both header and prefix's
# tblGrid need the same 4-column layout: 804/1497/6581/1044).
req_prefix = req_prefix.replace(
    '<w:tblGrid><w:gridCol w:w="804"/><w:gridCol w:w="1497"/><w:gridCol w:w="5563"/><w:gridCol w:w="1044"/><w:gridCol w:w="1018"/></w:tblGrid>',
    '<w:tblGrid><w:gridCol w:w="804"/><w:gridCol w:w="1497"/><w:gridCol w:w="6581"/><w:gridCol w:w="1044"/></w:tblGrid>',
    1,
)
req_header = req_header.replace('<w:tcW w:w="5563" w:type="dxa"/>', '<w:tcW w:w="6581" w:type="dxa"/>', 1)
req_row1 = req_row1.replace('<w:tcW w:w="5563" w:type="dxa"/>', '<w:tcW w:w="6581" w:type="dxa"/>', 1)

new_req_row = req_row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_req_row = new_req_row.replace('<w:t>TIC03-2170</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_req_row = new_req_row.replace('<w:t xml:space="preserve">Same-day exposure display incorrect - TIC03-2170</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_req_row = new_req_row.replace('<w:t>Critical</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_PRIORITY}}'):
    assert tok in new_req_row, f"REQ row: {tok} substitution silently no-op'd"
assert '{{ROW_DATAFIX}}' not in new_req_row, "REQ row: Datafix column should have been dropped"
new_req_row = re.sub(r'w14:paraId="([0-9A-Fa-f]{8})"', lambda m: 'w14:paraId="RQ' + m.group(1)[2:] + '"', new_req_row)
templated_req_row = '<!--ROW:REQ-->' + new_req_row + '<!--/ROW:REQ-->'
new_req_table = req_prefix + req_header + templated_req_row + '</w:tbl>'
# Synthesize the intro bullet sentence to match the Tasks Completed / CDD style,
# since Requirements has no such sentence in the source doc.
req_bullet_para = '<w:p w14:paraId="62FB2610" w14:textId="0F9C7610" w:rsidR="001C6D58" w:rsidRDefault="001C6D58"><w:pPr><w:rPr><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="20"/></w:rPr><w:t xml:space="preserve">Below requirements were released as part of CD {{CD_VERSION}} - </w:t></w:r></w:p>'
# Matches the empty spacer paragraph that CDD/Tasks Completed retain naturally
# from the source doc between their intro sentence and their table -- without
# it, Requirements' table sits flush against the sentence while every other
# section has a visible gap.
req_spacer_para = '<w:p w14:paraId="62FB2611" w14:textId="77777777" w:rsidR="001C6D58" w:rsidRPr="001C6D58" w:rsidRDefault="001C6D58" w:rsidP="001C6D58"><w:pPr><w:rPr><w:sz w:val="10"/><w:szCs w:val="10"/></w:rPr></w:pPr></w:p>'
table_block = '<!--BLOCK:REQ:TABLE_START-->' + req_bullet_para + req_spacer_para + new_req_table + '<!--BLOCK:REQ:TABLE_END-->'

req_na_para = '<w:p w14:paraId="146E8121" w14:textId="77777777" w:rsidR="00AD2C1D" w:rsidRDefault="00BE259B"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:REQ:NA_START-->' + req_na_para + '<!--BLOCK:REQ:NA_END-->'
assert data.count(req_na_para) == 1
data = data.replace(req_na_para, table_block + na_block)

# ==== Migration / E2E (free text) ====
one(
    'w14:paraId="17A35AFF" w14:textId="56872CB9" w:rsidR="001C6D58" w:rsidRPr="004B4CA7" w:rsidRDefault="001C6D58" w:rsidP="008B34CA"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="17A35AFF" w14:textId="56872CB9" w:rsidR="001C6D58" w:rsidRPr="004B4CA7" w:rsidRDefault="001C6D58" w:rsidP="008B34CA"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>{{MIGRATION_TEXT}}</w:t>',
)
one(
    'w14:paraId="5DBFEB03" w14:textId="77777777" w:rsidR="00553365" w:rsidRPr="004B4CA7" w:rsidRDefault="001C6D58" w:rsidP="004B4CA7"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="5DBFEB03" w14:textId="77777777" w:rsidR="00553365" w:rsidRPr="004B4CA7" w:rsidRDefault="001C6D58" w:rsidP="004B4CA7"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>{{E2E_TEXT}}</w:t>',
)

# ==== Tasks Completed (real table this time; needs a fabricated NA alternative) ====
# UNLIKE the previous base template (where Tasks Completed was NA and its table
# had to be borrowed from CDD), this doc's Tasks Completed section ships with
# its own real table. So this time it's TASKS that needs a hand-authored NA
# block (mirroring how BIZCONFIG/CDD got theirs above), and the table can be
# templatized directly from its own content.
tasks_seg_start = data.find('<w:p w14:paraId="0A1C93E5"')
tbl_start = data.find('<w:tbl>', tasks_seg_start)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
tasks_segment = data[tasks_seg_start:tbl_end]
rows = re.findall(r'<w:tr .*?</w:tr>', tasks_segment, re.S)
assert len(rows) == 9, f"expected header+8 rows, got {len(rows)}"
header, row1 = rows[0], rows[1]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC03-2220</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace(
    '<w:t>Canned GL Account Detail report errors for Entity Type Asset Value Adjustment</w:t>',
    '<w:t>{{ROW_SUMMARY}}</w:t>',
)
new_row = new_row.replace('<w:t>Critical</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_row = re.sub(r'<w:t>Yes</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_row)
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_PRIORITY}}', '{{ROW_DATAFIX}}'):
    assert tok in new_row, f"TASKS row: {tok} substitution silently no-op'd"
templated_row = '<!--ROW:TASKS-->' + new_row + '<!--/ROW:TASKS-->'
bullet_end = tasks_segment.find('<w:tbl>')
bullet_para = tasks_segment[:bullet_end]
# Reduce "Below tasks and Sub Tasks are released as part of CD..." from 11pt to 10pt.
assert bullet_para.count('<w:sz w:val="22"/>') == 2, "expected exactly 2 sz=22 runs in Tasks bullet paragraph"
bullet_para = bullet_para.replace('<w:sz w:val="22"/>', '<w:sz w:val="20"/>')
# Shrink the blank spacer line before the table from its default ~10.5pt down
# to 5pt, so there's still a visible gap but a much smaller one.
_tasks_spacer_old = '<w:p w14:paraId="05626A9F" w14:textId="77777777" w:rsidR="001C6D58" w:rsidRDefault="001C6D58" w:rsidP="001C6D58"/>'
_tasks_spacer_new = '<w:p w14:paraId="05626A9F" w14:textId="77777777" w:rsidR="001C6D58" w:rsidRDefault="001C6D58" w:rsidP="001C6D58"><w:pPr><w:rPr><w:sz w:val="10"/><w:szCs w:val="10"/></w:rPr></w:pPr></w:p>'
assert bullet_para.count(_tasks_spacer_old) == 1, "Tasks spacer paragraph not found in expected form"
bullet_para = bullet_para.replace(_tasks_spacer_old, _tasks_spacer_new)
table_part = tasks_segment[bullet_end:]
tbl_prefix = table_part[:table_part.find(header)]
new_table = tbl_prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:TASKS:TABLE_START-->' + bullet_para + new_table + '<!--BLOCK:TASKS:TABLE_END-->'
na_para = '<w:p w:rsidR="005D574F" w:rsidP="00BE7B2D" w:rsidRDefault="005D574F" w14:paraId="62FB2604" w14:textId="0F9C7604"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:TASKS:NA_START-->' + na_para + '<!--BLOCK:TASKS:NA_END-->'
assert data.count(tasks_segment) == 1
data = data.replace(tasks_segment, table_block + na_block)

# ==== Technical Configuration (free text) ====
# This doc formats these inline ("label - value" split across two runs) rather
# than label-newline-value like the previous base template, and the two
# fields aren't even internally consistent with each other (AppSettings has
# the dash in the label run; WebConfig has it baked into the value run). We
# anchor on paraId and touch only the value run so we don't disturb whichever
# formatting convention each one uses.
# Also drops the label runs from 12pt (sz=24) to 11pt (sz=22) per request.
one(
    'w14:paraId="42D80303" w14:textId="1C101F18" w:rsidR="00FD7163" w:rsidRPr="00520FCB" w:rsidRDefault="001C6D58" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t xml:space="preserve">AppSettings.Config change(s) - </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="42D80303" w14:textId="1C101F18" w:rsidR="00FD7163" w:rsidRPr="00520FCB" w:rsidRDefault="001C6D58" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">AppSettings.Config change(s) - </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{{APPSETTINGS_TEXT}}</w:t>',
)
one(
    'w14:paraId="75E97C55" w14:textId="31858B4D" w:rsidR="00CE257F" w:rsidRDefault="007E756C" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>Web Config change(s)</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>- NA</w:t>',
    'w14:paraId="75E97C55" w14:textId="31858B4D" w:rsidR="00CE257F" w:rsidRDefault="007E756C" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>Web Config change(s)</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">- {{WEBCONFIG_TEXT}}</w:t>',
)

# ==== Release Request Packages (fixed 6 rows) ====
# Anchor on paraId+textId of each value paragraph (not the <w:tr>, which also
# happens to carry a w14:paraId -- this template's rows have an extra <w:pPr>
# ahead of the run compared to the previous base template).
rrp_edits = [
    ('1C47DA84', '77777777', 'Yes', 'LESSOR_PORTAL'),
    ('2584BB05', '77777777', 'Yes', 'WINDOWS_SERVICE'),
    ('44569584', '77777777', 'Yes', 'WEB_API'),
    ('62088FC2', '77777777', 'Yes', 'DATABASE'),
    ('698015AC', '6F7443F5', 'No', 'REPORTS'),
    ('515517E6', '77777777', 'No', 'APPSETTINGS_CONFIG'),
]
for pid, tid, val, token in rrp_edits:
    old = f'<w:p w14:paraId="{pid}" w14:textId="{tid}"'
    n = data.count(old)
    assert n == 1, f"expected 1 occurrence for {pid}, got {n}"
    p_idx = data.find(old)
    p_end = data.find('</w:p>', p_idx)
    para = data[p_idx:p_end]
    new_para = para.replace(f'<w:t>{val}</w:t>', f'<w:t>{{{{RRP_{token}}}}}</w:t>')
    assert new_para != para, f"no {val!r} value found in RRP paragraph {pid}"
    data = data[:p_idx] + new_para + data[p_end:]

# ==== Normalize fonts/sizes/widths across the ticket tables ====
# The base doc's Business Configuration / Requirements / Tasks Completed /
# Code Drop Defects tables were each authored independently (evidently at
# different times), so they disagree on font (Calibri vs "Aptos Narrow"),
# size (10pt/10.5pt/11pt), and column proportions -- invisible in some
# renderers that silently substitute a fallback font, but visibly
# inconsistent in Word itself. Bring them all to a single standard: Calibri,
# 10pt, and matching column widths for the columns they share (SlNo/Issue
# key line up the same regardless of which section you're looking at).

def normalize_table_font(table_xml, table_name):
    n_aptos = table_xml.count('Aptos Narrow')
    n_sz22 = table_xml.count('<w:sz w:val="22"/>')
    if n_aptos or n_sz22:
        table_xml = table_xml.replace('Aptos Narrow', 'Calibri').replace('<w:sz w:val="22"/>', '<w:sz w:val="20"/>')
    return table_xml

def get_table(marker_start):
    idx = data.find(marker_start)
    assert idx != -1, f"marker not found: {marker_start}"
    tbl_start = data.find('<w:tbl>', idx)
    tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
    return data[tbl_start:tbl_end]

# --- Business Configuration: has Calibri already, but sizes were never set
# explicitly (silently inheriting an ambiguous ~10.5pt default) -- pin to 10pt,
# and widen/rebalance columns to line up with the other ticket tables below.
biz_table = get_table('BLOCK:BIZCONFIG:TABLE_START')
n_biz_szcs21 = biz_table.count('<w:szCs w:val="21"/>')
assert n_biz_szcs21 == 15, f"expected 15 szCs=21 runs in BizConfig table, got {n_biz_szcs21}"
new_biz_table = biz_table.replace('<w:szCs w:val="21"/>', '<w:sz w:val="20"/><w:szCs w:val="20"/>')
biz_widths_old = ['924', '1409', '6516', '1079']
biz_widths_new = ['804', '1497', '6546', '1079']  # SlNo/IssueKey widths now match REQ/TASKS/CDD below
for old_w, new_w in zip(biz_widths_old, biz_widths_new):
    n = new_biz_table.count(f'w:w="{old_w}"')
    assert n >= 1, f"BizConfig: width {old_w} not found"
    new_biz_table = new_biz_table.replace(f'w:w="{old_w}"', f'w:w="{new_w}"')
# Row heights: standardize on 227 dxa (0.4cm) for both header and data rows --
# confirmed against Word's own "single line, autofit" reported height -- so
# every ticket table's rows are not just proportioned the same but exactly
# the same height too.
SINGLE_LINE_ROW_HEIGHT = '227'  # 0.4cm
biz_heights_old = ['240', '237']
for old_h in biz_heights_old:
    n = new_biz_table.count(f'<w:trHeight w:val="{old_h}"/>')
    assert n == 1, f"BizConfig: trHeight {old_h} not found exactly once, got {n}"
    new_biz_table = new_biz_table.replace(f'<w:trHeight w:val="{old_h}"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
assert data.count(biz_table) == 1
data = data.replace(biz_table, new_biz_table)

# --- Requirements / Code Drop Defects: already share identical column widths
# (REQ was cloned from CDD's structure) and just need the font/size fix, plus
# the same row-height standardization as the other two tables.
for marker, label in [('BLOCK:REQ:TABLE_START', 'Requirements'), ('BLOCK:CDD:TABLE_START', 'CDD')]:
    t = get_table(marker)
    new_t = normalize_table_font(t, label)
    assert new_t != t, f"{label}: expected font/size normalization to change something"
    for old_h in ('331', '183'):
        n = new_t.count(f'<w:trHeight w:val="{old_h}"/>')
        assert n == 1, f"{label}: trHeight {old_h} not found exactly once, got {n}"
        new_t = new_t.replace(f'<w:trHeight w:val="{old_h}"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
    assert data.count(t) == 1
    data = data.replace(t, new_t)

# --- Tasks Completed: needs font/size fix AND a column-width rebalance to
# match Requirements/CDD's proportions (its table was authored separately
# with its own, different widths).
tasks_table = get_table('BLOCK:TASKS:TABLE_START')
new_tasks_table = normalize_table_font(tasks_table, 'Tasks')
tasks_widths_old = ['666', '1314', '6173', '888', '844']
tasks_widths_new = ['804', '1497', '5563', '1044', '1018']  # matches REQ/CDD exactly
for old_w, new_w in zip(tasks_widths_old, tasks_widths_new):
    n = new_tasks_table.count(f'w:w="{old_w}"')
    assert n >= 1, f"Tasks: width {old_w} not found"
    new_tasks_table = new_tasks_table.replace(f'w:w="{old_w}"', f'w:w="{new_w}"')
# The above only fixed gridCol (and the 2 columns whose per-cell tcW happened
# to carry an explicit width). SlNo/Priority/Datafix's per-cell tcW were
# independently "0" (auto) in the pristine source -- a real authoring
# inconsistency between gridCol and tcW, not something the literal-value
# replace above could have caught. Word renders columns from tcW when
# present, so those 3 columns were effectively auto-sized regardless of the
# gridCol fix, which is what made this table visibly narrower than the
# others. Replace all 6 occurrences (3 columns x header+data row) in order.
_tasks_zero_tcw = '<w:tcW w:w="0" w:type="auto"/>'
n_tasks_zero = new_tasks_table.count(_tasks_zero_tcw)
assert n_tasks_zero == 6, f"Tasks: expected 6 zero-width tcW cells (SlNo/Priority/Datafix x 2 rows), got {n_tasks_zero}"
_tasks_zero_fill = ['804', '1044', '1018', '804', '1044', '1018']  # SlNo/Priority/Datafix, header then data row
_parts = new_tasks_table.split(_tasks_zero_tcw)
assert len(_parts) == n_tasks_zero + 1
new_tasks_table = _parts[0]
for i, fill in enumerate(_tasks_zero_fill):
    new_tasks_table += f'<w:tcW w:w="{fill}" w:type="dxa"/>' + _parts[i + 1]
# Tasks was also missing tblLayout=fixed entirely (CDD/REQ both have it),
# meaning Word could auto-fit columns to content instead of respecting the
# declared widths above -- belt-and-suspenders alongside the tcW fix.
# (tblLayout must come after tblBorders per the OOXML schema's required
# child-element order within tblPr, not directly after tblW.)
assert new_tasks_table.count('</w:tblBorders><w:tblLook') == 1, "Tasks: tblPr anchor for tblLayout insert not found"
new_tasks_table = new_tasks_table.replace(
    '</w:tblBorders><w:tblLook',
    '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblLook',
    1,
)
# Row heights: same 0.4cm standardization as the other three tables.
tasks_heights_old = ['311', '608']
for old_h in tasks_heights_old:
    n = new_tasks_table.count(f'<w:trHeight w:val="{old_h}"/>')
    assert n == 1, f"Tasks: trHeight {old_h} not found exactly once, got {n}"
    new_tasks_table = new_tasks_table.replace(f'<w:trHeight w:val="{old_h}"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
assert data.count(tasks_table) == 1
data = data.replace(tasks_table, new_tasks_table)

# --- Header color: the Release Request Packages and Environment Summary
# tables' headers reference a theme color (accent1) that resolves to a
# visibly different, lighter blue than the literal navy every other table
# header uses. Pin both to the same literal color for a consistent look.
_old_header_fill = '<w:shd w:val="clear" w:color="auto" w:fill="156082" w:themeFill="accent1"/>'
_new_header_fill = '<w:shd w:val="clear" w:color="auto" w:fill="104861"/>'
n_header_fill = data.count(_old_header_fill)
assert n_header_fill == 8, f"expected 8 occurrences (RRP + Environment Summary headers), got {n_header_fill}"
data = data.replace(_old_header_fill, _new_header_fill)

# ==== Environment Summary table column widths ====
# Requested: first column (Environment) = 2.2cm, all other columns
# (Core / Partner Portal / Customer Portal / API) = 4cm each.
_es_idx1 = data.find('Environment Summary')
_es_idx2 = data.find('Environment Summary', _es_idx1 + 1)
_es_tbl_start = data.find('<w:tbl>', _es_idx2)
_es_tbl_end = data.find('</w:tbl>', _es_tbl_start) + len('</w:tbl>')
es_table = data[_es_tbl_start:_es_tbl_end]
# This table is (uniquely, among every table in the document) set up with
# floating/anchored positioning (tblpPr, absolute vertical offset from its
# anchor paragraph) rather than normal inline flow. That's fragile: any
# upstream change that shifts pagination -- like the heading font-size
# change earlier this round -- can make the "Environment Summary" heading
# itself render beside the table instead of above it, since the table no
# longer reliably tracks the heading's actual position. Converting it to a
# plain inline table (like every other table here) makes it immune to this
# class of bug regardless of what else changes upstream.
_es_floating_props = '<w:tblpPr w:leftFromText="180" w:rightFromText="180" w:vertAnchor="text" w:horzAnchor="margin" w:tblpXSpec="center" w:tblpY="164"/>'
assert es_table.count(_es_floating_props) == 1, "Environment Summary: floating tblpPr not found"
es_table_inline = es_table.replace(_es_floating_props, '')
FIRST_COL_DXA = round(2.2 * 1440 / 2.54)   # 2.2cm -> 1247 dxa
OTHER_COL_DXA = round(4 * 1440 / 2.54)     # 4cm   -> 2268 dxa
n_first = es_table_inline.count('w:w="1408"')
n_other = es_table_inline.count('w:w="2551"')
assert n_first == 5, f"expected 5 occurrences (1 gridCol + 4 rows) of the first column width, got {n_first}"
assert n_other == 20, f"expected 20 occurrences (4 gridCol + 4 rows x 4 cols) of the other column width, got {n_other}"
new_es_table = es_table_inline.replace('w:w="1408"', f'w:w="{FIRST_COL_DXA}"').replace('w:w="2551"', f'w:w="{OTHER_COL_DXA}"')
new_total = FIRST_COL_DXA + 4 * OTHER_COL_DXA
new_es_table = new_es_table.replace('<w:tblW w:w="11612" w:type="dxa"/>', f'<w:tblW w:w="{new_total}" w:type="dxa"/>', 1)
# Header row height (188 dxa) didn't match the 227 dxa (0.4cm) standard used
# for every other table's header/single-line rows. The data rows (Staging/
# UAT/Production) genuinely need more height to fit their wrapped 2-line
# URLs, so only the header row is touched here.
assert new_es_table.count('<w:trHeight w:val="188"/>') == 1, "Environment Summary: header trHeight not found"
new_es_table = new_es_table.replace('<w:trHeight w:val="188"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
# The header row's cells also carry explicit top/bottom padding (80 dxa each)
# that none of the ticket tables' headers have -- that padding adds directly
# to the rendered row height regardless of trHeight, so setting trHeight
# alone wasn't enough to make it visually match. Scoped to just the header
# row (not the data rows, which keep their padding for the wrapped URLs).
es_rows = re.findall(r'<w:tr .*?</w:tr>', new_es_table, re.S)
es_header = es_rows[0]
_es_header_padded_tcmar = '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar>'
_es_header_flat_tcmar = '<w:tcMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar>'
n_es_header_tcmar = es_header.count(_es_header_padded_tcmar)
assert n_es_header_tcmar == 5, f"Environment Summary header: expected 5 padded tcMar cells, got {n_es_header_tcmar}"
new_es_header = es_header.replace(_es_header_padded_tcmar, _es_header_flat_tcmar)
assert new_es_table.count(es_header) == 1
new_es_table = new_es_table.replace(es_header, new_es_header)
assert data.count(es_table) == 1
data = data.replace(es_table, new_es_table)

# ==== Document Revision History table: drop named style, go fully explicit ====
# This table is the only one in the document that relies on a named Word
# table style ("ListTable4-Accent4") instead of fully explicit, self-contained
# formatting like every other table here. That's not just a cosmetic
# difference -- Word's own conditional "first row" style formatting appears to
# take priority over inline cell shading for this style family in practice,
# so simply adding inline w:shd to the header cells (tried first) rendered
# correctly in LibreOffice but NOT in real Microsoft Word. Removing the style
# reference entirely and giving it the same explicit tblBorders every other
# table uses sidesteps that precedence question altogether -- there's no
# style left to compete with the inline formatting.
_drh_idx1 = data.find('Document Revision History')
_drh_idx2 = data.find('Document Revision History', _drh_idx1 + 1)
_drh_tbl_start = data.find('<w:tbl>', _drh_idx2)
_drh_tbl_end = data.find('</w:tbl>', _drh_tbl_start) + len('</w:tbl>')
drh_table = data[_drh_tbl_start:_drh_tbl_end]

_drh_old_tblpr = '<w:tblPr><w:tblStyle w:val="ListTable4-Accent4"/><w:tblW w:w="5000" w:type="pct"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
_drh_new_tblpr = '<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders><w:top w:val="single" w:sz="6" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="6" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="6" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="6" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="6" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="6" w:space="0" w:color="auto"/></w:tblBorders><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
assert drh_table.count(_drh_old_tblpr) == 1, "Document Revision History: tblPr not found in expected form"
new_drh_table = drh_table.replace(_drh_old_tblpr, _drh_new_tblpr)

drh_rows = re.findall(r'<w:tr .*?</w:tr>', new_drh_table, re.S)
drh_header = drh_rows[0]
drh_header_cells_old = [
    '<w:tcPr><w:cnfStyle w:val="001000000000" w:firstRow="0" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:oddVBand="0" w:evenVBand="0" w:oddHBand="0" w:evenHBand="0" w:firstRowFirstColumn="0" w:firstRowLastColumn="0" w:lastRowFirstColumn="0" w:lastRowLastColumn="0"/><w:tcW w:w="1000" w:type="pct"/></w:tcPr>',
    '<w:tcPr><w:tcW w:w="2000" w:type="pct"/></w:tcPr>',
    '<w:tcPr><w:tcW w:w="579" w:type="pct"/></w:tcPr>',
    '<w:tcPr><w:tcW w:w="1421" w:type="pct"/></w:tcPr>',
]
new_drh_header = drh_header
for old_cell in drh_header_cells_old:
    n = new_drh_header.count(old_cell)
    assert n == 1, f"Document Revision History header: expected 1 occurrence of {old_cell[:50]!r}, got {n}"
    new_cell = old_cell.replace('</w:tcPr>', '<w:shd w:val="clear" w:color="auto" w:fill="104861"/></w:tcPr>')
    new_drh_header = new_drh_header.replace(old_cell, new_cell)
assert new_drh_table.count(drh_header) == 1
new_drh_table = new_drh_table.replace(drh_header, new_drh_header)
assert data.count(drh_table) == 1
data = data.replace(drh_table, new_drh_table)

# ==== Decorative graphics: wrapThrough -> wrapNone ====
# Two cover-page decorative elements ("Group 7" and "Picture 4" -- the logo
# graphic and an accent shape) were set to wrapThrough/bothSides, meaning
# body text is allowed to flow around them. These are purely cosmetic and
# were never meant to interact with body text at all (every other decorative
# element in the doc already uses wrapNone) -- but because wrapThrough
# elements position relative to their anchor paragraph, any upstream content
# change that shifts pagination (like the heading-size or row-height fixes
# earlier this session) can cause a completely unrelated heading elsewhere in
# the document to land in these shapes' wrap zone and render squeezed beside
# them instead of at full width. Switching both to wrapNone removes that
# entire class of fragility regardless of what else changes upstream.
import re as _re
_wrap_through_pattern = _re.compile(r'<wp:wrapThrough wrapText="bothSides">.*?</wp:wrapThrough>', _re.S)
_wrap_matches = _wrap_through_pattern.findall(data)
assert len(_wrap_matches) == 2, f"expected exactly 2 wrapThrough decorative elements, got {len(_wrap_matches)}"
for _old_wrap in _wrap_matches:
    assert data.count(_old_wrap) == 1
    data = data.replace(_old_wrap, '<wp:wrapNone/>')

open(path, 'w', encoding='utf-8').write(data)
print("Templatization complete. Length:", len(data))

# ==== Heading2 style: 16pt -> 14pt ====
# Every major section heading (Business Configuration, Requirements, Migration,
# E2E Scenarios, Tasks Completed, Code Drop Defects, Release Details,
# Environment Summary, Technical Configuration, Release Request Package(s))
# uses the same "Heading2" paragraph style, so this is edited once at the
# style level rather than per-heading -- keeps them all consistent with each
# other, which is the same standard applied to the tables all session.
styles_path = 'unpacked/word/styles.xml'
styles_data = open(styles_path, encoding='utf-8').read()
_old_heading2_sz = '<w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading3"'
_new_heading2_sz = '<w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading3"'
assert styles_data.count(_old_heading2_sz) == 1, "Heading2 style sz=32 anchor not found"
styles_data = styles_data.replace(_old_heading2_sz, _new_heading2_sz)
open(styles_path, 'w', encoding='utf-8').write(styles_data)
print("Heading2 style updated to 14pt.")
