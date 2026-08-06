with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="quoteTabHeader"')
if idx != -1:
    print(text[max(0, idx-100):idx+500].encode('ascii', 'ignore').decode('ascii'))
else:
    print('quoteTabHeader not found')

idx2 = text.find('function selectBookingMode')
if idx2 != -1:
    print(text[max(0, idx2):idx2+1000].encode('ascii', 'ignore').decode('ascii'))
else:
    print('function selectBookingMode not found')
