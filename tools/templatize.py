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
# NOTE: this template phrases the three "as part of CD X" sentences differently
# ("...are released as part of CD 7.30.2" for Requirements/Tasks Completed, vs
# "...are Delivered as part of CD 7.30.2" for Code Drop Defects), so we match
# on the "as part of CD X" tail rather than hardcoding the verb.
n_cd_sentences = len(re.findall(r'as part of CD 7\.30\.2', data))
assert n_cd_sentences == 3, f"expected 3 'as part of CD' sentences, got {n_cd_sentences}"
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
# The base doc now ships Requirements with a genuine example table of its own
# (2 rows, 4 columns: SlNo/Key/Summary/Priority -- no Datafix), so this now
# extracts it directly rather than synthesizing from Code Drop Defects.
req_seg_start = data.find('<w:p w14:paraId="080641D0"')
req_tbl_start = data.find('<w:tbl>', req_seg_start)
req_tbl_end = data.find('</w:tbl>', req_tbl_start) + len('</w:tbl>')
req_segment = data[req_seg_start:req_tbl_end]

req_rows_found = re.findall(r'<w:tr .*?</w:tr>', req_segment, re.S)
req_header, req_row1 = req_rows_found[0], req_rows_found[1]
new_req_row = req_row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_req_row = new_req_row.replace('<w:t>TIC03-2220</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_req_row = new_req_row.replace(
    '<w:t>Canned GL Account Detail report errors for Entity Type Asset Value Adjustment</w:t>',
    '<w:t>{{ROW_SUMMARY}}</w:t>',
)
new_req_row = new_req_row.replace('<w:t>Critical</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_PRIORITY}}'):
    assert tok in new_req_row, f"REQ row: {tok} substitution silently no-op'd"
new_req_row = re.sub(r'w14:paraId="([0-9A-Fa-f]{8})"', lambda m: 'w14:paraId="RQ' + m.group(1)[2:] + '"', new_req_row)
templated_req_row = '<!--ROW:REQ-->' + new_req_row + '<!--/ROW:REQ-->'

req_bullet_end = req_segment.find('<w:tbl>')
req_bullet_para = req_segment[:req_bullet_end]
# Reduce "Below requirements are released as part of CD..." from 11pt to 10pt,
# matching the same treatment CDD/Tasks Completed already get.
assert req_bullet_para.count('<w:sz w:val="22"/>') == 2, "expected exactly 2 sz=22 runs in REQ bullet paragraph"
req_bullet_para = req_bullet_para.replace('<w:sz w:val="22"/>', '<w:sz w:val="20"/>')
# Shrink the blank spacer line before the table from its default ~10.5pt down
# to 5pt, matching CDD/Tasks Completed.
_req_spacer_old = '<w:p w14:paraId="381B3D2A" w14:textId="77777777" w:rsidR="005D08C4" w:rsidRPr="005D08C4" w:rsidRDefault="005D08C4" w:rsidP="005D08C4"/>'
_req_spacer_new = '<w:p w14:paraId="381B3D2A" w14:textId="77777777" w:rsidR="005D08C4" w:rsidRPr="005D08C4" w:rsidRDefault="005D08C4" w:rsidP="005D08C4"><w:pPr><w:rPr><w:sz w:val="10"/><w:szCs w:val="10"/></w:rPr></w:pPr></w:p>'
assert req_bullet_para.count(_req_spacer_old) == 1, "REQ spacer paragraph not found in expected form"
req_bullet_para = req_bullet_para.replace(_req_spacer_old, _req_spacer_new)

req_table_part = req_segment[req_bullet_end:]
req_tbl_prefix = req_table_part[:req_table_part.find(req_header)]
new_req_table = req_tbl_prefix + req_header + templated_req_row + '</w:tbl>'
table_block = '<!--BLOCK:REQ:TABLE_START-->' + req_bullet_para + new_req_table + '<!--BLOCK:REQ:TABLE_END-->'
# No naturally-occurring "NA" alternative for Requirements either (same as
# CDD/Tasks) -- hand-authored, with a fresh paraId that doesn't collide.
req_na_para = '<w:p w14:paraId="62FB2602" w14:textId="0F9C7602" w:rsidR="001C6D58" w:rsidRDefault="001C6D58"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:REQ:NA_START-->' + req_na_para + '<!--BLOCK:REQ:NA_END-->'
assert data.count(req_segment) == 1
data = data.replace(req_segment, table_block + na_block)

