import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Light Mode CSS Variables to professional, muted pastel colors
old_light_vars = """  --violet: #A78BFA;
  --violet2: #C4B5FD;
  --purple: #E879F9;
  --cyan: #22D3EE;
  --cyan2: #67E8F9;
  --pink: #F472B6;
  --green: #34D399;
  --amber: #FBBF24;
  --red: #F87171;"""

new_light_vars = """  --violet: #8ba5c9; /* Soft Steel Blue */
  --violet2: #a5bddc; /* Lighter Steel */
  --purple: #b9bdd6; /* Soft Lilac Gray */
  --cyan: #8bc3c9; /* Soft Aqua */
  --cyan2: #a8d5db; /* Lighter Aqua */
  --pink: #d9aebf; /* Muted Dusty Pink */
  --green: #9cc2a5; /* Soft Sage */
  --amber: #d4bc8e; /* Muted Sand */
  --red: #d19292; /* Soft Rose */"""

content = content.replace(old_light_vars, new_light_vars)

# 2. Update KPI gradients to match a lighter, lower-contrast look.
old_kpi_v = "background:linear-gradient(135deg,#7C3AED 0%,#A855F7 55%,#C084FC 100%); border:none; box-shadow:0 14px 34px -12px rgba(139,92,246,.65);"
new_kpi_v = "background:linear-gradient(135deg, #a5bddc 0%, #c4d7ec 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(139,165,201,.4);"
content = content.replace(old_kpi_v, new_kpi_v)

old_kpi_c = "background:linear-gradient(135deg,#0891B2 0%,#22D3EE 60%,#67E8F9 100%); border:none; box-shadow:0 14px 34px -12px rgba(34,211,238,.5);"
new_kpi_c = "background:linear-gradient(135deg, #a8d5db 0%, #c8ebef 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(139,195,201,.4);"
content = content.replace(old_kpi_c, new_kpi_c)

old_kpi_text1 = ".atlas-dashboard .kpi.grad-v .lbl, .atlas-dashboard .kpi.grad-c .lbl, .atlas-dashboard .kpi.grad-v .sub, .atlas-dashboard .kpi.grad-c .sub { color:rgba(255,255,255,.9); }"
new_kpi_text1 = ".atlas-dashboard .kpi.grad-v .lbl, .atlas-dashboard .kpi.grad-c .lbl, .atlas-dashboard .kpi.grad-v .sub, .atlas-dashboard .kpi.grad-c .sub { color:rgba(0,0,0,.6); }"
content = content.replace(old_kpi_text1, new_kpi_text1)

old_kpi_text2 = ".atlas-dashboard .kpi.grad-v .num, .atlas-dashboard .kpi.grad-c .num { color:#fff; }"
new_kpi_text2 = ".atlas-dashboard .kpi.grad-v .num, .atlas-dashboard .kpi.grad-c .num { color:rgba(0,0,0,.8); }"
content = content.replace(old_kpi_text2, new_kpi_text2)

old_kpi_text3 = ".atlas-dashboard .kpi.grad-v .pill, .atlas-dashboard .kpi.grad-c .pill { background:rgba(255,255,255,.22); color:#fff; }"
new_kpi_text3 = ".atlas-dashboard .kpi.grad-v .pill, .atlas-dashboard .kpi.grad-c .pill { background:rgba(0,0,0,.08); color:rgba(0,0,0,.7); }"
content = content.replace(old_kpi_text3, new_kpi_text3)

old_kpi_after = ".atlas-dashboard .kpi.grad-v::after, .atlas-dashboard .kpi.grad-c::after { content:\"\"; position:absolute; width:150px; height:150px; border-radius:50%; background:rgba(255,255,255,.14); top:-60px; right:-40px; }"
new_kpi_after = ".atlas-dashboard .kpi.grad-v::after, .atlas-dashboard .kpi.grad-c::after { content:\"\"; position:absolute; width:150px; height:150px; border-radius:50%; background:rgba(255,255,255,.4); top:-60px; right:-40px; }"
content = content.replace(old_kpi_after, new_kpi_after)

# Update buttons
old_btn = ".atlas-dashboard .btn-atlas { background:linear-gradient(135deg,var(--violet),var(--purple)); color:#fff; border:none; box-shadow:0 6px 20px -6px rgba(139,92,246,.7); }"
new_btn = ".atlas-dashboard .btn-atlas { background:var(--dashboard-card); color:var(--dashboard-text); border:1px solid var(--dashboard-line); box-shadow:0 2px 6px -2px rgba(0,0,0,.05); }"
content = content.replace(old_btn, new_btn)


with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated successfully!")
