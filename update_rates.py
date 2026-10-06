import re

def update_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # We want to find DOMContentLoaded and inject the handleLocationTypeChange calls
    text = re.sub(
        r'document.addEventListener\(\'DOMContentLoaded\', function \(\) \{',
        r'''document.addEventListener('DOMContentLoaded', function () {
            handleLocationTypeChange('origin', false);
            handleLocationTypeChange('dest', false);''',
        text
    )
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Updated {filename}')

update_file('app/templates/customer/rates.html')
