import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Terminology
content = content.replace(">LCL<", ">Less than a container load<")
content = content.replace("LCL (Less than Container)", "Less than a container load")
content = content.replace(">FCL<", ">Full container load<")
content = content.replace("FCL (Full Container)", "Full container load")

# Goods Type replacement for LCL
lcl_target = """                <div class="mt-3 pt-3 border-top d-flex align-items-center">
                    <input type="checkbox" class="me-2" style="width:16px; height:16px; accent-color: var(--primary-color);" onchange="toggleHazardous(this, '${id}')">
                    <label class="mb-0 text-muted" style="font-size: 0.75rem;">Flag as </label>&nbsp;
                    <span class="text-danger fw-bold" style="font-size: 0.75rem;"><i class="bi bi-exclamation-triangle"></i> IMO / Hazardous Goods</span>
                </div>
            </div>
            
            <div id="${id}-hazardousFields" style="display:none; margin-top:0.75rem; padding:0.75rem; border:1px solid #fda4af; background:#fff1f2; border-radius:4px;">
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <label class="premium-label">UN Class</label>
                        <input type="text" class="premium-input" placeholder="e.g. 3">
                    </div>
                    <div class="col-md-6 mb-2">
                        <label class="premium-label">UN Number</label>
                        <input type="text" class="premium-input" placeholder="e.g. 1263">
                    </div>
                </div>
            </div>"""

goods_type_html = """                <div class="mt-3 pt-3 border-top">
                    <div class="row">
                        <div class="col-md-12">
                            <label class="premium-label required">Goods Type</label>
                            <select class="premium-input" name="goods_type[]" required>
                                <option value="COMMERCIAL">Commercial Goods</option>
                                <option value="HAZARDOUS">Hazardous Materials</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>"""
content = content.replace(lcl_target, goods_type_html)

# Goods Type replacement for FCL
fcl_target = """                <div class="mt-3 pt-3 border-top d-flex align-items-center">
                    <input type="checkbox" class="me-2" style="width:16px; height:16px; accent-color: var(--primary-color);" onchange="toggleHazardous(this, '${id}')">
                    <label class="mb-0 text-muted" style="font-size: 0.75rem;">Flag as </label>&nbsp;
                    <span class="text-danger fw-bold" style="font-size: 0.75rem;"><i class="bi bi-exclamation-triangle"></i> IMO / Hazardous Goods</span>
                </div>
            </div>
            
            <div id="${id}-hazardousFields" style="display:none; margin-top:0.75rem; padding:0.75rem; border:1px solid #fda4af; background:#fff1f2; border-radius:4px;">
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <label class="premium-label">UN Class</label>
                        <input type="text" class="premium-input" placeholder="e.g. 3">
                    </div>
                    <div class="col-md-6 mb-2">
                        <label class="premium-label">UN Number</label>
                        <input type="text" class="premium-input" placeholder="e.g. 1263">
                    </div>
                </div>
            </div>"""
content = content.replace(fcl_target, goods_type_html)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Terminology and Goods Type updated.")
