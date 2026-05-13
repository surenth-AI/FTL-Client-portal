import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    new_content = content
    
    # Replace logo image tags with text
    img_pattern = r'<img\s+src="\{\{\s*url_for\(\'static\',\s*filename=\'img/logo\.png\'\)\s*\}\}"[^>]*>'
    replacement = '<div class="h3 text-white fw-bold mb-0 text-accent-glow"><i class="bi bi-globe me-2"></i>AXEGLOBAL</div>'
    new_content = re.sub(img_pattern, replacement, new_content)

    # Replace "Fast Transit Line"
    new_content = re.sub(r'Fast Transit Line', 'AxeGlobal Logistics', new_content, flags=re.IGNORECASE)
    
    # Replace "FTL"
    new_content = new_content.replace('FTL', 'AXEGLOBAL')
    new_content = new_content.replace('ftl', 'axeglobal')

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    skip_dirs = ['venv', '.git', '__pycache__', 'node_modules', '.gemini', 'uploads', 'static']
    count = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(('.py', '.html', '.md', '.txt', '.csv')):
                filepath = os.path.join(root, file)
                if file == 'remove_ftl.py':
                    continue
                if replace_in_file(filepath):
                    count += 1
                    print(f"Updated {filepath}")
    print(f"Total files updated: {count}")

    # Rename db if it exists
    if os.path.exists('ftl.db'):
        os.rename('ftl.db', 'axeglobal.db')
        print("Renamed ftl.db to axeglobal.db")

if __name__ == '__main__':
    main()
