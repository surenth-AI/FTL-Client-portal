import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Target to inject the alert box
target_html = """                                <select class="premium-input" name="transport_mode" id="wizTransportMode" required>
                                    <option value="SEA">Sea Freight</option>
                                    <option value="AIR">Air Freight</option>
                                    <option value="ROAD">Road Freight</option>
                                </select>"""

replacement_html = """                                <select class="premium-input" name="transport_mode" id="wizTransportMode" required>
                                    <option value="SEA">Sea Freight</option>
                                    <option value="AIR">Air Freight</option>
                                    <option value="ROAD">Road Freight</option>
                                </select>
                                <div id="transportModeAlert" style="display:none;"></div>"""

content = content.replace(target_html, replacement_html)

# Target to inject the Javascript
target_js = """    // Attach to existing blur events"""

replacement_js = """    // Transport Mode logic
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
    });

    // Attach to existing blur events"""

content = content.replace(target_js, replacement_js)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Transport mode logic injected successfully.")
