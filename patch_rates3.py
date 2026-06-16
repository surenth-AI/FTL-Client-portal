import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will append new JS functions at the end of the script block just before `</script>`
js_injection = """
    // ==========================================
    // Automated Data Fetching (Mock API)
    // ==========================================
    function triggerAutomatedDataFetch() {
        const originVal = document.getElementById('wizOriginLocation').value;
        const destVal = document.getElementById('wizDestLocation').value;
        
        if (originVal && originVal.length > 2) {
            // Mock fetching transport lanes to determine Import/Export
            console.log("Fetching Transport Lanes for origin:", originVal);
            const directionSelect = document.querySelector('select[name="direction"]');
            if (originVal.toLowerCase().includes('us') || originVal.toLowerCase().includes('united states')) {
                directionSelect.value = 'EXPORT';
            } else {
                directionSelect.value = 'IMPORT';
            }
        }
        
        if (originVal && destVal) {
            console.log("Validating route between", originVal, "and", destVal);
            // Mock Validation
            if (destVal.toLowerCase() === 'mars' || destVal.toLowerCase() === 'moon') {
                alert("Destination is not available for the chosen origin based on Transport Lanes.");
                document.getElementById('wizDestLocation').value = '';
            }
            
            // Mock fetching Value-Added Services
            console.log("Fetching Value-Added Services for trade link.");
            // e.g. Automatically check "Customs Clearance" if available
            const destChargesCheckbox = document.getElementById('wizIncludeDestCharges');
            if(destChargesCheckbox) {
                // If import to US, require dest charges
                if(destVal.toLowerCase().includes('us')) {
                    destChargesCheckbox.checked = true;
                    updateWizChargeStatus('dest');
                }
            }
        }
    }

    // Attach to existing blur events
    document.addEventListener('DOMContentLoaded', function() {
        const originInput = document.getElementById('wizOriginLocation');
        const destInput = document.getElementById('wizDestLocation');
        
        if(originInput) {
            originInput.addEventListener('blur', triggerAutomatedDataFetch);
        }
        if(destInput) {
            destInput.addEventListener('blur', triggerAutomatedDataFetch);
        }
    });
"""

content = content.replace('</script>\n{% endblock %}', js_injection + '</script>\n{% endblock %}')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Automated Data Fetching mock JS added.")
