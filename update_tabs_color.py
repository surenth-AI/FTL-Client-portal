import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_css = """    .header-section.active {
        background: var(--bg-white);
        border-left-color: #059669; /* Thick green left border */
    }"""

replacement_css = """    .header-section.active {
        background: #ecfdf5; /* Light green tint for active tab */
        border-left-color: #059669; /* Thick green left border */
    }"""

content = content.replace(target_css, replacement_css)

target_inactive_css = """    .header-section {
        flex: 1;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        border-left: 4px solid transparent; /* Keep width consistent */
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        text-align: center;
        background: #f8fafc; /* Very light gray for inactive */
    }"""

replacement_inactive_css = """    .header-section {
        flex: 1;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        border-left: 4px solid transparent; /* Keep width consistent */
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        text-align: center;
        background: #f1f5f9; /* Darker gray for inactive to increase contrast */
    }"""
content = content.replace(target_inactive_css, replacement_inactive_css)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS updated for active tab contrast.")
