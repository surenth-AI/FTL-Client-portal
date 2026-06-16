import re

with open('d:/FTL-DEV/view.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the styles
old_styles_regex = r'<style>.*?body \{.*?--primary-blue: var\(--primary-color\) !important;.*?</style>'
with open('d:/FTL-DEV/rewrite_rates.py', 'r', encoding='utf-8') as f:
    rewrite_script = f.read()

new_styles_match = re.search(r'new_styles = """(.*?)"""', rewrite_script, re.DOTALL)
if new_styles_match:
    new_styles = new_styles_match.group(1)
    content = re.sub(old_styles_regex, new_styles, content, flags=re.DOTALL)

# Replace the form body
form_regex = r'<div class="hero-search-section intel-fade-in".*?</form>\s*</div>'
new_form_match = re.search(r'new_form = """(.*?)"""', rewrite_script, re.DOTALL)
if new_form_match:
    new_form = new_form_match.group(1).replace("{{ url_for('customer.rates') }}", "#")
    content = re.sub(form_regex, new_form, content, flags=re.DOTALL)

# Add Leaflet JS
leaflet_script = """<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // Leaflet Maps Setup
    let mapOrigin, mapDest;
    document.addEventListener('DOMContentLoaded', function() {
        const mapOptions = {
            center: [20.0, 0.0], zoom: 1, attributionControl: false, zoomControl: false,
            dragging: false, scrollWheelZoom: false, doubleClickZoom: false, boxZoom: false
        };
        
        mapOrigin = L.map('mapOrigin', mapOptions);
        mapDest = L.map('mapDestination', mapOptions);
        
        const tileUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
        L.tileLayer(tileUrl).addTo(mapOrigin);
        L.tileLayer(tileUrl).addTo(mapDest);

        document.getElementById('wizOriginLocation').addEventListener('blur', function() {
            if(this.value.length > 2) {
                mapOrigin.setView([Math.random()*60, Math.random()*100], 4, {animate:true});
                L.circleMarker(mapOrigin.getCenter(), {radius:5, color:'#3b82f6'}).addTo(mapOrigin);
            }
        });
        document.getElementById('wizDestLocation').addEventListener('blur', function() {
            if(this.value.length > 2) {
                mapDest.setView([Math.random()*60, Math.random()*100], 4, {animate:true});
                L.circleMarker(mapDest.getCenter(), {radius:5, color:'#E11D48'}).addTo(mapDest);
            }
        });
    });
</script>"""

if "<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>" not in content:
    content = content.replace("<!-- ============================================================\n     RECENT QUOTATIONS & HISTORY", leaflet_script + "\n<!-- ============================================================\n     RECENT QUOTATIONS & HISTORY")

new_lcl_row_match = re.search(r'new_lcl_row = """(.*?)"""', rewrite_script, re.DOTALL)
if new_lcl_row_match:
    content = re.sub(r'function addWizLCLRow\(\) \{.*?document\.getElementById\(\'wiz_lcl_rows\'\)\.appendChild\(div\);\s*\}', new_lcl_row_match.group(1), content, flags=re.DOTALL)

new_fcl_row_match = re.search(r'new_fcl_row = """(.*?)"""', rewrite_script, re.DOTALL)
if new_fcl_row_match:
    content = re.sub(r'function addWizFCLRow\(\) \{.*?document\.getElementById\(\'wiz_fcl_rows\'\)\.appendChild\(div\);\s*\}', new_fcl_row_match.group(1), content, flags=re.DOTALL)

with open('d:/FTL-DEV/view.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("view.html rewritten successfully.")
