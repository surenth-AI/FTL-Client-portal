import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We need to find the end of panel3 and inject the map.
# The end of panel3 looks like:
#                         <div class="d-flex justify-content-between mt-5 pt-4 border-top align-items-center">
#                             <button type="button" class="btn btn-light border px-4 fw-bold" onclick="openPanel(2)"><i class="bi bi-chevron-left"></i> Back</button>
#                             <button type="button" class="btn-search-glow m-0 mt-0" style="width: auto;" onclick="submitWizForm()">
#                                 <i class="bi bi-calculator"></i> Request Quotes
#                             </button>
#                         </div>
#                     </div>
#                 </div>
#             </div>

pattern = r'(<button type="button" class="btn-search-glow m-0 mt-0" style="width: auto;" onclick="submitWizForm\(\)">.*?<i class="bi bi-calculator"></i> Request Quotes.*?</button>\s*</div>\s*</div>\s*</div>\s*</div>)(.*?)</form>'

replacement = r"""\1
                </div> <!-- End col-lg-7 -->
                
                <!-- SIDE MAP FOR ALL PANELS -->
                <div class="col-lg-5 p-0 bg-light d-none d-lg-block" style="border-radius: 0 0 12px 0;">
                    <div class="p-4 d-flex flex-column h-100">
                        <div class="card shadow-sm border-0 flex-grow-1" style="border-radius: 12px; overflow: hidden; min-height: 500px;">
                            <div class="card-header bg-white border-bottom-0 pt-3 pb-0">
                                <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                            </div>
                            <div class="card-body p-3 d-flex flex-column">
                                <!-- Set height: 450px explicitly just in case flex height fails -->
                                <div id="sideMap" style="height: 450px; flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                            </div>
                        </div>
                    </div>
                </div> <!-- End col-lg-5 -->
            </div> <!-- End row m-0 -->
        </div> <!-- End panels-container -->
    </form>"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("Failed to replace!")
else:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Map successfully injected!")
