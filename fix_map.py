import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the block title and endblock, extract the script, and move it inside block content
# The pattern to match:
# {% block title %}Search Rates
# <script ...>...</script>
# {% endblock %}
# We will change it to:
# {% block title %}Search Rates{% endblock %}
# And prepend the script to the beginning of {% block content %}

pattern = r'({% block title %}Search Rates\s*)(<script src="https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js"></script>.*?)({% endblock %})'

match = re.search(pattern, content, flags=re.DOTALL)
if match:
    script_content = match.group(2)
    # Remove script from title block
    content = content[:match.start()] + "{% block title %}Search Rates{% endblock %}" + content[match.end():]
    
    # Prepend to content block
    content = content.replace('{% block content %}', '{% block content %}\n' + script_content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Script moved successfully.")
else:
    print("Pattern not found.")
