import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the map div height so Leaflet renders properly
target_div = '<div id="sideMap" style="flex: 1;'
replacement_div = '<div id="sideMap" style="height: 450px; flex: 1;'
content = content.replace(target_div, replacement_div)

# Change default view to Italy
target_view = 'sideMap = L.map(\'sideMap\').setView([20.0, 40.0], 2);'
replacement_view = 'sideMap = L.map(\'sideMap\').setView([41.8719, 12.5674], 5); // Italy'
content = content.replace(target_view, replacement_view)

# Add an invalidation step to make sure Leaflet resizes correctly inside hidden or expanding panels
target_listener = "document.addEventListener('DOMContentLoaded', function() {"
replacement_listener = """document.addEventListener('DOMContentLoaded', function() {
    // Add tab click listener to invalidate map size
    document.querySelectorAll('.header-section').forEach(tab => {
        tab.addEventListener('click', () => {
            setTimeout(() => { if(sideMap) sideMap.invalidateSize(); }, 300);
        });
    });
"""
content = content.replace(target_listener, replacement_listener)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed map height and set default view to Italy.")
