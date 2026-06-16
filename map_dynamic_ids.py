import os

filepath = r'd:\FTL-DEV\app\routes\customer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_logic = """        # Build API Payload
        payload = {
            "header": {
                "branchId": 0,
                "customerId": 0,
                "customerContactId": 0,"""

replacement_logic = """        # Extract IDs from User Profile mappings
        branch_id = 0
        customer_id = 0
        if current_user.branches:
            try: branch_id = int(current_user.branches[0].branch_id)
            except: pass
        if current_user.accounts:
            try: customer_id = int(current_user.accounts[0].account_id)
            except: pass
            
        # Build API Payload
        payload = {
            "header": {
                "branchId": branch_id,
                "customerId": customer_id,
                "customerContactId": current_user.id,"""

content = content.replace(target_logic, replacement_logic)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Dynamic IDs mapped from current_user!")
