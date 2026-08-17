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
req_rows = re.findall(r'<w:tr .*?</w:tr>', cdd_source_table, re.S)
req_header, req_row1 = req_rows[0], req_rows[1]
req_prefix = cdd_source_table[:cdd_source_table.find(req_header)]
new_req_row = req_row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_req_row = new_req_row.replace('<w:t>TIC03-2170</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_req_row = new_req_row.replace('<w:t xml:space="preserve">Same-day exposure display incorrect - TIC03-2170</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_req_row = new_req_row.replace('<w:t>Critical</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_req_row = re.sub(r'<w:t>No</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_req_row)
for tok in ('{{ROW_SLNO}}', '{{ROW_KEY}}', '{{ROW_SUMMARY}}', '{{ROW_PRIORITY}}', '{{ROW_DATAFIX}}'):
    assert tok in new_req_row, f"REQ row: {tok} substitution silently no-op'd"
new_req_row = re.sub(r'w14:paraId="([0-9A-Fa-f]{8})"', lambda m: 'w14:paraId="RQ' + m.group(1)[2:] + '"', new_req_row)
templated_req_row = '<!--ROW:REQ-->' + new_req_row + '<!--/ROW:REQ-->'
new_req_table = req_prefix + req_header + templated_req_row + '</w:tbl>'
# Synthesize the intro bullet sentence to match the Tasks Completed / CDD style,
# since Requirements has no such sentence in the source doc.
req_bullet_para = '<w:p w14:paraId="62FB2610" w14:textId="0F9C7610" w:rsidR="001C6D58" w:rsidRDefault="001C6D58"><w:pPr><w:rPr><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="22"/></w:rPr></w:pPr><w:r><w:rPr><w:color w:val="000000" w:themeColor="text1"/><w:sz w:val="22"/></w:rPr><w:t xml:space="preserve">Below requirements were released as part of CD {{CD_VERSION}} - </w:t></w:r></w:p>'
# Matches the empty spacer paragraph that CDD/Tasks Completed retain naturally
# from the source doc between their intro sentence and their table -- without
# it, Requirements' table sits flush against the sentence while every other
# section has a visible gap.
req_spacer_para = '<w:p w14:paraId="62FB2611" w14:textId="77777777" w:rsidR="001C6D58" w:rsidRPr="001C6D58" w:rsidRDefault="001C6D58" w:rsidP="001C6D58"/>'
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
one(
    'w14:paraId="42D80303" w14:textId="1C101F18" w:rsidR="00FD7163" w:rsidRPr="00520FCB" w:rsidRDefault="001C6D58" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t xml:space="preserve">AppSettings.Config change(s) - </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="42D80303" w14:textId="1C101F18" w:rsidR="00FD7163" w:rsidRPr="00520FCB" w:rsidRDefault="001C6D58" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t xml:space="preserve">AppSettings.Config change(s) - </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{{APPSETTINGS_TEXT}}</w:t>',
)
one(
    'w14:paraId="75E97C55" w14:textId="31858B4D" w:rsidR="00CE257F" w:rsidRDefault="007E756C" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>Web Config change(s)</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>- NA</w:t>',
    'w14:paraId="75E97C55" w14:textId="31858B4D" w:rsidR="00CE257F" w:rsidRDefault="007E756C" w:rsidP="00743EF2"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t>Web Config change(s)</w:t></w:r><w:r><w:t xml:space="preserve"> </w:t></w:r><w:r><w:rPr><w:rFonts w:eastAsia="Calibri" w:cs="Calibri"/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t xml:space="preserve">- {{WEBCONFIG_TEXT}}</w:t>',
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

open(path, 'w', encoding='utf-8').write(data)
print("Templatization complete. Length:", len(data))
