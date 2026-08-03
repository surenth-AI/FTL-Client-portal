import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

css_addition = """
/* carrier popup */
.atlas-dashboard .carrier-popup-wrapper { position: relative; text-align: center; margin-top: 10px; }
.atlas-dashboard .carrier-popup { display: none; position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); background: var(--dashboard-card); border: 1px solid var(--dashboard-line); border-radius: 8px; padding: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); z-index: 100; min-width: 200px; text-align: left; margin-bottom: 10px;}
html[data-color-scheme='dark'] .atlas-dashboard .carrier-popup { box-shadow: 0 10px 30px -18px rgba(0,0,0,.9); }
.atlas-dashboard .carrier-popup.show { display: block; }
.atlas-dashboard .carrier-popup-header { display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.75rem; font-weight: 600; color: var(--amber); border-bottom: 1px solid var(--dashboard-line); padding-bottom: 6px;}
.atlas-dashboard .carrier-popup-header span { cursor: pointer; }
.atlas-dashboard .carrier-popup-list { max-height: 200px; overflow-y: auto; }
.atlas-dashboard .carrier-popup-list label { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; margin-bottom: 8px; cursor: pointer; }
.atlas-dashboard .carrier-popup-list input { cursor: pointer; accent-color: var(--dashboard-text); width: 14px; height: 14px;}
"""

content = content.replace("</style>", css_addition + "\n</style>")


carrier_html_old = """        <div class="chartbox small"><canvas id="chCarrier"></canvas></div>
        <div class="legend" style="justify-content:center;margin-top:10px;flex-wrap:wrap">
          <span><i style="background:#8B5CF6"></i>MSC</span><span><i style="background:#06B6D4"></i>Maersk</span>
          <span><i style="background:#EC4899"></i>CMA</span><span><i style="background:#67E8F9"></i>Hapag</span>
          <span><i style="background:#A78BFA"></i>ONE</span>
        </div>"""

carrier_html_new = """        <div class="chartbox small"><canvas id="chCarrier"></canvas></div>
        <div class="carrier-popup-wrapper">
          <a href="#" id="showCarriersLink" style="font-size:0.75rem; color:var(--cyan); text-decoration:none; font-weight:600;">Show all carriers</a>
          <div id="carrierPopup" class="carrier-popup">
             <div class="carrier-popup-header">
               <span id="selectAllCarriers">Select all</span>
               <span id="clearCarriers">Clear</span>
             </div>
             <div class="carrier-popup-list" id="carrierList">
               <!-- populated by js -->
             </div>
          </div>
        </div>"""

content = content.replace(carrier_html_old, carrier_html_new)


carrier_js_old = """    /* 2 · carrier doughnut */
    {
        const ctx = document.getElementById('chCarrier').getContext('2d');
        new Chart(ctx,{type:'doughnut',data:{labels:['MSC','Maersk','CMA CGM','Hapag','ONE','Other'],
        datasets:[{data:[31,24,17,13,9,6],borderWidth:3,borderColor: isDark ? '#161326' : '#FFFFFF',borderRadius:6,
        backgroundColor:['#8B5CF6',cyanMain,'#EC4899','#67E8F9','#A78BFA', isDark ? 'rgba(255,255,255,.14)' : 'rgba(0,0,0,.08)']}]},
        options:{maintainAspectRatio:false,cutout:'68%',
        plugins:{legend:{display:false},tooltip:{...tt,callbacks:{label:c=>' '+c.label+': '+c.parsed+'%'}}}}});
    }"""

carrier_js_new = """    /* 2 · carrier doughnut */
    {
        const carrierData = [
            {name: 'MSC', val: 31, col: '#8B5CF6'},
            {name: 'Maersk', val: 24, col: cyanMain},
            {name: 'CMA CGM', val: 17, col: '#EC4899'},
            {name: 'Hapag-Lloyd', val: 13, col: '#67E8F9'},
            {name: 'Evergreen', val: 10, col: '#10B981'},
            {name: 'ONE Line', val: 9, col: '#A78BFA'},
            {name: 'Emirates SkyCargo', val: 8, col: '#F59E0B'},
            {name: 'Qatar Airways Cargo', val: 7, col: '#EF4444'},
            {name: 'Cathay Cargo', val: 6, col: '#3B82F6'},
            {name: 'Other', val: 5, col: isDark ? 'rgba(255,255,255,.14)' : 'rgba(0,0,0,.08)'}
        ];
        
        let selectedCarriers = new Set(carrierData.map(c => c.name));

        const ctxC = document.getElementById('chCarrier').getContext('2d');
        const chCarrier = new Chart(ctxC,{type:'doughnut',data:{labels:[], datasets:[{data:[],backgroundColor:[],borderWidth:3,borderColor: isDark ? '#161326' : '#FFFFFF',borderRadius:6}]},
        options:{maintainAspectRatio:false,cutout:'68%',
        plugins:{legend:{display:false},tooltip:{...tt,callbacks:{label:c=>' '+c.label+': '+c.parsed+'%'}}}}});

        function updateCarrierChart() {
            const filtered = carrierData.filter(c => selectedCarriers.has(c.name));
            chCarrier.data.labels = filtered.map(c => c.name);
            chCarrier.data.datasets[0].data = filtered.map(c => c.val);
            chCarrier.data.datasets[0].backgroundColor = filtered.map(c => c.col);
            chCarrier.update();
        }
        
        const listContainer = document.getElementById('carrierList');
        carrierData.forEach(c => {
            const lbl = document.createElement('label');
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.checked = true;
            cb.value = c.name;
            cb.addEventListener('change', (e) => {
                if(e.target.checked) selectedCarriers.add(c.name);
                else selectedCarriers.delete(c.name);
                updateCarrierChart();
            });
            lbl.appendChild(cb);
            lbl.appendChild(document.createTextNode(c.name));
            listContainer.appendChild(lbl);
        });

        document.getElementById('showCarriersLink').addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('carrierPopup').classList.toggle('show');
        });
        document.getElementById('selectAllCarriers').addEventListener('click', () => {
            selectedCarriers = new Set(carrierData.map(c => c.name));
            listContainer.querySelectorAll('input').forEach(i => i.checked = true);
            updateCarrierChart();
        });
        document.getElementById('clearCarriers').addEventListener('click', () => {
            selectedCarriers.clear();
            listContainer.querySelectorAll('input').forEach(i => i.checked = false);
            updateCarrierChart();
        });

        // hide on outside click
        document.addEventListener('click', (e) => {
            const pop = document.getElementById('carrierPopup');
            const link = document.getElementById('showCarriersLink');
            if(!pop.contains(e.target) && e.target !== link) {
                pop.classList.remove('show');
            }
        });

        updateCarrierChart();
    }"""

content = content.replace(carrier_js_old, carrier_js_new)

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully!")
