import re
import os

view_path = r'd:\FTL-DEV\view.html'
rates_path = r'd:\FTL-DEV\app\templates\customer\rates.html'

with open(view_path, 'r', encoding='utf-8') as f:
    view_html = f.read()

# 1. Extract Styles
style_match = re.search(r'<style>(.*?)</style>', view_html, re.DOTALL)
styles = style_match.group(1) if style_match else ""
styles = styles.replace(".main-content", ".rates-view-content")
styles = re.sub(r'font-family:.*?;', '', styles)

# Replace hardcoded blue colors and rgba with dynamic ones
styles = styles.replace("rgba(37, 99, 235, 0.1)", "color-mix(in srgb, var(--primary-color) 10%, transparent)")
styles = styles.replace("rgba(37, 99, 235, 0.3)", "color-mix(in srgb, var(--primary-color) 30%, transparent)")
styles = styles.replace("rgba(37, 99, 235, 0.05)", "color-mix(in srgb, var(--primary-color) 5%, transparent)")
styles = styles.replace("rgba(37, 99, 235, 0.15)", "color-mix(in srgb, var(--primary-color) 15%, transparent)")

# 2. Extract Javascript
script_match = re.search(r'<script>(.*?)</script>', view_html, re.DOTALL)
script_content = script_match.group(1) if script_match else ""

# Update Script Content to add name attributes to JS-generated HTML
script_content = script_content.replace('id="${itemId}-pieces"', 'id="${itemId}-pieces" name="item_qty[]"')

package_select_old = """                        <select class="form-select" required>
                            <option value="">Select package type</option>
                            <option value="pallets">Pallets</option>
                            <option value="boxes">Boxes/Crates</option>
                            <option value="drums">Drums</option>
                            <option value="bags">Bags</option>
                            <option value="other">Other</option>
                        </select>"""

package_select_new = """                        <select class="form-select" required name="item_type[]">
                            <option value="">Select package type</option>
                            ${packageTypes.map(p => `<option value="${p.code}">${p.name}</option>`).join('')}
                        </select>"""

script_content = script_content.replace(package_select_old, package_select_new)

script_content = script_content.replace('id="${itemId}-goods"', 'id="${itemId}-goods" name="goods_type[]"')
script_content = script_content.replace('id="${itemId}-weight"', 'id="${itemId}-weight" name="item_weight[]"')
script_content = script_content.replace('id="${itemId}-volume"', 'id="${itemId}-volume" name="item_volume[]"')

# Rename old functions to prevent collision
script_content = script_content.replace("function handleLocationTypeChange(locationType) {", "function handleLocationTypeChange_old(locationType) {")
script_content = script_content.replace("function filterLocations(locationType) {", "function filterLocations_old(locationType) {")

