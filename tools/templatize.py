import re

path = 'unpacked/word/document.xml'
data = open(path).read()

def one(old, new):
    global data
    n = data.count(old)
    assert n == 1, f"expected 1 occurrence, got {n}: {old[:80]!r}"
    data = data.replace(old, new)

# ---- Cover / version tokens ----
one('<w:t>7.31.1</w:t>', '<w:t>{{CD_VERSION}}</w:t>')
one('<w:t>CodeDrop7.31.1</w:t>', '<w:t>CodeDrop{{CD_VERSION}}</w:t>')
one('<w:t>118.7.31.1</w:t>', '<w:t>{{FULL_VERSION}}</w:t>')
data = re.sub(r'released as part of CD 7\.31\.1', 'released as part of CD {{CD_VERSION}}', data)

# ---- Dates ----
data = data.replace('<w:t>August 3, 2026</w:t>', '<w:t>{{RELEASE_DATE}}</w:t>')
data = data.replace('<w:t>August 3 - 2026</w:t>', '<w:t>{{REV_DATE}}</w:t>')

# ---- Release Details table ----
one('<w:t>4.24.12.49</w:t>', '<w:t>{{FX_VERSION}}</w:t>')
one('<w:t>5.81.2.7418</w:t>', '<w:t>{{PRODUCT_VERSION}}</w:t>')
one('<w:t>Full Release</w:t>', '<w:t>{{RELEASE_TYPE}}</w:t>')
one('<w:t>Odessa Core</w:t>', '<w:t>{{SITE_LABEL}}</w:t>')

one(
    'w14:paraId="701406AE" w14:textId="7B304F81"><w:pPr><w:widowControl/><w:autoSpaceDE/><w:autoSpaceDN/><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>No</w:t>',
    'w14:paraId="701406AE" w14:textId="7B304F81"><w:pPr><w:widowControl/><w:autoSpaceDE/><w:autoSpaceDN/><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:color w:val="263746"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>{{HOTFIX}}</w:t>',
)

