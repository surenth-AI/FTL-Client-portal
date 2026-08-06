import re
with open('app/routes/customer.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = '''
    # Fetch Countries
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
                         valid_quotes=valid_quotes)
'''

text = re.sub(r'# Fetch Countries.*?countries=countries\)', replacement.strip(), text, flags=re.DOTALL)

with open('app/routes/customer.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated customer.py')
