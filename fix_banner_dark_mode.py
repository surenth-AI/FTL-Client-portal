import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_html = """                        <!-- Air/Road Freight Notice Banner -->
                        <div id="offlineServiceBanner" style="display: none; background: #fffbeb; border: 1px solid #fef08a; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                            <div class="d-flex align-items-center gap-3">
                                <div style="background: #fef08a; color: #ca8a04; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
                                    <i class="bi bi-info-circle-fill"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1 text-dark fw-bold" style="font-size: 0.9rem;">Offline Service Request</h6>
                                    <p class="mb-0 text-muted" style="font-size: 0.8rem;" id="offlineServiceText">
                                        This transport mode requires direct contact with our office for personalized rates.
                                    </p>
                                </div>
                                <div>
                                    <a href="mailto:support@axeglobal.com" class="btn btn-sm" style="background: #eab308; color: white; font-weight: 600;"><i class="bi bi-envelope me-1"></i> Contact Us</a>
                                </div>
                            </div>
                        </div>"""

replacement_html = """                        <!-- Air/Road Freight Notice Banner -->
                        <div id="offlineServiceBanner" class="offline-banner" style="display: none;">
                            <div class="d-flex align-items-center gap-3">
                                <div class="offline-banner-icon">
                                    <i class="bi bi-info-circle-fill"></i>
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1 offline-banner-title fw-bold" style="font-size: 0.9rem;">Offline Service Request</h6>
                                    <p class="mb-0 offline-banner-text" style="font-size: 0.8rem;" id="offlineServiceText">
                                        This transport mode requires direct contact with our office for personalized rates.
                                    </p>
                                </div>
                                <div>
                                    <a href="mailto:support@axeglobal.com" class="btn btn-sm offline-banner-btn"><i class="bi bi-envelope me-1"></i> Contact Us</a>
                                </div>
                            </div>
                        </div>"""

content = content.replace(target_html, replacement_html)

css_to_add = """    /* Offline Banner */
    .offline-banner { background: #fffbeb; border: 1px solid #fef08a; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: all 0.3s; }
    .offline-banner-icon { background: #fef08a; color: #ca8a04; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; transition: all 0.3s; }
    .offline-banner-title { color: #854d0e; transition: all 0.3s; }
    .offline-banner-text { color: #a16207; transition: all 0.3s; }
    .offline-banner-btn { background: #eab308; color: white; font-weight: 600; transition: all 0.3s; border: 1px solid #ca8a04; }
    .offline-banner-btn:hover { background: #ca8a04; color: white; }

    html[data-color-scheme='dark'] .offline-banner { background: rgba(234, 179, 8, 0.1); border-color: rgba(234, 179, 8, 0.2); }
    html[data-color-scheme='dark'] .offline-banner-icon { background: rgba(234, 179, 8, 0.2); color: #fde047; }
    html[data-color-scheme='dark'] .offline-banner-title { color: #fef08a; }
    html[data-color-scheme='dark'] .offline-banner-text { color: #fde047; }
    html[data-color-scheme='dark'] .offline-banner-btn { background: #ca8a04; color: #fff; border: 1px solid #a16207; }
    html[data-color-scheme='dark'] .offline-banner-btn:hover { background: #a16207; color: #fff; }
</style>"""

content = content.replace("</style>", css_to_add)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Dark mode CSS fixed for offline banner.")