# ==== Business Configuration (table <-> "No RBS Impact") ====
# second occurrence is the real body heading (first is the TOC entry)
_bc_idx1 = data.find('Business Configuration</w:t>')
idx = data.find('Business Configuration</w:t>', _bc_idx1 + 1)
tbl_start = data.find('<w:tbl>', idx)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
table = data[tbl_start:tbl_end]
rows = re.findall(r'<w:tr .*?</w:tr>', table, re.S)
header, row1 = rows[0], rows[1]
prefix = table[:table.find(header)]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC04-122</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace('<w:t>Phase2 | M2 | RBS changes</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row = new_row.replace('<w:t>RBS</w:t>', '<w:t>{{ROW_TYPE}}</w:t>')
templated_row = '<!--ROW:BIZCONFIG-->' + new_row + '<!--/ROW:BIZCONFIG-->'
new_table = prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:BIZCONFIG:TABLE_START-->' + new_table + '<!--BLOCK:BIZCONFIG:TABLE_END-->'
na_para = '<w:p w:rsidRPr="00860B61" w:rsidR="001C6D58" w:rsidP="007E756C" w:rsidRDefault="001C6D58" w14:paraId="62FB2601" w14:textId="0F9C7601"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>No RBS Impact</w:t></w:r></w:p>'
na_block = '<!--BLOCK:BIZCONFIG:NA_START-->' + na_para + '<!--BLOCK:BIZCONFIG:NA_END-->'
assert data.count(table) == 1
data = data.replace(table, table_block + na_block)

# ==== Requirements (bullet + table <-> NA) ====
idx = data.find('<w:t>Requirements</w:t>')
bm_idx = data.find('bookmarkEnd w:id="21"', idx)
seg_start = data.find('</w:p>', bm_idx) + len('</w:p>')
tbl_start = data.find('<w:tbl>', seg_start)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
segment = data[seg_start:tbl_end]
rows = re.findall(r'<w:tr .*?</w:tr>', segment, re.S)
header, row1 = rows[0], rows[1]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC04-38</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace('<w:t>Funding | Wholesale Intelligence Payment Date</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row = new_row.replace('<w:t>Medium</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_row = re.sub(r'<w:t>No</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_row)
templated_row = '<!--ROW:REQ-->' + new_row + '<!--/ROW:REQ-->'
bullet_end = segment.find('<w:tbl>')
bullet_para = segment[:bullet_end]
table_part = segment[bullet_end:]
tbl_prefix = table_part[:table_part.find(header)]
new_table = tbl_prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:REQ:TABLE_START-->' + bullet_para + new_table + '<!--BLOCK:REQ:TABLE_END-->'
na_para = '<w:p w:rsidRPr="00860B61" w:rsidR="001C6D58" w:rsidP="007E756C" w:rsidRDefault="001C6D58" w14:paraId="62FB2602" w14:textId="0F9C7602"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:REQ:NA_START-->' + na_para + '<!--BLOCK:REQ:NA_END-->'
assert data.count(segment) == 1
data = data.replace(segment, table_block + na_block)

# ==== Migration / E2E (free text) ====
one(
    'w14:paraId="62FB274F" w14:textId="0F9C707F"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="62FB274F" w14:textId="0F9C707F"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>{{MIGRATION_TEXT}}</w:t>',
)
one(
    'w14:paraId="5C0640D3" w14:textId="4C73C013"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="5C0640D3" w14:textId="4C73C013"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>{{E2E_TEXT}}</w:t>',
)

# ==== Code Drop Defects (bullet + table <-> NA) -- do this BEFORE Tasks Completed
# so we can reuse its original table structure as source for Tasks Completed ====
idx = data.find('defect was released')
cdd_seg_start = data.find('<w:p w:rsidR="50E7ED56"')
tbl_start = data.find('<w:tbl>', cdd_seg_start)
tbl_end = data.find('</w:tbl>', tbl_start) + len('</w:tbl>')
cdd_segment = data[cdd_seg_start:tbl_end]
cdd_source_table = cdd_segment[cdd_segment.find('<w:tbl>'):]  # save pristine copy for Tasks Completed

rows = re.findall(r'<w:tr .*?</w:tr>', cdd_segment, re.S)
header, row1 = rows[0], rows[1]
new_row = row1.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row = new_row.replace('<w:t>TIC04-130</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row = new_row.replace('<w:t>Core_TIC04-17_ Odessa is creating $0 sundry for the asset sale fee and...</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row = new_row.replace('<w:t>Highest</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_row = re.sub(r'<w:t>No</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_row)
templated_row = '<!--ROW:CDD-->' + new_row + '<!--/ROW:CDD-->'
bullet_end = cdd_segment.find('<w:tbl>')
bullet_para = cdd_segment[:bullet_end]
table_part = cdd_segment[bullet_end:]
tbl_prefix = table_part[:table_part.find(header)]
new_table = tbl_prefix + header + templated_row + '</w:tbl>'
table_block = '<!--BLOCK:CDD:TABLE_START-->' + bullet_para + new_table + '<!--BLOCK:CDD:TABLE_END-->'
na_para = '<w:p w:rsidRPr="00860B61" w:rsidR="001C6D58" w:rsidP="007E756C" w:rsidRDefault="001C6D58" w14:paraId="62FB2603" w14:textId="0F9C7603"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block = '<!--BLOCK:CDD:NA_START-->' + na_para + '<!--BLOCK:CDD:NA_END-->'
assert data.count(cdd_segment) == 1
data = data.replace(cdd_segment, table_block + na_block)

# ==== Tasks Completed (build table from CDD source structure) ====
rows2 = re.findall(r'<w:tr .*?</w:tr>', cdd_source_table, re.S)
header2, row1_2 = rows2[0], rows2[1]
prefix2 = cdd_source_table[:cdd_source_table.find(header2)]
new_row2 = row1_2.replace('<w:t>1</w:t>', '<w:t>{{ROW_SLNO}}</w:t>', 1)
new_row2 = new_row2.replace('<w:t>TIC04-130</w:t>', '<w:t>{{ROW_KEY}}</w:t>')
new_row2 = new_row2.replace('<w:t>Core_TIC04-17_ Odessa is creating $0 sundry for the asset sale fee and...</w:t>', '<w:t>{{ROW_SUMMARY}}</w:t>')
new_row2 = new_row2.replace('<w:t>Highest</w:t>', '<w:t>{{ROW_PRIORITY}}</w:t>')
new_row2 = re.sub(r'<w:t>No</w:t></w:r></w:p></w:tc></w:tr>$', '<w:t>{{ROW_DATAFIX}}</w:t></w:r></w:p></w:tc></w:tr>', new_row2)
new_row2 = re.sub(r'w14:paraId="([0-9A-Fa-f]{8})"', lambda m: 'w14:paraId="TC' + m.group(1)[2:] + '"', new_row2)
templated_row2 = '<!--ROW:TASKS-->' + new_row2 + '<!--/ROW:TASKS-->'
new_table2 = prefix2 + header2 + templated_row2 + '</w:tbl>'
table_block2 = '<!--BLOCK:TASKS:TABLE_START-->' + new_table2 + '<!--BLOCK:TASKS:TABLE_END-->'

old_na_para_tasks = '<w:p w:rsidR="005D574F" w:rsidP="00BE7B2D" w:rsidRDefault="005D574F" w14:paraId="3D44F99B" w14:textId="16137C4C"><w:pPr><w:ind w:left="720"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t></w:r></w:p>'
na_block2 = '<!--BLOCK:TASKS:NA_START-->' + old_na_para_tasks + '<!--BLOCK:TASKS:NA_END-->'
assert data.count(old_na_para_tasks) == 1
data = data.replace(old_na_para_tasks, table_block2 + na_block2)

# ==== Technical Configuration (free text) ====
one('<w:t xml:space="preserve">               NA</w:t>', '<w:t xml:space="preserve">               {{APPSETTINGS_TEXT}}</w:t>')
one(
    'w14:paraId="03D1E0FA" w14:textId="76C0B47D"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>NA</w:t>',
    'w14:paraId="03D1E0FA" w14:textId="76C0B47D"><w:pPr><w:ind w:left="720"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:color w:val="000000"/></w:rPr><w:t>{{WEBCONFIG_TEXT}}</w:t>',
)

# ==== Release Request Packages (fixed 6 rows) ====
rrp_edits = [
    ('5FDC94EE', '62F0FA17', 'Yes', 'LESSOR_PORTAL'),
    ('17278F8A', '79C2019A', 'Yes', 'WINDOWS_SERVICE'),
    ('6893F9CC', '5408D7C0', 'Yes', 'WEB_API'),
    ('0462495C', '1159665B', 'Yes', 'DATABASE'),
]
for pid, tid, val, token in rrp_edits:
    old = f'w14:paraId="{pid}" w14:textId="{tid}"><w:r><w:t>{val}</w:t>'
    new = f'w14:paraId="{pid}" w14:textId="{tid}"><w:r><w:t>{{{{RRP_{token}}}}}</w:t>'
    one(old, new)

one(
    'w14:paraId="3FB9D7F8" w14:textId="77777777"><w:pPr><w:rPr><w:rFonts w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-IN" w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-IN" w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>No</w:t>',
    'w14:paraId="3FB9D7F8" w14:textId="77777777"><w:pPr><w:rPr><w:rFonts w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-IN" w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:cs="Calibri"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-IN" w:eastAsia="en-IN" w:bidi="ar-SA"/></w:rPr><w:t>{{RRP_REPORTS}}</w:t>',
)
one(
    'w14:paraId="07977E0D" w14:textId="75C87E71"><w:pPr><w:spacing w:line="259" w:lineRule="auto"/></w:pPr><w:r><w:t>No</w:t>',
    'w14:paraId="07977E0D" w14:textId="75C87E71"><w:pPr><w:spacing w:line="259" w:lineRule="auto"/></w:pPr><w:r><w:t>{{RRP_APPSETTINGS_CONFIG}}</w:t>',
)

open(path, 'w').write(data)
print("Templatization complete. Length:", len(data))
