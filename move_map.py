import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Change col-12 to col-lg-6 in panel1
# Since panel1 starts with:
#             <!-- PANEL 1: ROUTING DETAILS -->
#             <div class="expandable-panel open" id="panel1">
#                 <div class="row">
#                     <div class="col-12">
target_panel1_start = """            <!-- PANEL 1: ROUTING DETAILS -->
            <div class="expandable-panel open" id="panel1">
                <div class="row">
                    <div class="col-12">"""
replacement_panel1_start = """            <!-- PANEL 1: ROUTING DETAILS -->
            <div class="expandable-panel open" id="panel1">
                <div class="row">
                    <div class="col-lg-6 pe-lg-4 border-end">"""
content = content.replace(target_panel1_start, replacement_panel1_start)


# 2. Append the map inside the row after the Next Step button
target_panel1_end = """                        <div class="text-end mt-4 pt-3 border-top">
                            <button type="button" class="btn btn-primary px-4 fw-bold" onclick="openPanel(2)">Next Step <i class="bi bi-chevron-right"></i></button>
                        </div>
                    </div>
                </div>
            </div>"""

replacement_panel1_end = """                        <div class="text-end mt-4 pt-3 border-top">
                            <button type="button" class="btn btn-primary px-4 fw-bold" onclick="openPanel(2)">Next Step <i class="bi bi-chevron-right"></i></button>
                        </div>
                    </div>
                    
                    <!-- Map on the right side of Panel 1 -->
                    <div class="col-lg-6 ps-lg-4 d-none d-lg-block">
                        <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden; height: 100%;">
                            <div class="card-header bg-white border-bottom-0 pt-2 pb-0">
                                <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                            </div>
                            <div class="card-body p-2 d-flex flex-column">
                                <div id="sideMap" style="height: 400px; flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>"""
content = content.replace(target_panel1_end, replacement_panel1_end)


# 3. Remove the old panoramic map at the bottom
target_old_map = """            <!-- PANORAMIC MAP AT THE BOTTOM -->
            <div class="col-12 mt-4">
                <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden;">
                    <div class="card-header bg-white border-bottom-0 pt-3 pb-0">
                        <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                    </div>
                    <div class="card-body p-3 d-flex flex-column">
                        <div id="sideMap" style="height: 450px; flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                    </div>
                </div>
            </div>"""

content = content.replace(target_old_map, "")


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Map moved into panel1 successfully.")