# Prefix with dynamic API values, country dictionary, and new dropdown-filling functions
prefix_content = """
// Dynamic ports from API passed by Flask
const apiOrigins = {{ origins_json | safe }};
const apiDestinations = {{ destinations_json | safe }};
const packageTypes = {{ package_types_json | safe }};
const containerTypes = {{ container_types_json | safe }};
const weightUomOptions = {{ weight_uom_json | safe }};
const volumeUomOptions = {{ volume_uom_json | safe }};

const COUNTRY_NAMES = {
    'US': 'United States',
    'CN': 'China',
    'GB': 'United Kingdom',
    'DE': 'Germany',
    'ES': 'Spain',
    'FR': 'France',
    'NL': 'Netherlands',
    'BE': 'Belgium',
    'DK': 'Denmark',
    'IT': 'Italy',
    'IN': 'India',
    'AE': 'United Arab Emirates',
    'SG': 'Singapore',
    'HK': 'Hong Kong',
    'JP': 'Japan',
    'KR': 'South Korea',
    'CA': 'Canada',
    'MX': 'Mexico',
    'BR': 'Brazil',
    'AU': 'Australia',
    'PL': 'Poland',
    'SE': 'Sweden',
    'NO': 'Norway',
    'FI': 'Finland',
    'CH': 'Switzerland',
    'AT': 'Austria',
    'TR': 'Turkey',
    'VN': 'Vietnam',
    'TH': 'Thailand',
    'MY': 'Malaysia',
    'ID': 'Indonesia',
    'PH': 'Philippines',
    'TW': 'Taiwan',
    'ZA': 'South Africa'
};

function updateMovementType() {
    const originTypeEl = document.getElementById('originType');
    const destTypeEl = document.getElementById('destType');
    if (!originTypeEl || !destTypeEl) return;
    
    const originType = originTypeEl.value;
    const destType = destTypeEl.value;
    let mType = 'PORT_TO_PORT';
    if (originType === 'door' && destType === 'door') {
        mType = 'DOOR_TO_DOOR';
    } else if (originType === 'door' && destType === 'port') {
        mType = 'DOOR_TO_PORT';
    } else if (originType === 'port' && destType === 'door') {
        mType = 'PORT_TO_DOOR';
    } else if (originType === 'port' && destType === 'port') {
        mType = 'PORT_TO_PORT';
    }
    const hiddenMovementType = document.getElementById('hidden_movement_type');
    if (hiddenMovementType) {
        hiddenMovementType.value = mType;
    }
}

function updateDirection() {
    const originCountryEl = document.getElementById('originCountry');
    const destCountryEl = document.getElementById('destCountry');
    if (!originCountryEl || !destCountryEl) return;
    
    const originCountry = originCountryEl.value;
    const destCountry = destCountryEl.value;
    let direction = 'EXPORT'; // Default
    if (originCountry && destCountry) {
        if (destCountry === 'US' && originCountry !== 'US') {
            direction = 'IMPORT';
        } else {
            direction = 'EXPORT';
        }
    }
    const hiddenDirection = document.getElementById('hidden_direction');
    if (hiddenDirection) {
        hiddenDirection.value = direction;
    }
}

function handleLocationTypeChange(locationType) {
    const type = document.getElementById(locationType + 'Type').value;
    const label = document.getElementById(locationType + 'LocationLabel');
    const input = document.getElementById(locationType + 'Location');

    if (type === 'door') {
        label.innerHTML = 'City <span class="required">*</span>';
        input.placeholder = 'Search by city name or zip code';
    } else {
        label.innerHTML = 'Port <span class="required">*</span>';
        input.placeholder = 'Search by port name or UN code';
    }

    // Clear selection
    selectedLocations[locationType] = null;
    input.value = '';
    
    populateCountries(locationType, type);
    updateMovementType();
}

function populateCountries(locationType, type) {
    const countrySelect = document.getElementById(locationType + 'Country');
    if (!countrySelect) return;
    const currentValue = countrySelect.value;
    countrySelect.innerHTML = '<option value="">Select country</option>';
    
    let countries = new Set();
    
    if (type === 'door') {
        Object.keys(COUNTRY_NAMES).forEach(c => countries.add(c));
    } else {
        const portsList = (locationType === 'origin') ? apiOrigins : apiDestinations;
        portsList.forEach(p => {
            if (p.country) {
                countries.add(p.country.toUpperCase());
            }
        });
    }
    
    Array.from(countries).sort().forEach(code => {
        const name = COUNTRY_NAMES[code] || code;
        const option = document.createElement('option');
        option.value = code;
        option.textContent = name;
        countrySelect.appendChild(option);
    });
    
    if (countries.has(currentValue)) {
        countrySelect.value = currentValue;
    }
}

function filterLocations(locationType) {
    const country = document.getElementById(locationType + 'Country').value;
    const type = document.getElementById(locationType + 'Type').value;
    const searchTerm = document.getElementById(locationType + 'Location').value.toLowerCase();
    const dropdown = document.getElementById(locationType + 'Dropdown');

    if (!country) {
        dropdown.classList.remove('show');
        return;
    }

    let filtered = [];
    if (type === 'door') {
        dropdown.classList.remove('show');
        selectedLocations[locationType] = { name: searchTerm, code: '' };
        return;
    } else {
        const portsList = (locationType === 'origin') ? apiOrigins : apiDestinations;
        const locations = portsList.filter(p => p.country && p.country.toUpperCase() === country.toUpperCase());
        filtered = locations.filter(loc => 
            loc.name.toLowerCase().includes(searchTerm) ||
            loc.code.toLowerCase().includes(searchTerm)
        ).map(loc => ({
            name: loc.name,
            code: loc.code
        }));
    }

    if (filtered.length === 0) {
        dropdown.innerHTML = '<div class="dropdown-no-results">No results found</div>';
    } else {
        dropdown.innerHTML = filtered.map(loc => `
            <div class="dropdown-item" onclick="selectLocation('${locationType}', '${loc.name.replace(/'/g, "\\\\'")}', '${loc.code}')">
                <div class="dropdown-item-name">${loc.name}</div>
                <div class="dropdown-item-code">${loc.code}</div>
            </div>
        `).join('');
    }

    dropdown.classList.add('show');
}
"""

