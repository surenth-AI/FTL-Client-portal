import re

def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        new_booking = f.read()

    with open('app/templates/customer/rates_new.html', 'r', encoding='utf-8') as f:
        rates_new = f.read()

    # Extract the origin grid
    origin_grid_match = re.search(r'(<h3 class=\"route-section-title\">📍 Origin</h3>\s*)(<div class=\"form-grid\">.*?</div>\s*</div>)', rates_new, re.DOTALL)
    origin_grid = origin_grid_match.group(2) if origin_grid_match else ""
    
    # Extract the destination grid
    dest_grid_match = re.search(r'(<h3 class=\"route-section-title\">📍 Destination</h3>\s*)(<div class=\"form-grid\">.*?</div>\s*</div>)', rates_new, re.DOTALL)
    dest_grid = dest_grid_match.group(2) if dest_grid_match else ""

    if not origin_grid or not dest_grid:
        print("Could not find origin/dest grid in rates_new")
        return

    # Replace origin grid in new_booking
    new_booking = re.sub(
        r'(<h3 class=\"route-section-title\">📍 Origin.*?</h3>\s*)<div class=\"form-grid\">.*?</div>(\s*</div>\s*<div class=\"route-section\">\s*<h3 class=\"route-section-title\">📍 Destination)',
        r'\g<1>' + origin_grid + r'\g<2>',
        new_booking,
        flags=re.DOTALL
    )

    # Replace destination grid in new_booking
    new_booking = re.sub(
        r'(<h3 class=\"route-section-title\">📍 Destination.*?</h3>\s*)<div class=\"form-grid\">.*?</div>(\s*</div>\s*<div class=\"route-section\">\s*<h3 class=\"route-section-title\">🚢 Sailing)',
        r'\g<1>' + dest_grid + r'\g<2>',
        new_booking,
        flags=re.DOTALL
    )

    # Inject the Location scripts and locationData from rates_new.html if not already there
    if 'const locationData = {' not in new_booking:
        js_to_inject = """
        // ---- Injected Location Data & Functions ----
        const locationData = {
            cities: {
                'US': [
                    { name: 'New York', zipcode: '10001', state: 'NY' },
                    { name: 'Los Angeles', zipcode: '90001', state: 'CA' },
                    { name: 'Chicago', zipcode: '60601', state: 'IL' },
                    { name: 'Houston', zipcode: '77001', state: 'TX' },
                    { name: 'Miami', zipcode: '33101', state: 'FL' },
                ],
                'CN': [
                    { name: 'Shanghai', zipcode: '200000' },
                    { name: 'Beijing', zipcode: '100000' },
                    { name: 'Shenzhen', zipcode: '518000' },
                    { name: 'Guangzhou', zipcode: '510000' },
                ],
                'GB': [
                    { name: 'London', zipcode: 'EC1A' },
                    { name: 'Manchester', zipcode: 'M1' },
                    { name: 'Birmingham', zipcode: 'B1' },
                ],
                'ES': [
                    { name: 'Barcelona', zipcode: '08001' },
                    { name: 'Madrid', zipcode: '28001' },
                    { name: 'Valencia', zipcode: '46001' },
                ],
                'DE': [
                    { name: 'Hamburg', zipcode: '20095' },
                    { name: 'Berlin', zipcode: '10115' },
                ],
                'BE': [
                    { name: 'Antwerp', zipcode: '2000' },
                    { name: 'Brussels', zipcode: '1000' },
                ],
                'IN': [
                    { name: 'Mumbai', zipcode: '400001' },
                    { name: 'Nhava Sheva', zipcode: '400707' },
                ],
                'NL': [
                    { name: 'Rotterdam', zipcode: '3011' },
                    { name: 'Amsterdam', zipcode: '1011' },
                ],
                'FR': [
                    { name: 'Paris', zipcode: '75000' },
                    { name: 'Le Havre', zipcode: '76600' },
                ]
            },
            ports: {
                'US': [
                    { name: 'Port of Los Angeles', uncode: 'USLAX' },
                    { name: 'Port of Long Beach', uncode: 'USLGB' },
                    { name: 'Port of New York', uncode: 'USNYC' },
                    { name: 'Port of Savannah', uncode: 'USSAV' },
                ],
                'CN': [
                    { name: 'Port of Shanghai', uncode: 'CNSHA' },
                    { name: 'Port of Shenzhen', uncode: 'CNSZX' },
                    { name: 'Port of Ningbo', uncode: 'CNNGB' },
                ],
                'GB': [
                    { name: 'Port of Felixstowe', uncode: 'GBFXT' },
                    { name: 'Port of Southampton', uncode: 'GBSOU' },
                    { name: 'Port of London', uncode: 'GBLGP' },
                ],
                'ES': [
                    { name: 'Port of Barcelona', uncode: 'ESBCN' },
                    { name: 'Port of Valencia', uncode: 'ESVLC' },
                ],
                'DE': [
                    { name: 'Port of Hamburg', uncode: 'DEHAM' },
                    { name: 'Port of Bremerhaven', uncode: 'DEBRV' },
                ],
                'BE': [
                    { name: 'Port of Antwerp', uncode: 'BEANR' },
                    { name: 'Port of Zeebrugge', uncode: 'BEZEE' },
                ],
                'IN': [
                    { name: 'Nhava Sheva', uncode: 'INNSA' },
                    { name: 'Mundra', uncode: 'INMUN' },
                ],
                'NL': [
                    { name: 'Port of Rotterdam', uncode: 'NLRTM' },
                ],
                'FR': [
                    { name: 'Port of Le Havre', uncode: 'FRLEH' },
                    { name: 'Port of Marseille', uncode: 'FRMRS' },
                ]
            }
        };

        const selectedLocations = {
            origin: null,
            dest: null
        };

        function handleLocationTypeChange(locationType) {
            const type = document.getElementById(locationType + 'Type').value;
            const label = document.getElementById(locationType + 'LocationLabel');
            const input = document.getElementById(locationType + 'Location');

            if (type === 'door') {
                if (label) label.innerHTML = 'City <span class="required">*</span>';
                if (input) input.placeholder = 'Search by city name or zip code';
            } else {
                if (label) label.innerHTML = 'Port <span class="required">*</span>';
                if (input) input.placeholder = 'Search by port name or UN code';
            }

            // Clear selection
            selectedLocations[locationType] = null;
            if (input) input.value = '';
        }

        function handleCountryChange(locationType) {
            // Clear location when country changes
            selectedLocations[locationType] = null;
            const locInput = document.getElementById(locationType + 'Location');
            if (locInput) locInput.value = '';
        }

        function showDropdown(locationType) {
            const countryEl = document.getElementById(locationType + 'Country');
            const country = countryEl ? countryEl.value : null;
            if (!country) {
                alert('Please select a country first');
                return;
            }
            filterLocations(locationType);
        }

        function filterLocations(locationType) {
            const country = document.getElementById(locationType + 'Country').value;
            const type = document.getElementById(locationType + 'Type').value;
            const inputEl = document.getElementById(locationType + 'Location');
            const searchTerm = inputEl ? inputEl.value.toLowerCase() : '';
            const dropdown = document.getElementById(locationType + 'Dropdown');
            if (!dropdown) return;

            if (!country) {
                dropdown.classList.remove('show');
                return;
            }

            const dataKey = type === 'door' ? 'cities' : 'ports';
            const locations = locationData[dataKey][country] || [];

            const filtered = locations.filter(loc => {
                if (type === 'door') {
                    return loc.name.toLowerCase().includes(searchTerm) ||
                        loc.zipcode.toLowerCase().includes(searchTerm);
                } else {
                    const uncode = loc.uncode || '';
                    return loc.name.toLowerCase().includes(searchTerm) ||
                        uncode.toLowerCase().includes(searchTerm);
                }
            });

            if (filtered.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-no-results">No results found</div>';
            } else {
                dropdown.innerHTML = filtered.map(loc => {
                    const code = type === 'door' ? loc.zipcode : loc.uncode;
                    return `
                        <div class="dropdown-item" onclick="selectLocation('${locationType}', '${loc.name.replace(/'/g, "\\'")}', '${code.replace(/'/g, "\\'")}')">
                            <div class="dropdown-item-name">${loc.name}</div>
                            <div class="dropdown-item-code">${code}</div>
                        </div>
                    `;
                }).join('');
            }

            dropdown.classList.add('show');
        }

        function selectLocation(locationType, name, code) {
            selectedLocations[locationType] = { name, code };
            const input = document.getElementById(locationType + 'Location');
            if (input) input.value = `${name} (${code})`;
            const dropdown = document.getElementById(locationType + 'Dropdown');
            if (dropdown) dropdown.classList.remove('show');
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.searchable-select')) {
                document.querySelectorAll('.searchable-dropdown').forEach(d => d.classList.remove('show'));
            }
        });
        // ------------------------------------------
"""
        new_booking = new_booking.replace('<script>', '<script>' + js_to_inject)

    # 5. Fix useQuote logic to also extract and set the country and location properly.
    # We will just replace the existing `useQuote` function in new_booking.html with one that populates the country.
    # The existing useQuote uses document.getElementById('originCountry').value = q.originCountry;
    # We can just update it so that if q.originCountry is set, it also sets selectedLocations.

    new_use_quote = """
        function useQuote(ref) {
            linkedQuote = ref;
            const q = quoteData[ref];
            document.getElementById('quotePicker').classList.remove('show');
            document.getElementById('linkedQuoteBanner').classList.add('show');
            document.getElementById('linkedRef').textContent = ref;
            document.getElementById('linkedRouteText').textContent = q.route;
            document.getElementById('linkedPrice').textContent = q.price;
            
            // Extract country from location if not provided
            let orgCountry = q.originCountry;
            let destCountry = q.destCountry;
            
            // Extract from UNCODE e.g., (ESBCN) -> ES
            const orgMatch = q.originLocation.match(/\\(([A-Z]{2})[A-Z]{3}\\)/);
            if (orgMatch && !orgCountry) orgCountry = orgMatch[1];
            
            const destMatch = q.destLocation.match(/\\(([A-Z]{2})[A-Z]{3}\\)/);
            if (destMatch && !destCountry) destCountry = destMatch[1];

            // Prefill route
            document.getElementById('originType').value = q.originType || 'port';
            handleLocationTypeChange('origin');
            const oc = document.getElementById('originCountry');
            if (oc && orgCountry) oc.value = orgCountry;
            
            const ol = document.getElementById('originLocation');
            if (ol) ol.value = q.originLocation;
            if (orgCountry) {
                 selectedLocations.origin = { name: q.originLocation.split('(')[0].trim(), code: orgMatch ? (orgMatch[1]+orgMatch[2] || '') : '' };
            }

            document.getElementById('destType').value = q.destType || 'port';
            handleLocationTypeChange('dest');
            const dc = document.getElementById('destCountry');
            if (dc && destCountry) dc.value = destCountry;
            
            const dl = document.getElementById('destLocation');
            if (dl) dl.value = q.destLocation;
            if (destCountry) {
                 selectedLocations.dest = { name: q.destLocation.split('(')[0].trim(), code: destMatch ? (destMatch[1]+destMatch[2] || '') : '' };
            }

            document.getElementById('originFromQuoteTag').style.display = 'inline-block';
            document.getElementById('destFromQuoteTag').style.display = 'inline-block';
            
            // Update route section label
            const originText = q.originLocation;
            const destText = q.destLocation;
            document.getElementById('routeValue').textContent = `${originText} → ${destText}`;
            document.getElementById('routeValue').classList.remove('section-placeholder');
            document.getElementById('routeValue').classList.add('section-value');
            document.getElementById('routeSection').classList.add('completed');

            // Prefill cargo — ensure at least one item exists, then fill the first
            if (document.querySelectorAll('.cargo-item').length === 0) addCargoItem();
            const firstItem = document.querySelector('.cargo-item');
            const itemId = firstItem.id;
            const piecesEl = document.getElementById(`${itemId}-pieces`);
            if (piecesEl) piecesEl.value = q.pieces;
            
            const pkgEl = document.getElementById(`${itemId}-package`);
            if (pkgEl) pkgEl.value = q.packageType;
            
            const goodsEl = document.getElementById(`${itemId}-goods`);
            if (goodsEl) goodsEl.value = q.goodsType;
            
            const wEl = document.getElementById(`${itemId}-weight`);
            if (wEl) wEl.value = q.weight;
            
            const vEl = document.getElementById(`${itemId}-volume`);
            if (vEl) vEl.value = q.volume;
            
            document.getElementById('cargoFromQuoteTag').style.display = 'inline-block';
            updateDocumentRequirements();
            updateRateSummary();
            showAlert('Quote ' + ref + ' linked. Route and cargo details have been pre-filled — feel free to adjust them.');
        }
    """

    new_booking = re.sub(r'function useQuote\(ref\) \{.*?\}\s*function changeQuote', new_use_quote + '\n        function changeQuote', new_booking, flags=re.DOTALL)

    # Styles
    styles = '''
    .searchable-select { position: relative; margin-bottom: 1rem; }
    .searchable-dropdown {
        position: absolute; top: 100%; left: 0; right: 0;
        max-height: 220px; overflow-y: auto;
        background: var(--bg-white);
        border: 1px solid var(--border-color);
        border-radius: 8px; margin-top: 0.5rem;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
        z-index: 1000; display: none;
    }
    .searchable-dropdown.show { display: block; animation: slideDown 0.2s; }
    .dropdown-item { padding: 0.75rem 1.25rem; cursor: pointer; transition: background 0.2s; border-bottom: 1px solid var(--border-color); }
    .dropdown-item:last-child { border-bottom: none; }
    .dropdown-item:hover { background: var(--hover-bg); }
    .dropdown-item-name { font-size: 0.85rem; font-weight: 600; }
    .dropdown-item-code { font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.1rem; }
    .dropdown-no-results { padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.875rem; }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
'''
    if '.searchable-dropdown.show' not in new_booking:
        new_booking = new_booking.replace('</style>', styles + '\n</style>')

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(new_booking)

    print("Successfully patched new_booking.html")

if __name__ == '__main__':
    main()
