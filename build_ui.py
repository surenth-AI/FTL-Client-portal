import re

with open('d:/FTL-DEV/view.html', 'r', encoding='utf-8') as f:
    view_content = f.read()

# Extract styles
styles_match = re.search(r'<style>(.*?)</style>', view_content, re.DOTALL)
styles = styles_match.group(1) if styles_match else ""

# Extract container content
container_match = re.search(r'<div class="container">(.*?)<!-- Inline Alert Container', view_content, re.DOTALL)
container_content = '<div class="container">' + container_match.group(1) + '</div>' if container_match else ""

# Extract script
script_match = re.search(r'<script>(.*?)</script>', view_content, re.DOTALL)
script_content = script_match.group(1) if script_match else ""

# Build new HTML
new_html = """{% extends 'base.html' %}
{% block title %}Search Rates{% endblock %}
{% block content %}
<style>
""" + styles + """
</style>
<form action="{{ url_for('customer.rates') }}" method="POST" id="wizardSearchForm">
    <input type="hidden" name="service_type" id="wiz_hidden_service_type" value="LCL">
    <input type="hidden" name="origin" id="wiz_hidden_origin" value="">
    <input type="hidden" name="destination" id="wiz_hidden_dest" value="">
    <!-- Container from view.html -->
    """ + container_content + """
    <!-- Custom Alert Overlay -->
    <div class="custom-alert-overlay" id="customAlertOverlay" onclick="closeCustomAlert()">
        <div class="custom-alert-box" onclick="event.stopPropagation()">
            <div class="custom-alert-message" id="customAlertMessage"></div>
            <button type="button" class="custom-alert-button" onclick="closeCustomAlert()">OK</button>
        </div>
    </div>
</form>

<script>
    // Variables from Jinja
    const databaseOrigins = {{ origins|tojson }};
    const databaseDestinations = {{ destinations|tojson }};
""" + script_content + """
    
    // Additional bindings for form submission integration
    function submitWizForm() {
        if (!selectedLocations.origin || !selectedLocations.dest) {
            alert('Please select both origin and destination');
            return;
        }
        document.getElementById('wiz_hidden_origin').value = selectedLocations.origin.name;
        document.getElementById('wiz_hidden_dest').value = selectedLocations.dest.name;
        document.getElementById('wiz_hidden_service_type').value = selectedCargoType.toUpperCase();
        
        document.getElementById('wizardSearchForm').submit();
    }
    
    // Override the getQuotes function from view.html to actually submit the form
    function getQuotes() {
        submitWizForm();
    }

</script>
{% endblock %}
"""

# Now write back to a temp file, then we will use replace to fine-tune inputs.
with open('d:/FTL-DEV/app/templates/customer/rates_new.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Generated rates_new.html successfully.')
