import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

show_more_html = '\n        <div style="text-align:center; margin-top:12px;"><a href="#" style="font-size:0.75rem; color:var(--cyan); text-decoration:none; font-weight:600;">Show more</a></div>\n      </div>'

# 1. Expiring quotes
content = re.sub(r'(<div class="row">.*?<div class="v2">.*?</div></div>\s*)</div>\s*(?=<!-- Bookings Overview)', r'\1' + show_more_html + '\n\n      ', content, flags=re.DOTALL)

# 2. Risk radar
content = re.sub(r'(<div class="row">.*?<div class="v2">.*?</div></div>\s*)</div>\s*(?=<!-- doughnut: carrier -->)', r'\1' + show_more_html + '\n\n      ', content, flags=re.DOTALL)

# 3. Top performing clients
content = re.sub(r'(<div class="row">.*?<div class="v2">.*?</div></div>\s*)</div>\s*(?=<!-- weekday bars -> client profit line -->)', r'\1' + show_more_html + '\n\n      ', content, flags=re.DOTALL)

# 4. Client specific profit header
old_client_profit_head = """          <div><h3>Client specific profit</h3><div class="hint">Monthly profit trends per top client</div></div>
          <button class="btn-atlas" style="padding:4px 8px;font-size:.65rem;border-radius:6px;min-width:auto;">Export</button>"""

new_client_profit_head = """          <div><h3>Client specific profit</h3><div class="hint">Monthly profit trends per top client</div></div>
          <div style="display:flex; gap:10px; align-items:center;">
             <select id="clientProfitFilter" aria-label="Client" style="padding:4px 8px;font-size:.65rem;border-radius:6px;">
                <option value="nordchem" selected>NordChem BV</option>
                <option value="elbe">Elbe Machinery</option>
                <option value="all">All Top Clients</option>
             </select>
             <button class="btn-atlas" style="padding:4px 8px;font-size:.65rem;border-radius:6px;min-width:auto;">Export</button>
          </div>"""

content = content.replace(old_client_profit_head, new_client_profit_head)

# 5. Client specific profit js
old_client_js = """    /* 4 · client profit line */
    {
        const ctx = document.getElementById('chDays').getContext('2d');
        new Chart(ctx,{type:'line',data:{labels:['Jan','Feb','Mar','Apr','May','Jun'],
        datasets:[
            {label:'NordChem BV',data:[120,190,150,220,290,240],borderColor:'#8B5CF6',backgroundColor:'rgba(139,92,246,0.1)',borderWidth:2.5,tension:0.4,fill:true},
            {label:'Elbe Machinery',data:[80,120,180,140,200,250],borderColor:cyanMain,backgroundColor:isDark ? 'rgba(34,211,238,0.1)' : 'rgba(6,182,212,0.1)',borderWidth:2.5,tension:0.4,fill:true}
        ]},
        options:{maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom'},tooltip:tt},
        scales:{y:{beginAtZero:true,grid:{drawTicks:false},border:{display:false}},
                x:{grid:{display:false},border:{display:false}}}}});
    }"""

new_client_js = """    /* 4 · client profit line */
    {
        const ctx = document.getElementById('chDays').getContext('2d');
        const profitChart = new Chart(ctx,{type:'line',data:{labels:['Jan','Feb','Mar','Apr','May','Jun'],
        datasets:[
            {label:'NordChem BV',data:[120,190,150,220,290,240],borderColor:'#8B5CF6',backgroundColor:'rgba(139,92,246,0.1)',borderWidth:2.5,tension:0.4,fill:true, client:'nordchem'},
            {label:'Elbe Machinery',data:[80,120,180,140,200,250],borderColor:cyanMain,backgroundColor:isDark ? 'rgba(34,211,238,0.1)' : 'rgba(6,182,212,0.1)',borderWidth:2.5,tension:0.4,fill:true, client:'elbe'}
        ]},
        options:{maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom'},tooltip:tt},
        scales:{y:{beginAtZero:true,grid:{drawTicks:false},border:{display:false}},
                x:{grid:{display:false},border:{display:false}}}}});

        profitChart.data.datasets.forEach(ds => {
            if(ds.client !== 'nordchem') ds.hidden = true;
        });
        profitChart.update();

        document.getElementById('clientProfitFilter')?.addEventListener('change', (e) => {
            const val = e.target.value;
            profitChart.data.datasets.forEach(ds => {
                if(val === 'all') ds.hidden = false;
                else ds.hidden = (ds.client !== val);
            });
            profitChart.update();
        });
    }"""

content = content.replace(old_client_js, new_client_js)

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully!")