script_content = prefix_content + script_content

# Add country population on page load and update movement/direction
script_content = script_content.replace(
    "document.addEventListener('DOMContentLoaded', function () {", 
    "document.addEventListener('DOMContentLoaded', function () {\n            populateCountries('origin', document.getElementById('originType').value);\n            populateCountries('dest', document.getElementById('destType').value);\n            updateMovementType();\n            updateDirection();"
)

# Intercept country changes to update the direction dynamically
script_content = script_content.replace(
    "function handleCountryChange(locationType) {",
    "function handleCountryChange(locationType) {\n            updateDirection();"
)

# Update getQuotes() to actually submit the form instead of alerting
script_content = script_content.replace("alert('🎉 Quote request submitted! You will be redirected to view available offers.');", 
"""// Inject transport_mode and service_type into hidden fields before submitting
document.getElementById('hidden_transport_mode').value = selectedTransportMode;
document.getElementById('hidden_service_type').value = selectedCargoType;
document.getElementById('wizardSearchForm').submit();""")

# 3. Extract Main Content (the entire panel container)
# Find start of main-content
start_idx = view_html.find('<div class="quote-card">')
if start_idx == -1:
    start_idx = view_html.find('<div class="steps-ribbon"')

# Find end of main-content (right before custom-alert-overlay or script)
end_idx = view_html.find('<div class="custom-alert-overlay"')
if end_idx == -1:
    end_idx = view_html.find('<script>')

main_content = view_html[start_idx:end_idx]

# Include custom-alert-overlay
alert_overlay = view_html[view_html.find('<div class="custom-alert-overlay"'):view_html.find('<script>')]

# 4. Modify HTML inputs to have name attributes
replacements = [
    ('id="${itemId}-weight-uom"', 'id="${itemId}-weight-uom" name="item_weight_uom[]"'),
    ('id="${itemId}-volume-uom"', 'id="${itemId}-volume-uom" name="item_volume_uom[]"'),
    # Remove garbled emojis and arrows
    ('➔', 'to'),
    ('dY"', ''),
    ('dYs', ''),
    ('o^', ''),
    ('', ''),
    ('+', ''),
    ('?', ''),
]

for old, new in replacements:
    main_content = main_content.replace(old, new)

# Replace hardcoded incoterm select with dynamic Jinja loop
incoterm_select_old = """                                    <select class="form-select" id="incoterm" name="freight_terms" onchange="updateChargeInclusions()">
                                        <option value="">Select incoterm</option>
                                        <option value="FCA">FCA - Free Carrier</option>
                                        <option value="FOB">FOB - Free On Board</option>
                                        <option value="CFR">CFR - Cost and Freight</option>
                                    </select>"""

