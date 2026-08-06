with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="quotePicker"')
end_idx = text.find('<!-- Linked quote banner -->')

print(text[max(0, idx-100):end_idx].encode('ascii', 'ignore').decode('ascii'))
