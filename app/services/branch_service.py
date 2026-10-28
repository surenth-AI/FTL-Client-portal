import requests
from app import db
from app.models.models import Branch, UserBranchMapping, UserAccountMapping

ERP_BRANCHES_URL = "http://realnexus.comit.cloud:5000/api/Branches/Branches"
ERP_ACCOUNTS_URL = "http://realnexus.comit.cloud:5000/api/Accounts/Accounts"
ERP_HEADERS = {'x-api-key': '1', 'accept': 'application/json'}

def sync_branches_from_erp():
    """
    Calls the Nexus ERP API and upserts all branch names and details
    directly into the 'branch' database table.
    """
    try:
        resp = requests.get(ERP_BRANCHES_URL, headers=ERP_HEADERS, timeout=8)
        if resp.status_code == 200:
            branches_data = resp.json()
            for b in branches_data:
                b_id = str(b.get('branchID') or b.get('branchId', '')).strip()
                if not b_id:
                    continue
                name = (b.get('name') or f"Branch {b_id}").strip()
                call_name = (b.get('callName') or '').strip()
                b_uuid = (b.get('uuid') or '').strip()
                currency = (b.get('currency') or '').strip()
                country_code = (b.get('countryCode') or '').strip()

                branch = Branch.query.get(b_id)
                if not branch:
                    branch = Branch(
                        id=b_id,
                        name=name,
                        call_name=call_name,
                        uuid=b_uuid,
                        currency=currency,
                        country_code=country_code
                    )
                    db.session.add(branch)
                else:
                    branch.name = name
                    branch.call_name = call_name
                    branch.uuid = b_uuid
                    branch.currency = currency
                    branch.country_code = country_code

            db.session.commit()
            print(f"[branch_service] Synced {len(branches_data)} branches from ERP into database.")
            return Branch.query.order_by(Branch.id).all()
        else:
            print(f"[branch_service] ERP branches API returned status {resp.status_code}")
    except Exception as e:
        print(f"[branch_service] Failed to sync branches from ERP: {e}")

    return Branch.query.order_by(Branch.id).all()


def get_all_branches():
    """
    Returns all branches from the database. If table is empty,
    fetches from ERP API first and stores them.
    """
    branches = Branch.query.order_by(Branch.id).all()
    if not branches:
        branches = sync_branches_from_erp()
    return branches


def discover_and_map_user_branches(user, account_ids=None, explicit_branch_ids=None):
    """
    Dynamically finds and maps branches for a customer and stores them in user_branch_mapping.
    
    1. If explicit_branch_ids is provided (e.g. from admin or API sync payload), saves them.
    2. Otherwise, looks at user's mapped accounts, fetches account details from ERP,
       matches the account's branch UUID to Branch.uuid, and maps the branch to user.
    """
    if not user or not user.id:
        return []

    # 1. Explicit branch IDs supplied
    if explicit_branch_ids is not None:
        valid_bids = [str(bid).strip() for bid in explicit_branch_ids if str(bid).strip()]
        UserBranchMapping.query.filter_by(user_id=user.id).delete()
        for bid in valid_bids:
            db.session.add(UserBranchMapping(user_id=user.id, branch_id=bid))
        db.session.commit()
        return valid_bids

    # 2. Determine target accounts
    if account_ids is None:
        target_accounts = [str(m.account_id).strip() for m in user.accounts if m.account_id]
    else:
        target_accounts = [str(aid).strip() for aid in account_ids if str(aid).strip()]

    discovered_branch_ids = set()

    # Look up accounts from ERP to find their branch
    if target_accounts:
        try:
            # Ensure branch table has data
            branches = get_all_branches()
            uuid_to_bid = {str(b.uuid).lower().strip(): str(b.id) for b in branches if b.uuid}

            resp = requests.get(ERP_ACCOUNTS_URL, headers=ERP_HEADERS, timeout=8)
            if resp.status_code == 200:
                accounts_data = resp.json()
                acc_set = set(target_accounts)
                for a in accounts_data:
                    aid = str(a.get('accountID') or a.get('accountId', '')).strip()
                    if aid in acc_set:
                        b_ref = str(a.get('branchID') or a.get('branchId', '')).lower().strip()
                        # Match UUID first, then direct branch ID
                        if b_ref in uuid_to_bid:
                            discovered_branch_ids.add(uuid_to_bid[b_ref])
                        elif Branch.query.get(b_ref):
                            discovered_branch_ids.add(b_ref)
        except Exception as e:
            print(f"[branch_service] Error resolving branches from ERP accounts: {e}")

    # Store discovered branches in DB
    if discovered_branch_ids:
        existing = {m.branch_id for m in user.branches}
        new_added = False
        for bid in discovered_branch_ids:
            if bid not in existing:
                db.session.add(UserBranchMapping(user_id=user.id, branch_id=bid))
                new_added = True
        if new_added:
            db.session.commit()

    return [m.branch_id for m in UserBranchMapping.query.filter_by(user_id=user.id).all()]