incoterm_select_new = """                                    <select class="form-select" id="incoterm" name="freight_terms" onchange="updateChargeInclusions()">
                                        <option value="">Select incoterm</option>
                                        {% for incoterm in incoterms %}
                                            <option value="{{ incoterm.code }}">{{ incoterm.name }}</option>
                                        {% endfor %}
                                    </select>"""

main_content = main_content.replace(incoterm_select_old, incoterm_select_new)

freight_terms_select_old = """                                    <select class="form-select" id="freightTerms" name="payment_terms">
                                        <option value="">Select terms</option>
                                        <option value="prepaid">Prepaid</option>
                                        <option value="collect">Collect</option>
                                        <option value="third_party">Third Party</option>
                                    </select>"""

freight_terms_select_new = """                                    <select class="form-select" id="freightTerms" name="payment_terms">
                                        <option value="">Select terms</option>
                                        {% for term in freight_terms %}
                                            <option value="{{ term.code }}">{{ term.name }}</option>
                                        {% endfor %}
                                    </select>"""

main_content = main_content.replace(freight_terms_select_old, freight_terms_select_new)

# Strip any remaining non-ASCII (this safely removes the emojis)
main_content = re.sub(r'[^\x00-\x7F]+', '', main_content)


# 5. Build final rates.html
final_html = f"""{{% extends "base.html" %}}

{{% block title %}}Request Quotes - FTL Portal{{% endblock %}}

{{% block head %}}
<style>
{styles}

/* Adjustments for integration with base.html */
.rates-view-content {{
    padding: 0;
    margin-left: 0; /* Override if base.html has sidebar handling */
    background: var(--bg-white);
    
    /* Dynamic Theme Mapping */
    --primary-blue: var(--primary-color, #2563eb);
    --primary-blue-dark: var(--primary-hover, #1d4ed8);
    --primary-blue-light: var(--primary-hover, #3b82f6);
}}

/* Dark mode handling for rates view content */
html[data-color-scheme='dark'] .rates-view-content {{
    --bg-white: #1E293B;
    --bg-gray: #0F172A;
    --border-color: #334155;
    --text-primary: #F1F5F9;
    --text-secondary: #CBD5E1;
    --text-muted: #64748B;
    --hover-bg: #263348;
}}

.quote-card {{
    border-radius: 0;
    box-shadow: none;
    border: none;
    background: transparent;
}}

/* Steps ribbon active states style consistency overrides */
.header-section.active {{
    background: var(--primary-color) !important;
    color: #ffffff !important;
    font-weight: 600;
}}

.header-section.active .section-label,
.header-section.active .section-value,
.header-section.active .section-placeholder {{
    color: #ffffff !important;
}}

.header-section.completed::after {{
    background: var(--success-green) !important;
    color: #ffffff !important;
}}
</style>
{{% endblock %}}

{{% block content %}}
<div class="rates-view-content">
    <div class="header-actions" style="display: none;"></div> <!-- Hide view.html header actions if any -->

    <form method="POST" action="{{{{ url_for('customer.rates') }}}}" id="wizardSearchForm">
        <!-- Hidden inputs for JS state -->
        <input type="hidden" name="transport_mode" id="hidden_transport_mode" value="ocean">
        <input type="hidden" name="service_type" id="hidden_service_type" value="lcl">
        <input type="hidden" name="direction" id="hidden_direction" value="EXPORT">
        <input type="hidden" name="movement_type" id="hidden_movement_type" value="PORT_TO_PORT">

        {main_content}
    </form>
    
    {alert_overlay}
</div>

<script>
{script_content}

// Ensure the first cargo item is added on load
document.addEventListener('DOMContentLoaded', function() {{
    if (typeof addCargoItem === 'function') {{
        addCargoItem();
    }}
}});
</script>
{{% endblock %}}
"""

with open(rates_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print("rates.html successfully rebuilt from view.html!")
