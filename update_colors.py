import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Light Mode CSS Variables to softer/pastel colors
old_light_vars = """  --violet: #8B5CF6;
  --violet2: #A78BFA;
  --purple: #C026D3;
  --cyan: #06B6D4;
  --cyan2: #22D3EE;
  --pink: #EC4899;
  --green: #10B981;
  --amber: #F59E0B;
  --red: #EF4444;"""

new_light_vars = """  --violet: #A78BFA;
  --violet2: #C4B5FD;
  --purple: #E879F9;
  --cyan: #22D3EE;
  --cyan2: #67E8F9;
  --pink: #F472B6;
  --green: #34D399;
  --amber: #FBBF24;
  --red: #F87171;"""

content = content.replace(old_light_vars, new_light_vars)

# 2. Update JavaScript to use CSS variables
content = content.replace("const cyanMain = isDark ? '#22D3EE' : '#06B6D4';", "")

js_fix = """
    const style = getComputedStyle(document.body);
    const getVar = (name) => style.getPropertyValue(name).trim();
    const cyanMain = getVar('--cyan');
    const violet = getVar('--violet');
    const violet2 = getVar('--violet2');
    const purple = getVar('--purple');
    const pink = getVar('--pink');
    const green = getVar('--green');
    const amber = getVar('--amber');
    const red = getVar('--red');
"""

content = re.sub(r'const isDark = .*?;', r'const isDark = document.documentElement.getAttribute(\'data-color-scheme\') === \'dark\';\n' + js_fix, content)

content = content.replace("'#8B5CF6'", "violet")
content = content.replace("'#A78BFA'", "violet2")
content = content.replace("'#C026D3'", "purple")
content = content.replace("'#06B6D4'", "cyanMain")
content = content.replace("'#EC4899'", "pink")
content = content.replace("'#10B981'", "green")
content = content.replace("'#F59E0B'", "amber")
content = content.replace("'#EF4444'", "red")
content = content.replace("'#3B82F6'", "getVar('--cyan2')")
content = content.replace("isDark ? '#67E8F9' : '#06B6D4'", "cyanMain")

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully!")
