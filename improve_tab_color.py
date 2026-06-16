import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_active_css = """    .header-section.active {
        background: #ecfdf5; /* Light green tint for active tab */
        border-left-color: #059669; /* Thick green left border */
    }"""

replacement_active_css = """    .header-section.active {
        background: #ffffff; /* Pure crisp white */
        border-left-color: #047857; /* Slightly deeper, richer emerald green */
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); /* Subtle lift */
        z-index: 10;
    }"""
content = content.replace(target_active_css, replacement_active_css)

target_inactive_css = """    .header-section {
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

replacement_inactive_css = """    .header-section {
        flex: 1;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        border-left: 4px solid transparent;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        text-align: center;
        background: #f8fafc; /* Keep it very light gray */
    }"""
content = content.replace(target_inactive_css, replacement_inactive_css)


target_text_css = """    .header-section.active .section-label,
    .header-section.active .section-label i {
        color: #059669 !important; /* Green text and icon for active state */
    }"""

replacement_text_css = """    .header-section.active .section-label,
    .header-section.active .section-label i {
        color: #047857 !important; /* Richer emerald text to match border */
        font-weight: 700 !important; /* Make it extra bold so it pops */
    }"""
content = content.replace(target_text_css, replacement_text_css)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Color improved for active tab.")
