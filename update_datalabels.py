import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add chartjs-plugin-datalabels CDN
if 'chartjs-plugin-datalabels' not in content:
    script_cdn = '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>\n<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>'
    content = content.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>', script_cdn)

# 2. Fix colors for Export/Import Incomplete to be visible in both themes
content = content.replace(
    "backgroundColor:isDark ? 'rgba(255,255,255,.14)' : 'rgba(0,0,0,.08)'",
    "backgroundColor:isDark ? 'rgba(255,255,255,.14)' : '#94a3b8'"
)
content = content.replace(
    "backgroundColor:isDark ? 'rgba(255,255,255,.24)' : 'rgba(0,0,0,.15)'",
    "backgroundColor:isDark ? 'rgba(255,255,255,.24)' : '#cbd5e1'"
)

# 3. Add DataLabels plugin to chShipmentStatus safely
# Find the chShipmentStatus instantiation block
pattern = r"(const chShipmentStatus = new Chart\(ctxS,\{type:'bar',data:\{.*?\],)(.*?\n.*?)(options:\{maintainAspectRatio:false,plugins:\{legend:\{display:false\},tooltip:tt\},)"

def replacer(match):
    prefix = match.group(1) + match.group(2)
    # inject plugins array for this chart and add datalabels to options
    return prefix + """plugins: [ChartDataLabels],
        options:{maintainAspectRatio:false,plugins:{
            legend:{display:false},
            tooltip:tt,
            datalabels: {
                color: isDark ? '#ffffff' : '#ffffff',
                font: { weight: 'bold', size: 10 },
                formatter: (value) => value > 0 ? value : ''
            }
        },"""

content = re.sub(pattern, replacer, content, flags=re.DOTALL)


with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated successfully!")
