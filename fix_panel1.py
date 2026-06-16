import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure we didn't already inject the map
if '<!-- SIDE MAP -->' not in content:
    target_btn = '<div class="text-end mt-4 pt-3 border-top">'
    if target_btn in content:
        map_html = """</div>
                    <!-- SIDE MAP -->
                    <div class="col-lg-5">
                        <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden; height: 100%; min-height: 400px;">
                            <div class="card-header bg-white border-bottom-0 pt-3 pb-0">
                                <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                            </div>
                            <div class="card-body p-3">
                                <div id="sideMap" style="height: 100%; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                            </div>
                        </div>
                    </div>
                    """
        content = content.replace(target_btn, map_html + target_btn, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Map injected into panel1 safely.")
