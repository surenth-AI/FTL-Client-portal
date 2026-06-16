import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target = """                        <div>
                            <label class="premium-label required">Estimated Departure Date (ETD)</label>
                            <input type="date" class="premium-input" id="wizCargoReadyDate" name="cargo_ready_date" required>
                        </div>

                        <div class="text-end mt-4 pt-3 border-top">
                            <button type="button" class="btn btn-primary px-4 fw-bold" onclick="openPanel(2)">Next Step <i class="bi bi-chevron-right"></i></button>
                        </div>"""

replacement = """                        <div>
                            <label class="premium-label required">Estimated Departure Date (ETD)</label>
                            <input type="date" class="premium-input" id="wizCargoReadyDate" name="cargo_ready_date" required>
                        </div>
                        </div> <!-- Closing offlineDisabledArea1 -->

                        <div class="text-end mt-4 pt-3 border-top">
                            <button type="button" class="btn btn-primary px-4 fw-bold" onclick="openPanel(2)">Next Step <i class="bi bi-chevron-right"></i></button>
                        </div>"""

content = content.replace(target, replacement)

# I should also remove the redundant JS and HTML I injected in patch_transport.py 
# because there's already an offlineServiceBanner doing the exact same thing!
target_redundant_html = """                                <select class="premium-input" name="transport_mode" id="wizTransportMode" required>
                                    <option value="SEA">Sea Freight</option>
                                    <option value="AIR">Air Freight</option>
                                    <option value="ROAD">Road Freight</option>
                                </select>
                                <div id="transportModeAlert" style="display:none;"></div>"""
replacement_redundant_html = """                                <select class="premium-input" name="transport_mode" id="wizTransportMode" required>
                                    <option value="SEA">Sea Freight</option>
                                    <option value="AIR">Air Freight</option>
                                    <option value="ROAD">Road Freight</option>
                                </select>"""
content = content.replace(target_redundant_html, replacement_redundant_html)

# And remove my redundant JS
target_redundant_js = """    // Transport Mode logic
    document.getElementById('wizTransportMode').addEventListener('change', function() {
        const mode = this.value;
        const alertBox = document.getElementById('transportModeAlert');
        const submitBtn = document.querySelector('button[type="submit"]'); // Find the Request Quotes button
        
        if (mode === 'AIR' || mode === 'ROAD') {
            const modeName = mode === 'AIR' ? 'Air Freight' : 'Road Freight';
            alertBox.innerHTML = `
                <div class="alert alert-warning d-flex align-items-center mt-3 shadow-sm" role="alert" style="border-left: 4px solid #f59e0b; background: #fffbeb; border-radius: 8px;">
                    <i class="bi bi-exclamation-circle-fill fs-3 text-warning me-3"></i>
                    <div>
                        <h6 class="fw-bold mb-1 text-dark">${modeName} - Contact Our Office</h6>
                        <p class="mb-2 text-dark small" style="opacity: 0.8;">${modeName} quotes are not currently available online. Please contact our office for specific routing and pricing.</p>
                        <button type="button" class="btn btn-sm btn-dark fw-bold px-3" onclick="alert('Please contact us:\\n\\nEmail: quotes@fasttransitline.com\\nPhone: +1 (555) 123-4567\\n\\nOur team will respond within 24 hours.')"><i class="bi bi-telephone-fill me-2"></i>Contact Us</button>
                    </div>
                </div>
            `;
            alertBox.style.display = 'block';
            if (submitBtn) submitBtn.disabled = true; // Prevent submission
        } else {
            alertBox.style.display = 'none';
            if (submitBtn) submitBtn.disabled = false;
        }
    });"""

content = content.replace(target_redundant_js, "")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed unclosed div and removed redundant injected code.")
