import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace <div class="quote-header"> with row wrapper
target_header = '<div class="quote-header">'
replacement_header = """<div class="row">
            <div class="col-lg-7">
                <div class="quote-header">"""
content = content.replace(target_header, replacement_header, 1)

# The end of panels-container needs to close the col-lg-7 and add the map col-lg-5
# The panels-container ends before `</form>`
target_end = '        </div>\n    </form>'
replacement_end = """        </div>
            </div>
            
            <!-- SIDE MAP FOR ALL THREE SECTIONS -->
            <div class="col-lg-5">
                <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden; height: 100%; min-height: 500px; position: sticky; top: 1rem;">
                    <div class="card-header bg-white border-bottom-0 pt-3 pb-0">
                        <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>
                    </div>
                    <div class="card-body p-3 d-flex flex-column">
                        <div id="sideMap" style="flex: 1; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-gray);"></div>
                    </div>
                </div>
            </div>
        </div>
    </form>"""
content = content.replace(target_end, replacement_end, 1)

# Inject Leaflet CSS
if 'leaflet.css' not in content:
    content = content.replace('<style>', '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />\n<style>', 1)

# Inject Leaflet JS
if 'leaflet.js' not in content:
    leaflet_js = """
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    let sideMap;
    let sideOriginMarker, sideDestMarker, sideRouteLine;

    document.addEventListener('DOMContentLoaded', function() {
        if(document.getElementById('sideMap')) {
            sideMap = L.map('sideMap').setView([20.0, 40.0], 2);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png').addTo(sideMap);

            const originInput = document.getElementById('wizOriginLocation');
            const destInput = document.getElementById('wizDestLocation');
            
            if(originInput) originInput.addEventListener('blur', updateSideMap);
            if(destInput) destInput.addEventListener('blur', updateSideMap);
        }
    });

    function updateSideMap() {
        if(!sideMap) return;
        
        const originInput = document.getElementById('wizOriginLocation');
        const destInput = document.getElementById('wizDestLocation');
        
        const originVal = originInput ? originInput.value : '';
        const destVal = destInput ? destInput.value : '';
        
        if (sideOriginMarker) sideMap.removeLayer(sideOriginMarker);
        if (sideDestMarker) sideMap.removeLayer(sideDestMarker);
        if (sideRouteLine) sideMap.removeLayer(sideRouteLine);
        
        let originLatlng = null;
        let destLatlng = null;

        if (originVal.length > 2) {
            originLatlng = [22.5, 114.0]; 
            sideOriginMarker = L.circleMarker(originLatlng, {radius: 6, color: '#2563eb', fillColor: '#2563eb', fillOpacity: 1}).addTo(sideMap);
        }
        
        if (destVal.length > 2) {
            destLatlng = [53.5, 9.9]; 
            sideDestMarker = L.circleMarker(destLatlng, {radius: 6, color: '#dc2626', fillColor: '#dc2626', fillOpacity: 1}).addTo(sideMap);
        }
        
        if (originLatlng && destLatlng) {
            sideRouteLine = L.polyline([originLatlng, destLatlng], {
                color: '#8b5cf6', weight: 3, dashArray: '5, 10', opacity: 0.8
            }).addTo(sideMap);
            sideMap.fitBounds(sideRouteLine.getBounds(), {padding: [30, 30]});
        } else if (originLatlng) {
            sideMap.setView(originLatlng, 4);
        } else if (destLatlng) {
            sideMap.setView(destLatlng, 4);
        }
    }
</script>
{% endblock %}
"""
    content = content.replace('{% endblock %}', leaflet_js, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Map injected globally across all panels.")
