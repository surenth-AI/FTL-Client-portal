import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Restore panel1 to use col-12 instead of col-lg-6
content = content.replace('<div class="col-lg-6 pe-lg-4 border-end">', '<div class="col-12">')

# 2. Remove Map from panel1
map_in_panel1 = """                    <!-- Map on the right side of Panel 1 -->
                    <div class="col-lg-6 ps-lg-4 d-none d-lg-block">
                        <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden; height: 100%;">
                            <div class="card-header bg-white border-bottom-0 pt-2 pb-0">
                                <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                            </div>
                            <div class="card-body p-2 d-flex flex-column">
                                <div id="sideMap" style="height: 400px; flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                            </div>
                        </div>
                    </div>"""
content = content.replace(map_in_panel1, "")


# 3. Restructure panels-container
target_panels_start = """        <div class="panels-container">
            
            <!-- PANEL 1: ROUTING DETAILS -->"""

replacement_panels_start = """        <div class="panels-container">
            <div class="row m-0">
                <div class="col-lg-7 p-0 border-end">
            
            <!-- PANEL 1: ROUTING DETAILS -->"""
content = content.replace(target_panels_start, replacement_panels_start)


# 4. Append Map to the end of panels-container
target_panels_end = """                        </div>
                    </div>
                </div>
            </div>
        </div>
    </form>"""

replacement_panels_end = """                        </div>
                    </div>
                </div>
            </div>
                </div> <!-- End col-lg-7 -->
                
                <!-- SIDE MAP FOR ALL PANELS -->
                <div class="col-lg-5 p-0 bg-light d-none d-lg-block" style="border-radius: 0 0 12px 0;">
                    <div class="p-4 d-flex flex-column h-100">
                        <div class="card shadow-sm border-0 flex-grow-1" style="border-radius: 12px; overflow: hidden; min-height: 500px;">
                            <div class="card-header bg-white border-bottom-0 pt-3 pb-0">
                                <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                            </div>
                            <div class="card-body p-3 d-flex flex-column">
                                <div id="sideMap" style="height: 100%; flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                            </div>
                        </div>
                    </div>
                </div> <!-- End col-lg-5 -->
            </div> <!-- End row -->
        </div> <!-- End panels-container -->
    </form>"""
content = content.replace(target_panels_end, replacement_panels_end)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Restructured map layout for all panels.")
