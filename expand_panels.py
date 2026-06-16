import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace col-md-8 mx-auto with col-12
content = content.replace('<div class="col-md-8 mx-auto">', '<div class="col-12">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Expanded all 3 panels to use the full container width.")
