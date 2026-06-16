import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the circle markers with custom DivIcons
target_origin = "sideOriginMarker = L.circleMarker(originLatlng, {radius: 6, color: '#2563eb', fillColor: '#2563eb', fillOpacity: 1}).addTo(sideMap);"
replacement_origin = """
            const originIcon = L.divIcon({
                className: 'custom-div-icon',
                html: "<div style='background-color:#2563eb; width:20px; height:20px; border-radius:50%; border:3px solid white; box-shadow: 0 0 10px rgba(37,99,235,0.8); display:flex; justify-content:center; align-items:center;'><span style='color:white; font-size:10px; font-weight:bold;'>O</span></div>",
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            sideOriginMarker = L.marker(originLatlng, {icon: originIcon}).addTo(sideMap);
"""
content = content.replace(target_origin, replacement_origin)

target_dest = "sideDestMarker = L.circleMarker(destLatlng, {radius: 6, color: '#dc2626', fillColor: '#dc2626', fillOpacity: 1}).addTo(sideMap);"
replacement_dest = """
            const destIcon = L.divIcon({
                className: 'custom-div-icon',
                html: "<div style='background-color:#dc2626; width:20px; height:20px; border-radius:50%; border:3px solid white; box-shadow: 0 0 10px rgba(220,38,38,0.8); display:flex; justify-content:center; align-items:center;'><span style='color:white; font-size:10px; font-weight:bold;'>D</span></div>",
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            sideDestMarker = L.marker(destLatlng, {icon: destIcon}).addTo(sideMap);
"""
content = content.replace(target_dest, replacement_dest)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Custom markers applied.")
