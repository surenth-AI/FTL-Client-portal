with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<span class="picker-meta"> {{ q.service_type', '<span class="picker-meta">📦 {{ q.service_type')

with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
    f.write(text)
print('Added emoji back')
