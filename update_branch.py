import re

def update_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    # Part 1: Replace branch fetching logic
    old_fetch = '''    user_branch_name = ''
    try:
        branch_id = None
        if current_user.branches:
            branch_id = int(current_user.branches[0].branch_id)
        
        if branch_id:
            b_resp = requests.get("http://realnexus.comit.cloud:5000/api/Branches/Branches", headers={'x-api-key': '1'}, timeout=3)
            if b_resp.status_code == 200:
                for b in b_resp.json():
                    if str(b.get('branchID')) == str(branch_id):
                        user_branch_name = b.get('name')
                        break
    except Exception as e:
        print("Failed to fetch user branch name:", e)'''

    new_fetch = '''    all_branches = {}
    try:
        b_resp = requests.get("http://realnexus.comit.cloud:5000/api/Branches/Branches", headers={'x-api-key': '1'}, timeout=3)
        if b_resp.status_code == 200:
            for b in b_resp.json():
                all_branches[str(b.get('branchID') or b.get('branchId', ''))] = b.get('name', '')
    except Exception as e:
        print("Failed to fetch branches:", e)'''
        
    text = text.replace(old_fetch, new_fetch)

    # Part 2: Add offering_branch to the mapped dict
    old_append = '''quote_data.append({
                    'id': local_id,
                    'origin': origin,
                    'destination': destination,
                    'total_cost': total_cost,
                    'currency': quote_currency,
                    'selected_nvocc': header.get('nvoccName') or header.get('carrierName') or user_branch_name or '','''
                    
    new_append = '''
                q_branch_id = header.get('branchId') or header.get('branchID') or (current_user.branches[0].branch_id if current_user.branches else '')
                offering_branch = all_branches.get(str(q_branch_id)) or ''

                quote_data.append({
                    'id': local_id,
                    'origin': origin,
                    'destination': destination,
                    'total_cost': total_cost,
                    'currency': quote_currency,
                    'offering_branch': offering_branch,
                    'selected_nvocc': header.get('nvoccName') or header.get('carrierName') or offering_branch or '','''

    text = text.replace(old_append, new_append)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Updated {filename}')

update_file('app/routes/customer.py')
