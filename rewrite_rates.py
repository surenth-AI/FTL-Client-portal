import re

with open('d:/FTL-DEV/app/templates/customer/rates.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the styles
old_styles_regex = r'<!-- Leaflet Engine Integration for Dynamic Visual Inputs -->.*?<style>.*?</style>'
if '<!-- Leaflet Engine Integration for Dynamic Visual Inputs -->' not in content:
    old_styles_regex = r'<style>.*?</style>'

new_styles = """<!-- Leaflet Engine Integration for Dynamic Visual Inputs -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
    /* Premium AxeGlobal Aesthetic */
    :root {
        --deck-bg: #070B14;
        --deck-surface: rgba(15, 23, 42, 0.65);
        --deck-border: rgba(255, 255, 255, 0.08);
        --neon-cyan: #06b6d4;
        --neon-indigo: #6366f1;
        --text-bright: #f8fafc;
        --text-dim: #94a3b8;
    }

    body { background-color: var(--deck-bg); color: var(--text-bright); font-family: 'Inter', sans-serif; }

    .command-deck-container {
        position: relative;
        background: var(--deck-surface);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid var(--deck-border);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.05);
        overflow: hidden;
        margin-bottom: 2rem;
    }

    /* Ambient Glow Effects */
    .command-deck-container::before {
        content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.15), transparent 50%),
                    radial-gradient(circle at 100% 100%, rgba(6, 182, 212, 0.1), transparent 50%);
        pointer-events: none; z-index: 0;
    }

    .deck-content { position: relative; z-index: 1; }

    /* Section Cards */
    .section-card {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 1.5rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        transition: all 0.3s;
    }
    .section-card:hover {
        border-color: rgba(6, 182, 212, 0.3);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .section-header { margin-bottom: 1.5rem; }
    .section-title { font-size: 1.1rem; font-weight: 800; color: white; display: flex; align-items: center; gap: 0.5rem; }
    .section-title i { color: var(--neon-cyan); }
    .section-subtitle { font-size: 0.75rem; color: var(--text-dim); margin-top: 0.2rem; padding-left: 1.5rem; }

    /* Input Styling */
    .cyber-input-group { margin-bottom: 1.25rem; position: relative; }
    .cyber-label {
        display: block; font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 1px; color: var(--text-dim); margin-bottom: 0.4rem;
    }
    .cyber-input {
        width: 100%; background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px; padding: 0.7rem 1rem; color: white; font-size: 0.85rem;
        transition: all 0.3s;
    }
    .cyber-input:focus {
        outline: none; border-color: var(--neon-cyan); box-shadow: 0 0 0 1px var(--neon-cyan);
        background: rgba(6, 182, 212, 0.05);
    }
    
    /* Cargo Manifest */
    .cargo-hologram {
        background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 100%);
        border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 1rem;
        margin-bottom: 1rem; position: relative; overflow: hidden;
        animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .cargo-hologram::before {
        content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
        background: var(--neon-indigo); box-shadow: 0 0 8px var(--neon-indigo);
    }
    @keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
    .holo-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 0.75rem; }
    
    /* Panoramic Map */
    .panoramic-map-container {
        margin-top: 2rem; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);
        height: 300px; position: relative;
    }
    #globalRouteMap {
        height: 100%; width: 100%; filter: invert(90%) hue-rotate(180deg) brightness(85%) contrast(110%);
    }
    .map-overlay-text {
        position: absolute; top: 1rem; left: 1rem; z-index: 1000;
        background: rgba(0,0,0,0.6); backdrop-filter: blur(5px);
        padding: 0.5rem 1rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
        font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; color: var(--neon-cyan);
        pointer-events: none;
    }

    /* Action Orb */
    .orb-btn {
        background: linear-gradient(135deg, var(--neon-cyan), var(--neon-indigo));
        border: none; border-radius: 50px; padding: 1rem 2rem; color: white; width: 100%;
        font-weight: 800; font-size: 1rem; text-transform: uppercase; letter-spacing: 2px;
        cursor: pointer; box-shadow: 0 10px 30px rgba(6, 182, 212, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); margin-top: auto;
    }
    .orb-btn:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 15px 40px rgba(99, 102, 241, 0.4); }

    /* Autocomplete */
    .searchable-select { position: relative; }
    .searchable-dropdown {
        position: absolute; top: 100%; left: 0; right: 0; max-height: 200px; overflow-y: auto;
        background: var(--deck-bg); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; margin-top: 0.2rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5); z-index: 1000; display: none;
    }
    .searchable-dropdown.show { display: block; }
    .dropdown-item { padding: 0.6rem 1rem; cursor: pointer; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.8rem; }
    .dropdown-item:hover { background: rgba(6, 182, 212, 0.1); color: var(--neon-cyan); }
    
    /* Toggle switches & Vas tags */
    .cyber-switch { position: relative; display: inline-block; width: 36px; height: 18px; }
    .cyber-switch input { opacity: 0; width: 0; height: 0; }
    .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(255,255,255,0.1); transition: .4s; border-radius: 34px; }
    .slider:before { position: absolute; content: ""; height: 12px; width: 12px; left: 3px; bottom: 3px; background-color: var(--text-dim); transition: .4s; border-radius: 50%; }
    input:checked + .slider { background-color: rgba(6, 182, 212, 0.2); border: 1px solid var(--neon-cyan); }
    input:checked + .slider:before { transform: translateX(18px); background-color: var(--neon-cyan); box-shadow: 0 0 10px var(--neon-cyan); }
    
    .vas-tag {
        display: inline-block; padding: 0.4rem 0.6rem; border-radius: 6px; background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.1); font-size: 0.7rem; font-weight: 600; color: var(--text-dim);
        cursor: pointer; transition: all 0.2s; margin-right: 0.4rem; margin-bottom: 0.4rem;
    }
    .vas-tag.selected { background: rgba(99, 102, 241, 0.15); border-color: var(--neon-indigo); color: white; }
    
    .cyber-btn-outline {
        background: transparent; border: 1px dashed rgba(255,255,255,0.2); color: var(--text-dim);
        padding: 0.5rem; border-radius: 8px; font-weight: 600; font-size: 0.75rem;
        text-transform: uppercase; letter-spacing: 1px; cursor: pointer; transition: all 0.2s;
    }
    .cyber-btn-outline:hover { background: rgba(255,255,255,0.05); color: white; border-style: solid; border-color: var(--neon-cyan); }
    
    .mode-pill-container {
        display: inline-flex; background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255,255,255,0.05);
        border-radius: 40px; padding: 4px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.5);
    }
    .mode-pill {
        padding: 0.4rem 1rem; border-radius: 30px; font-weight: 700; font-size: 0.7rem;
        color: var(--text-dim); cursor: pointer; transition: all 0.3s;
    }
    .mode-pill.active {
        background: linear-gradient(135deg, var(--neon-indigo), var(--neon-cyan)); color: white;
    }
</style>"""

content = re.sub(old_styles_regex, new_styles, content, flags=re.DOTALL)

# Replace the form body
form_regex = r'<div class="intel-fade-in".*?</form>\s*</div>'
if '<div class="intel-fade-in"' not in content:
    form_regex = r'<div class="hero-search-section intel-fade-in".*?</form>\s*</div>'
    if '<div class="hero-search-section intel-fade-in"' not in content:
        form_regex = r'<div class="command-deck-container".*?</form>\s*</div>'

new_form = """<div class="intel-fade-in" style="animation-delay: 0.1s;">
    <!-- Offline Quote Notice -->
    <div class="alert shadow-sm" id="offlineBanner" style="display: none; margin-bottom: 2rem; background: rgba(255, 183, 77, 0.1); border: 1px solid rgba(255, 183, 77, 0.3); border-left: 4px solid #ffb74d; border-radius: 12px; color: #fff;">
        <div class="d-flex align-items-center p-3">
            <i class="bi bi-exclamation-triangle-fill fs-4 text-warning me-3"></i>
            <div>
                <span class="fw-bold d-block" style="font-size: 1.1rem; color: #ffb74d;">Direct Office Contact Required</span>
                <span id="offlineBannerText" style="font-size: 0.9rem; color: rgba(255,255,255,0.7);">Air freight quotes require direct contact with our office for personalized rates and service.</span>
            </div>
            <button type="button" class="btn ms-auto fw-bold" style="background: #ffb74d; color: #000; border-radius: 8px;">📞 Contact Us</button>
        </div>
    </div>

    <form action="{{ url_for('customer.rates') }}" method="POST" id="wizardSearchForm">
        <input type="hidden" name="service_type" id="wiz_hidden_service_type" value="LCL">
        <input type="hidden" name="transport_mode" id="hidden_transport_mode" value="SEA">
        
        <div class="command-deck-container" id="mainFormContent">
            <div class="deck-content">

                <!-- 3 SECTION LAYOUT -->
                <div class="row g-4">
                    
                    <!-- SECTION 1: ROUTE -->
                    <div class="col-lg-4">
                        <div class="section-card">
                            <div class="section-header">
                                <div class="section-title"><i class="bi bi-geo-alt"></i> Route</div>
                                <div class="section-subtitle">Origin → Destination</div>
                            </div>
                            
                            <div class="cyber-input-group mb-4">
                                <select class="cyber-input" style="color:#000;" onchange="setTransportMode(this.value)">
                                    <option value="SEA">Sea Freight</option>
                                    <option value="AIR">Air Freight</option>
                                    <option value="RAIL">Rail Freight</option>
                                </select>
                            </div>
                            
                            <div class="cyber-input-group">
                                <label class="cyber-label">Origin (POL) <span class="text-danger">*</span></label>
                                <div class="searchable-select">
                                    <input type="text" class="cyber-input" id="wizOriginLocation" placeholder="Port of Loading..." onfocus="showWizDropdown('origin')" oninput="filterWizLocations('origin')" autocomplete="off" required>
                                    <div class="searchable-dropdown" id="wizOriginDropdown"></div>
                                </div>
                                <input type="hidden" name="origin" id="wiz_hidden_origin">
                            </div>

                            <div class="cyber-input-group">
                                <label class="cyber-label">Destination (POD) <span class="text-danger">*</span></label>
                                <div class="searchable-select">
                                    <input type="text" class="cyber-input" id="wizDestLocation" placeholder="Port of Discharge..." onfocus="showWizDropdown('dest')" oninput="filterWizLocations('dest')" autocomplete="off" required>
                                    <div class="searchable-dropdown" id="wizDestDropdown"></div>
                                </div>
                                <input type="hidden" name="destination" id="wiz_hidden_dest">
                            </div>

                            <div class="cyber-input-group mb-0 mt-4">
                                <label class="cyber-label">ETD (Cargo Ready)</label>
                                <input type="date" class="cyber-input" name="cargo_ready_date" required>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION 2: CARGO -->
                    <div class="col-lg-4">
                        <div class="section-card">
                            <div class="d-flex justify-content-between align-items-center mb-2 border-bottom border-secondary pb-3" style="border-color: rgba(255,255,255,0.05) !important;">
                                <div class="section-header mb-0">
                                    <div class="section-title"><i class="bi bi-box-seam"></i> Cargo</div>
                                    <div class="section-subtitle">What are you shipping?</div>
                                </div>
                                <div class="mode-pill-container" style="transform: scale(0.8); transform-origin: right;">
                                    <div class="mode-pill active" id="tab_lcl" onclick="setWizService('LCL')">LCL</div>
                                    <div class="mode-pill" id="tab_fcl" onclick="setWizService('FCL')">FCL</div>
                                </div>
                            </div>

                            <div style="flex: 1; overflow-y: auto; overflow-x: hidden; padding-right: 5px;" id="cargoScrollArea">
                                <div id="wiz_lcl_section" class="pt-3">
                                    <div id="wiz_lcl_rows"></div>
                                    <button type="button" class="cyber-btn-outline w-100" onclick="addWizLCLRow()">+ Add Commodity</button>
                                </div>

                                <div id="wiz_fcl_section" style="display:none;" class="pt-3">
                                    <div id="wiz_fcl_rows"></div>
                                    <button type="button" class="cyber-btn-outline w-100" onclick="addWizFCLRow()">+ Add Container</button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- SECTION 3: OPTIONS & SUBMIT -->
                    <div class="col-lg-4">
                        <div class="section-card">
                            <div class="section-header">
                                <div class="section-title"><i class="bi bi-gear"></i> Services</div>
                                <div class="section-subtitle">Select services</div>
                            </div>
                            
                            <div class="cyber-input-group">
                                <label class="cyber-label">Incoterm <span class="text-danger">*</span></label>
                                <select class="cyber-input" id="wizIncoterm" name="freight_terms" required>
                                    <option value="" style="color:#000;">Select trade term...</option>
                                    <option value="FCA" style="color:#000;">FCA - Free Carrier</option>
                                    <option value="FOB" style="color:#000;">FOB - Free On Board</option>
                                    <option value="CIF" style="color:#000;">CIF - Cost, Insurance & Freight</option>
                                    <option value="DAP" style="color:#000;">DAP - Delivered At Place</option>
                                    <option value="DDP" style="color:#000;">DDP - Delivered Duty Paid</option>
                                </select>
                            </div>

                            <div class="cyber-input-group mb-4">
                                <label class="cyber-label">Value Added Services</label>
                                <div>
                                    <div class="vas-tag" onclick="toggleVas(this)"><input type="checkbox" name="vas[]" value="Customs" class="d-none"> Customs Clearance</div>
                                    <div class="vas-tag" onclick="toggleVas(this)"><input type="checkbox" name="vas[]" value="Insurance" class="d-none"> Cargo Insurance</div>
                                    <div class="vas-tag" onclick="toggleVas(this)"><input type="checkbox" name="vas[]" value="Pickup" class="d-none"> Origin Pickup</div>
                                    <div class="vas-tag" onclick="toggleVas(this)"><input type="checkbox" name="vas[]" value="Delivery" class="d-none"> Destination Delivery</div>
                                </div>
                            </div>

                            <!-- Final Button -->
                            <button type="submit" class="orb-btn mt-auto">
                                Request Quotes <i class="bi bi-arrow-right-circle ms-2"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- PANORAMIC ROUTE MAP -->
                <div class="panoramic-map-container shadow-lg">
                    <div class="map-overlay-text"><i class="bi bi-radar"></i> Live Lane Mapping</div>
                    <div id="globalRouteMap"></div>
                </div>

            </div>
        </div>
    </form>
</div>"""

content = re.sub(form_regex, new_form, content, flags=re.DOTALL)


# Add custom JS logic
custom_js = """
    let globalRouteMap;
    let originMarker, destMarker, routeLine;

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize Global Route Map
        const mapOptions = {
            center: [20.0, 40.0], zoom: 2, attributionControl: false, zoomControl: true,
            scrollWheelZoom: false
        };
        
        if (document.getElementById('globalRouteMap')) {
            globalRouteMap = L.map('globalRouteMap', mapOptions);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(globalRouteMap);

            document.getElementById('wizOriginLocation').addEventListener('blur', updateMapRoute);
            document.getElementById('wizDestLocation').addEventListener('blur', updateMapRoute);
        }
    });

    function updateMapRoute() {
        if (!globalRouteMap) return;
        
        const originVal = document.getElementById('wizOriginLocation').value;
        const destVal = document.getElementById('wizDestLocation').value;
        
        if (originMarker) globalRouteMap.removeLayer(originMarker);
        if (destMarker) globalRouteMap.removeLayer(destMarker);
        if (routeLine) globalRouteMap.removeLayer(routeLine);
        
        let originLatlng = null;
        let destLatlng = null;

        if (originVal.length > 2) {
            // Mock coord
            originLatlng = [22.5, 114.0]; 
            originMarker = L.circleMarker(originLatlng, {radius: 6, color: '#06b6d4', fillColor: '#06b6d4', fillOpacity: 1}).addTo(globalRouteMap);
        }
        
        if (destVal.length > 2) {
            // Mock coord
            destLatlng = [53.5, 9.9]; 
            destMarker = L.circleMarker(destLatlng, {radius: 6, color: '#f43f5e', fillColor: '#f43f5e', fillOpacity: 1}).addTo(globalRouteMap);
        }
        
        if (originLatlng && destLatlng) {
            routeLine = L.polyline([originLatlng, destLatlng], {
                color: '#6366f1',
                weight: 3,
                dashArray: '5, 10',
                opacity: 0.8
            }).addTo(globalRouteMap);
            globalRouteMap.fitBounds(routeLine.getBounds(), {padding: [50, 50]});
        } else if (originLatlng) {
            globalRouteMap.setView(originLatlng, 4);
        } else if (destLatlng) {
            globalRouteMap.setView(destLatlng, 4);
        }
    }

    function setTransportMode(mode) {
        document.getElementById('hidden_transport_mode').value = mode;
        const banner = document.getElementById('offlineBanner');
        const formContent = document.getElementById('mainFormContent');
        
        if (mode === 'AIR' || mode === 'RAIL') {
            document.getElementById('offlineBannerText').textContent = `${mode === 'AIR' ? 'Air' : 'Rail'} freight quotes require direct contact with our office for personalized rates and service.`;
            banner.style.display = 'block';
            formContent.style.opacity = '0.3';
            formContent.style.pointerEvents = 'none';
        } else {
            banner.style.display = 'none';
            formContent.style.opacity = '1';
            formContent.style.pointerEvents = 'auto';
        }
    }
    
    function toggleVas(el) {
        el.classList.toggle('selected');
        const cb = el.querySelector('input');
        cb.checked = !cb.checked;
    }
"""
content = content.replace("function toggleTransportMode() {", custom_js + "\n    function old_toggleTransportMode() {")
content = re.sub(r'let mapOrigin, mapDest;.*?\}\);', '', content, flags=re.DOTALL) # Remove old map logic

with open('d:/FTL-DEV/app/templates/customer/rates.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("rates.html Command Deck UI (3-sections + Panoramic Map) applied.")
