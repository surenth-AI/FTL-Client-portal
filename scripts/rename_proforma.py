import os
import re

def replace_in_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    new_content = content
    
    # Replace specific phrases first
    new_content = re.sub(r'Proforma Invoice', 'Revenue Invoice', new_content)
    new_content = re.sub(r'PROFORMA INVOICE', 'REVENUE INVOICE', new_content)
    new_content = re.sub(r'Proforma Invoices', 'Revenue Invoices', new_content)
    new_content = re.sub(r'PROFORMA INVOICES', 'REVENUE INVOICES', new_content)
    
    # Replace standalone words
    new_content = re.sub(r'Proformas', 'Revenue Invoices', new_content)
    new_content = re.sub(r'PROFORMAS', 'REVENUE INVOICES', new_content)
    new_content = re.sub(r'(?<!_)Proforma(?!Invoice)', 'Revenue Invoice', new_content)

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
            if file.endswith(('.html', '.md')):
                filepath = os.path.join(root, file)
                if replace_in_html(filepath):
                    count += 1
                    print(f"Updated {filepath}")
    print(f"Total files updated: {count}")

if __name__ == '__main__':
    main()
