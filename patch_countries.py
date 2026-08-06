import re

def main():
    with open('app/routes/customer.py', 'r', encoding='utf-8') as f:
        text = f.read()

    start_idx = text.find('def new_booking():')
    if start_idx != -1:
        render_idx = text.find("return render_template('customer/new_booking.html'", start_idx)
        
        if render_idx != -1 and 'countries=countries' not in text[render_idx:render_idx+200]:
            insert_code = """
    # Fetch Countries
    from app.services.master_data import get_code_list
    try:
        countries_api = get_code_list('countrycode')
        countries = [c.to_dict() for c in countries_api] if countries_api else []
    except Exception as ex:
        print("Error fetching countries:", ex)
        countries = []

    """
            text = text[:render_idx] + insert_code + text[render_idx:]
            
            text = text.replace(
                "return render_template('customer/new_booking.html', \n                         origins=origins, \n                         destinations=destinations,\n                         query=session.get('search_query', {}),\n                         quote_data=quote_data)",
                "return render_template('customer/new_booking.html', \n                         origins=origins, \n                         destinations=destinations,\n                         query=session.get('search_query', {}),\n                         quote_data=quote_data,\n                         countries=countries)"
            )
            text = text.replace(
                "return render_template('customer/new_booking.html', \r\n                         origins=origins, \r\n                         destinations=destinations,\r\n                         query=session.get('search_query', {}),\r\n                         quote_data=quote_data)",
                "return render_template('customer/new_booking.html', \r\n                         origins=origins, \r\n                         destinations=destinations,\r\n                         query=session.get('search_query', {}),\r\n                         quote_data=quote_data,\r\n                         countries=countries)"
            )
            # also handle case without \r
            text = re.sub(
                r"return render_template\('customer/new_booking.html', \s*origins=origins, \s*destinations=destinations,\s*query=session.get\('search_query', \{\}\),\s*quote_data=quote_data\)",
                r"return render_template('customer/new_booking.html', origins=origins, destinations=destinations, query=session.get('search_query', {}), quote_data=quote_data, countries=countries)",
                text, flags=re.MULTILINE
            )
            
            with open('app/routes/customer.py', 'w', encoding='utf-8') as f:
                f.write(text)
            print("Patched customer.py")
        else:
            print("Could not find render_template or already patched")

if __name__ == '__main__':
    main()
