with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("route: \"{{ q.origin | default('') }} &rarr; {{ q.destination | default('') }}\"", "route: \"{{ q.origin | default('') }} \\u2192 {{ q.destination | default('') }}\"")

with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Fixed JS route separator')
