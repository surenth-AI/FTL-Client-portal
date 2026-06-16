import os

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_css = """    .header-section {
        flex: 1;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        text-align: center;
    }
    .header-section:last-child {
        border-right: none;
    }
    .header-section:hover {
        background: var(--hover-bg);
    }
    .header-section.active {
        background: var(--primary-color);
        color: white;
    }
    .section-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        transition: color 0.2s;
    }
    .header-section.active .section-label {
        color: white;
    }"""

replacement_css = """    .header-section {
        flex: 1;
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        border-left: 4px solid transparent; /* Keep width consistent */
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        text-align: center;
        background: #f8fafc; /* Very light gray for inactive */
    }
    .header-section:last-child {
        border-right: none;
    }
    .header-section:hover {
        background: #f1f5f9;
    }
    .header-section.active {
        background: var(--bg-white);
        border-left-color: #059669; /* Thick green left border */
    }
    .section-label {
        font-size: 0.95rem; /* Slightly larger like the image */
        font-weight: 600;
        color: var(--text-muted);
        transition: color 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    .header-section.active .section-label,
    .header-section.active .section-label i {
        color: #059669 !important; /* Green text and icon for active state */
    }
    
    /* Ensure dark mode adapts the new design nicely */
    html[data-color-scheme='dark'] .header-section { background: #1e293b; border-color: #334155; }
    html[data-color-scheme='dark'] .header-section:hover { background: #334155; }
    html[data-color-scheme='dark'] .header-section.active { background: #0f172a; border-left-color: #10b981; }
    html[data-color-scheme='dark'] .header-section.active .section-label,
    html[data-color-scheme='dark'] .header-section.active .section-label i { color: #10b981 !important; }"""

content = content.replace(target_css, replacement_css)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS updated successfully.")
