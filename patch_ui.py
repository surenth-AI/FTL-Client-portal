import re

with open('d:/FTL-DEV/app/templates/customer/rates_new.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Cargo Item HTML to include name attributes for LCL
cargo_item_regex = r'<div class="cargo-item-header">(.*?)<label for="\${itemId}-stackable">Stackable</label>'
new_cargo_item = """
                <div class="cargo-item-header">
                    <div class="cargo-item-title">Cargo Item #${cargoItemCounter}</div>
                    ${cargoItemCounter > 1 ? `<button type="button" class="remove-btn" onclick="removeCargoItem('${itemId}')">Remove</button>` : ''}
                </div>

                <div class="form-group" style="margin-bottom: 1rem;">
                    <label class="form-label">Unit of Measurement</label>
                    <div class="unit-toggle">
                        <button type="button" class="unit-option active" onclick="setUnit('${itemId}', 'metric')">Metric (kg/m³/cm)</button>
                        <button type="button" class="unit-option" onclick="setUnit('${itemId}', 'imperial')">Imperial (lbs/ft³/in)</button>
                    </div>
                </div>

                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Total Pieces <span class="required">*</span></label>
                        <input type="number" name="item_qty[]" class="form-input" placeholder="0" min="1" value="1" required 
                               id="${itemId}-pieces" oninput="updateTotals('${itemId}')">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Package Type <span class="required">*</span></label>
                        <select name="item_type[]" class="form-select" required>
                            <option value="">Select package type</option>
                            <option value="Pallet">Pallets</option>
                            <option value="Box">Boxes/Crates</option>
                            <option value="Drum">Drums</option>
                            <option value="Bag">Bags</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Goods Type <span class="required">*</span></label>
                        <select name="item_desc[]" class="form-select" id="${itemId}-goods" required>
                            <option value="commercial">Commercial Cargo</option>
                            <option value="personal" disabled style="color: #94a3b8;">Personal Effects (Upon Request)</option>
                            <option value="hazardous">Hazardous Materials</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-grid" style="grid-template-columns: repeat(2, 1fr);">
                    <div class="form-group">
                        <label class="form-label">Total Weight <span class="required">*</span></label>
                        <input type="number" name="item_weight[]" class="form-input" step="0.01" required 
                               id="${itemId}-weight" oninput="updateTotals('${itemId}')"
                               placeholder="0.00 kg">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Total Volume <span class="required">*</span></label>
                        <input type="number" name="item_volume[]" class="form-input" step="0.01" required 
                               id="${itemId}-volume" oninput="updateTotals('${itemId}')"
                               placeholder="0.00 m³">
                    </div>
                </div>

                <div class="checkbox-group">
                    <input type="checkbox" id="${itemId}-stackable" checked onchange="toggleStackable('${itemId}')">
                    <label for="${itemId}-stackable">Stackable</label>
"""
content = re.sub(cargo_item_regex, new_cargo_item, content, flags=re.DOTALL)

# Add name to Incoterm
content = content.replace('id="incoterm"', 'id="incoterm" name="freight_terms"')

# Make sure buttons inside forms don't accidentally submit
content = content.replace('<button class="', '<button type="button" class="')
content = content.replace('<button type="button" type="button"', '<button type="button"')
content = content.replace('<button type="button" class="btn btn-primary" onclick="saveRoute()"', '<button type="button" class="btn btn-primary" onclick="saveRoute()"')

# Fix filterLocations and selectLocation
filter_script_replacement = """
        function filterLocations(locationType) {
            const country = document.getElementById(locationType + 'Country').value;
            const type = document.getElementById(locationType + 'Type').value;
            const searchTerm = document.getElementById(locationType + 'Location').value.toLowerCase();
            const dropdown = document.getElementById(locationType + 'Dropdown');

            const isOrig = locationType === 'origin';
            const locations = isOrig ? databaseOrigins : databaseDestinations;
            
            const filtered = locations.filter(l => l.toLowerCase().includes(searchTerm));

            if (filtered.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-no-results">No results found</div>';
            } else {
                dropdown.innerHTML = filtered.map(loc => {
                    return `
                        <div class="dropdown-item" onclick="selectLocation('${locationType}', '${loc.replace(/'/g, "\\'")}')">
                            <div class="dropdown-item-name">${loc}</div>
                        </div>
                    `;
                }).join('');
            }

            dropdown.classList.add('show');
        }

        function selectLocation(locationType, fullName) {
            selectedLocations[locationType] = { name: fullName };
            document.getElementById(locationType + 'Location').value = fullName;
            document.getElementById(locationType + 'Dropdown').classList.remove('show');
        }
"""

content = re.sub(r'function filterLocations\(locationType\).*?document\.getElementById\(locationType \+ \'Dropdown\'\)\.classList\.remove\(\'show\'\);[\s\n]+}', filter_script_replacement, content, flags=re.DOTALL)

with open('d:/FTL-DEV/app/templates/customer/rates.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched successfully')
