import re

def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    js_logic = """
        // ---- API-based Location Data & Functions ----
        const apiCountries = {{ countries | tojson | safe }};
        window.fetchedPortsCache = { origin: {}, dest: {} };

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
            
            populateCountries(locationType, type);
        }

        function populateCountries(locationType, type) {
            const countrySelect = document.getElementById(locationType + 'Country');
            if (!countrySelect) return;
            const currentValue = countrySelect.value;
            countrySelect.innerHTML = '<option value="">Select country</option>';
            
            // Sort apiCountries by name, filtering out empty keys
            const sorted = [...apiCountries].filter(c => c.code && c.name).sort((a, b) => a.name.localeCompare(b.name));
            sorted.forEach(c => {
                const option = document.createElement('option');
                option.value = c.code;
                option.textContent = c.name;
                countrySelect.appendChild(option);
            });
            
            if (currentValue && sorted.some(c => c.code === currentValue)) {
                countrySelect.value = currentValue;
            }
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

        async function filterLocations(locationType) {
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

            if (type === 'door') {
                dropdown.classList.remove('show');
                selectedLocations[locationType] = { name: searchTerm, code: '' };
                return;
            }

            dropdown.innerHTML = '<div class="dropdown-item text-center text-muted"><div class="spinner-border spinner-border-sm" role="status" style="width: 1rem; height: 1rem;"></div> Loading ports...</div>';
            dropdown.classList.add('show');

            // Fetch from cache or API
            let locations = window.fetchedPortsCache[locationType][country];
            if (!locations) {
                try {
                    const resp = await fetch(`/customer/api/get-ports/${locationType}/${country}`);
                    if (resp.ok) {
                        locations = await resp.json();
                        window.fetchedPortsCache[locationType][country] = locations;
                    } else {
                        locations = [];
                    }
                } catch (e) {
                    console.error('Error fetching ports:', e);
                    locations = [];
                }
            }

            const filtered = locations.filter(loc => {
                const uncode = loc.code || '';
                return loc.name.toLowerCase().includes(searchTerm) ||
                    uncode.toLowerCase().includes(searchTerm);
            });

            if (filtered.length === 0) {
                dropdown.innerHTML = '<div class="dropdown-no-results">No results found</div>';
            } else {
                dropdown.innerHTML = filtered.map(loc => {
                    const code = loc.code || '';
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
        
        // Initialize dynamic countries on load
        document.addEventListener('DOMContentLoaded', function() {
            populateCountries('origin', 'port');
            populateCountries('dest', 'port');
        });
        // ------------------------------------------
"""
    # Find block to replace
    start = text.find('// ---- Injected Location Data & Functions ----')
    end = text.find('// ------------------------------------------')
    
    if start != -1 and end != -1:
        text = text[:start] + js_logic + text[end + len('// ------------------------------------------'):]
        with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Patched new_booking.html successfully")
    else:
        print("Could not find the JS block to replace.")

if __name__ == '__main__':
    main()
