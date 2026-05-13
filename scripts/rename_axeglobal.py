import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    new_content = content
    
    # Replace text
    new_content = re.sub(r'Nexus Logistics', 'AxeGlobal Logistics', new_content, flags=re.IGNORECASE)
    new_content = new_content.replace('NEXUS', 'AXEGLOBAL')
    new_content = new_content.replace('Nexus', 'AxeGlobal')
    new_content = new_content.replace('nexus', 'axeglobal')

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
                if file == 'rename_axeglobal.py':
                    continue
                if replace_in_file(filepath):
                    count += 1
                    print(f"Updated {filepath}")
    print(f"Total files updated: {count}")

    # Rename db if it exists
    if os.path.exists('nexus.db'):
        try:
            os.rename('nexus.db', 'axeglobal.db')
            print("Renamed nexus.db to axeglobal.db")
        except:
            print("Could not rename nexus.db to axeglobal.db (might be in use)")

if __name__ == '__main__':
    main()
