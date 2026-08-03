import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Light Mode CSS Variables to slightly higher contrast professional colors (Tailwind 500-600s)
old_light_vars = """  --violet: #8ba5c9; /* Soft Steel Blue */
  --violet2: #a5bddc; /* Lighter Steel */
  --purple: #b9bdd6; /* Soft Lilac Gray */
  --cyan: #8bc3c9; /* Soft Aqua */
  --cyan2: #a8d5db; /* Lighter Aqua */
  --pink: #d9aebf; /* Muted Dusty Pink */
  --green: #9cc2a5; /* Soft Sage */
  --amber: #d4bc8e; /* Muted Sand */
  --red: #d19292; /* Soft Rose */"""

new_light_vars = """  --violet: #6366f1; /* Indigo 500 */
  --violet2: #818cf8; /* Indigo 400 */
  --purple: #8b5cf6; /* Violet 500 */
  --cyan: #0ea5e9; /* Sky 500 */
  --cyan2: #38bdf8; /* Sky 400 */
  --pink: #d946ef; /* Fuchsia 500 */
  --green: #10b981; /* Emerald 500 */
  --amber: #f59e0b; /* Amber 500 */
  --red: #ef4444; /* Red 500 */"""

content = content.replace(old_light_vars, new_light_vars)

# 2. Update KPI gradients to match
old_kpi_v = "background:linear-gradient(135deg, #a5bddc 0%, #c4d7ec 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(139,165,201,.4);"
new_kpi_v = "background:linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(99,102,241,.15);"
content = content.replace(old_kpi_v, new_kpi_v)

old_kpi_c = "background:linear-gradient(135deg, #a8d5db 0%, #c8ebef 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(139,195,201,.4);"
new_kpi_c = "background:linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%); border:1px solid var(--dashboard-line); box-shadow:0 8px 24px -12px rgba(14,165,233,.15);"
content = content.replace(old_kpi_c, new_kpi_c)

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated successfully!")