# ==== Migration / E2E (free text) ====
one(
    'w14:paraId="17A35AFF" w14:textId="56872CB9" w:rsidR="001C6D58" w:rsidRPr="00972B98" w:rsidRDefault="001C6D58" w:rsidP="008B34CA"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="17A35AFF" w14:textId="56872CB9" w:rsidR="001C6D58" w:rsidRPr="00972B98" w:rsidRDefault="001C6D58" w:rsidP="008B34CA"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{{MIGRATION_TEXT}}</w:t>',
)
one(
    'w14:paraId="5DBFEB03" w14:textId="77777777" w:rsidR="00553365" w:rsidRPr="00972B98" w:rsidRDefault="001C6D58" w:rsidP="004B4CA7"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="5DBFEB03" w14:textId="77777777" w:rsidR="00553365" w:rsidRPr="00972B98" w:rsidRDefault="001C6D58" w:rsidP="004B4CA7"><w:pPr><w:ind w:left="720"/><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{{E2E_TEXT}}</w:t>',
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
assert len(rows) == 4, f"expected header+3 rows, got {len(rows)}"
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

# --- Code Drop Defects: just needs the font/size fix plus the shared
# row-height standardization used by every ticket table.
t = get_table('BLOCK:CDD:TABLE_START')
new_t = normalize_table_font(t, 'CDD')
assert new_t != t, "CDD: expected font/size normalization to change something"
for old_h in ('331', '183'):
    n = new_t.count(f'<w:trHeight w:val="{old_h}"/>')
    assert n == 1, f"CDD: trHeight {old_h} not found exactly once, got {n}"
    new_t = new_t.replace(f'<w:trHeight w:val="{old_h}"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
assert data.count(t) == 1
data = data.replace(t, new_t)

# --- Requirements: has its own genuine example table now (not cloned from
# CDD), authored independently with its own column widths/row heights, so it
# needs the same kind of dedicated width-rebalance Tasks Completed needed.
req_table = get_table('BLOCK:REQ:TABLE_START')
new_req_table2 = normalize_table_font(req_table, 'Requirements')
req_widths_old = ['666', '1314', '6662', '1276']
req_widths_new = ['804', '1497', '6581', '1044']  # matches the 4-col standard (no Datafix)
for old_w, new_w in zip(req_widths_old, req_widths_new):
    n = new_req_table2.count(f'w:w="{old_w}"')
    assert n >= 1, f"Requirements: width {old_w} not found"
    new_req_table2 = new_req_table2.replace(f'w:w="{old_w}"', f'w:w="{new_w}"')
req_heights_old = ['277', '608']
for old_h in req_heights_old:
    n = new_req_table2.count(f'<w:trHeight w:val="{old_h}"/>')
    assert n == 1, f"Requirements: trHeight {old_h} not found exactly once, got {n}"
    new_req_table2 = new_req_table2.replace(f'<w:trHeight w:val="{old_h}"/>', f'<w:trHeight w:val="{SINGLE_LINE_ROW_HEIGHT}"/>')
assert data.count(req_table) == 1
data = data.replace(req_table, new_req_table2)

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
# tables' headers used to reference a theme color (accent1) that resolved to
# a visibly different, lighter blue than the literal navy every other table
# header uses. The base doc now ships with the literal navy already applied
# everywhere, so this is just a defensive check that it stays that way rather
# than an active fix.
assert data.count('w:fill="156082" w:themeFill="accent1"') == 0, \
    "found theme-colored header fill(s) that should be literal navy -- base doc may have reverted"

# ==== Environment Summary table column widths ====
# The user's latest base doc has its own finalized column widths, row
# heights, and cell padding for this table -- those are trusted as-is now
# rather than overridden. The one thing still worth fixing structurally
# (not visually) is that this table is uniquely set up with floating/
# anchored positioning (tblpPr, absolute vertical offset from its anchor
# paragraph) rather than normal inline flow. That's fragile: any upstream
# change that shifts pagination can make the "Environment Summary" heading
# itself render beside the table instead of above it, since the table no
# longer reliably tracks the heading's actual position. Converting it to a
# plain inline table (like every other table here) makes it immune to this
# class of bug regardless of what else changes upstream.
_es_idx1 = data.find('Environment Summary')
_es_idx2 = data.find('Environment Summary', _es_idx1 + 1)
_es_tbl_start = data.find('<w:tbl>', _es_idx2)
_es_tbl_end = data.find('</w:tbl>', _es_tbl_start) + len('</w:tbl>')
es_table = data[_es_tbl_start:_es_tbl_end]
_es_floating_props = '<w:tblpPr w:leftFromText="180" w:rightFromText="180" w:vertAnchor="text" w:horzAnchor="margin" w:tblpXSpec="center" w:tblpY="164"/>'
assert es_table.count(_es_floating_props) == 1, "Environment Summary: floating tblpPr not found"
new_es_table = es_table.replace(_es_floating_props, '')
assert data.count(es_table) == 1
data = data.replace(es_table, new_es_table)

# ==== Document Revision History table ====
# Previously needed fixing (named style overriding inline header shading),
# but the base doc now ships with a plain "TableGrid" style plus explicit
# per-cell header shading already applied -- nothing left to do here.

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

# ==== Breathing room before "Environment Summary" ====
# Previously needed fixing (it sat flush against the table above with no
# gap), but the base doc now has its own fix for this baked in (two empty
# Heading2-styled paragraphs inserted before the heading) -- nothing left
# to do here.



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
