import re

with open('d:/FTL-DEV/view.html', 'r', encoding='utf-8') as f:
    view_content = f.read()

# Extract styles
style_match = re.search(r'(<style>.*?</style>)', view_content, re.DOTALL)
styles = style_match.group(1) if style_match else ""

# Extract body
body_match = re.search(r'<body>(.*?)<script>', view_content, re.DOTALL)
body = body_match.group(1) if body_match else ""

# Extract script
script_match = re.search(r'(<script>.*?</script>)', view_content, re.DOTALL)
script = script_match.group(1) if script_match else ""

rates_html = '{% extends "base.html" %}\n{% block title %}Search Rates - FTL{% endblock %}\n\n{% block content %}\n<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />\n\n' + styles + '\n\n<div class="container-fluid py-4">\n    <div class="row">\n        <!-- Accordion Form Area -->\n        <div class="col-lg-8">\n' + body + '\n        </div>\n        \n        <!-- Side Map Area -->\n        <div class="col-lg-4">\n            <div style="position: sticky; top: 2rem;">\n                <div class="card shadow-sm border-0" style="border-radius: 12px; overflow: hidden;">\n                    <div class="card-header bg-white border-bottom-0 pt-3 pb-0">\n                        <h6 class="fw-bold mb-0 text-primary"><i class="bi bi-map me-2"></i>Live Route Map</h6>\n                    </div>\n                    <div class="card-body p-3">\n                        <div id="sideMap" style="height: 500px; border-radius: 8px; border: 1px solid #e2e8f0; background: #f8fafc;"></div>\n                    </div>\n                </div>\n            </div>\n        </div>\n    </div>\n</div>\n\n' + script + '\n\n<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<script>\n    let sideMap;\n    let sideOriginMarker, sideDestMarker, sideRouteLine;\n\n    document.addEventListener("DOMContentLoaded", function() {\n        if(document.getElementById("sideMap")) {\n            sideMap = L.map("sideMap").setView([20.0, 40.0], 2);\n            L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png").addTo(sideMap);\n\n            const originInput = document.getElementById("originLocation");\n            const destInput = document.getElementById("destLocation");\n            \n            if(originInput) originInput.addEventListener("blur", updateSideMap);\n            if(destInput) destInput.addEventListener("blur", updateSideMap);\n        }\n    });\n\n    function updateSideMap() {\n        if(!sideMap) return;\n        \n        const originInput = document.getElementById("originLocation");\n        const destInput = document.getElementById("destLocation");\n        \n        const originVal = originInput ? originInput.value : "";\n        const destVal = destInput ? destInput.value : "";\n        \n        if (sideOriginMarker) sideMap.removeLayer(sideOriginMarker);\n        if (sideDestMarker) sideMap.removeLayer(sideDestMarker);\n        if (sideRouteLine) sideMap.removeLayer(sideRouteLine);\n        \n        let originLatlng = null;\n        let destLatlng = null;\n\n        if (originVal.length > 2) {\n            originLatlng = [22.5, 114.0]; \n            sideOriginMarker = L.circleMarker(originLatlng, {radius: 6, color: "#2563eb", fillColor: "#2563eb", fillOpacity: 1}).addTo(sideMap);\n        }\n        \n        if (destVal.length > 2) {\n            destLatlng = [53.5, 9.9]; \n            sideDestMarker = L.circleMarker(destLatlng, {radius: 6, color: "#dc2626", fillColor: "#dc2626", fillOpacity: 1}).addTo(sideMap);\n        }\n        \n        if (originLatlng && destLatlng) {\n            sideRouteLine = L.polyline([originLatlng, destLatlng], {\n                color: "#8b5cf6", weight: 3, dashArray: "5, 10", opacity: 0.8\n            }).addTo(sideMap);\n            sideMap.fitBounds(sideRouteLine.getBounds(), {padding: [30, 30]});\n        } else if (originLatlng) {\n            sideMap.setView(originLatlng, 4);\n        } else if (destLatlng) {\n            sideMap.setView(destLatlng, 4);\n        }\n    }\n</script>\n{% endblock %}\n'

with open('d:/FTL-DEV/app/templates/customer/rates.html', 'w', encoding='utf-8') as f:
    f.write(rates_html)

print("rates.html successfully rebuilt with accordion layout and side map.")
