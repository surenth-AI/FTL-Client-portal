import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for the hazardous checkbox and Stackable Cargo div
pattern = r'<label class="d-flex align-items-center" style="cursor:pointer;">\s*<input type="checkbox" class="me-2" style="width:16px; height:16px; accent-color: var\(--primary-color\);" onchange="toggleHazardous\(this, \'\$\{id\}\'\)">\s*<input type="hidden" name="item_is_imo\[\]" id="\$\{id\}-imo-hidden" value="no">\s*<span class="text-danger fw-bold" style="font-size: 0\.75rem;"><i class="bi bi-exclamation-triangle"></i> IMO / Hazardous Goods</span>\s*</label>'

replacement = """<label class="d-flex align-items-center" style="cursor:pointer;">
                    <select class="premium-input me-2" name="goods_type[]" style="width: auto; font-size: 0.75rem; padding: 0.2rem 0.5rem;" required>
                        <option value="COMMERCIAL">Commercial Goods</option>
                        <option value="HAZARDOUS">Hazardous Materials</option>
                    </select>
                </label>"""

content = re.sub(pattern, replacement, content)

# Remove the hazardousFields div
pattern_fields = r'<div id="\$\{id\}-hazardousFields".*?</div>\s*</div>\s*</div>'
content = re.sub(pattern_fields, '', content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Goods type updated.")
