import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix KPI text colors in case it was missed (the image showed white text for "Total shipment")
content = content.replace("color:#fff;", "color:var(--dashboard-text);")

# Fix chShipmentStatus colors
content = content.replace("backgroundColor:'#10B981'", "backgroundColor:green")
content = content.replace("backgroundColor:'#8B5CF6'", "backgroundColor:violet")

# Fix chTrend gradient colors. 
content = re.sub(
    r"vGrad\(ctx,'rgba\(139,92,246,\.30\)','rgba\(139,92,246,0\)'\)", 
    r"vGrad(ctx, isDark ? 'rgba(139,92,246,.30)' : 'rgba(139,165,201,.30)', 'transparent')", 
    content
)

content = re.sub(
    r"vGrad\(ctx, isDark \? 'rgba\(34,211,238,\.22\)' : 'rgba\(6,182,212,\.22\)','rgba\(34,211,238,0\)'\)",
    r"vGrad(ctx, isDark ? 'rgba(34,211,238,.22)' : 'rgba(139,195,201,.40)', 'transparent')",
    content
)

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated successfully!")
