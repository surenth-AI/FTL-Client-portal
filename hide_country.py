import re

def update_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # We want to find the <div class='form-group'> that immediately precedes <label class="form-label">Country
    # and add style='display: none;' to it.
    
    # Find all occurrences
    text = re.sub(
        r'<div class="form-group">\s*<label class="form-label">Country',
        r'<div class="form-group" style="display: none;">\n                                        <label class="form-label">Country',
        text
    )
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Updated {filename}')

update_file('app/templates/customer/new_booking.html')
update_file('app/templates/customer/rates.html')
