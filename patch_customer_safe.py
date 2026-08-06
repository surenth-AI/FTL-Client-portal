import re

with open('app/routes/customer.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Find def new_booking
idx_start = text.find('def new_booking')

# Find the specific return render_template inside new_booking
target_block = """    # Fetch Countries
    from app.services.master_data import get_code_list
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    return render_template('customer/new_booking.html', 
                         origins=origins, 
                         destinations=destinations,
                         query=session.get('search_query', {}),
                         quote_data=quote_data,
                         countries=countries)"""

replacement_block = """    # Fetch Countries
    from app.services.master_data import get_code_list
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    # Fetch valid quotes for the quote picker
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    my_quotes = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status == 'Saved Quote'
    ).order_by(Booking.created_at.desc()).limit(100).all()

    valid_quotes = []
    for q in my_quotes:
        valid_until = q.created_at + timedelta(days=30)
        if valid_until >= now:
            computed_status = 'Expiring Soon' if (valid_until - now).days <= 2 else 'Active'
            q.computed_status = computed_status
            valid_quotes.append(q)

    return render_template('customer/new_booking.html', 
                         origins=origins, 
                         destinations=destinations,
                         query=session.get('search_query', {}),
                         quote_data=quote_data,
                         countries=countries,
                         valid_quotes=valid_quotes)"""

# We only want to replace it INSIDE new_booking
if target_block in text[idx_start:]:
    # Reconstruct text
    part1 = text[:idx_start]
    part2 = text[idx_start:]
    part2 = part2.replace(target_block, replacement_block, 1)
    text = part1 + part2
    
    with open('app/routes/customer.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully patched customer.py")
else:
    print("Could not find target block")
