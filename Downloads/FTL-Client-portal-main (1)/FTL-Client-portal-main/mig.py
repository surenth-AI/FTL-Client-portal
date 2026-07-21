import re

with open('bookind_sample.html', 'r', encoding='utf-8') as f:
    content = f.read()

styles_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
styles = styles_match.group(1) if styles_match else ''

body_match = re.search(r'<div class="container">(.*?)</body>', content, re.DOTALL)
body_content = '<div class="container">' + body_match.group(1) if body_match else ''

jinja_template = '{% extends "base.html" %}\n{% block title %}Create Booking - Fast Transit Line{% endblock %}\n{% block content %}\n<style>\n' + styles + '\n</style>\n' + body_content + '\n{% endblock %}\n'

with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
    f.write(jinja_template)

print('Done!')
