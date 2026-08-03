import re

with open('app/templates/admin/shipment_intelligence.html', 'r', encoding='utf-8') as f:
    content = f.read()

holo_exact = """        <div class="holo fade-in" style="animation-delay:.3s">
          <svg class="wave" viewBox="0 0 330 150" preserveAspectRatio="none">
            <path d="M0 110 C60 70 90 130 150 95 S260 40 330 78" fill="none" stroke="rgba(167,139,250,.8)" stroke-width="2.5"/>
            <path d="M0 120 C70 90 110 140 170 108 S270 60 330 95" fill="none" stroke="rgba(103,232,249,.5)" stroke-width="2"/>
          </svg>
          <div class="lbl">Total pipeline · premium</div>
          <div class="num">$4,280,400</div>
          <div class="digits">QT26 •• 4187 •• 0731</div>
          <div class="foot"><span>ATLAS FREIGHT LINE</span><span>VALID THRU 08/26</span></div>
        </div>"""

carrier_exact = """      <!-- doughnut: carrier -->
      <div class="acard fade-in" style="animation-delay:.45s">
        <div class="head-row">
          <div><h3>Carrier mix</h3><div class="hint">Share of sailings · dependence check</div></div>
          <button class="btn-atlas" style="padding:4px 8px;font-size:.65rem;border-radius:6px;min-width:auto;">Export</button>
        </div>
        <div class="chartbox small"><canvas id="chCarrier"></canvas></div>
        <div class="legend" style="justify-content:center;margin-top:10px;flex-wrap:wrap">
          <span><i style="background:#8B5CF6"></i>MSC</span><span><i style="background:#06B6D4"></i>Maersk</span>
          <span><i style="background:#EC4899"></i>CMA</span><span><i style="background:#67E8F9"></i>Hapag</span>
          <span><i style="background:#A78BFA"></i>ONE</span>
        </div>
      </div>"""

outcome_exact = """      <!-- ring: booked vs expired -->
      <div class="acard fade-in" style="animation-delay:.5s">
        <div class="head-row">
          <div><h3>Quote outcome (30d)</h3><div class="hint">Booked vs expired vs open</div></div>
          <button class="btn-atlas" style="padding:4px 8px;font-size:.65rem;border-radius:6px;min-width:auto;">Export</button>
        </div>
        <div class="chartbox small">
          <canvas id="chOutcome"></canvas>
          <div class="center-lb"><div><b>151</b><small>quotes issued</small></div></div>
        </div>
        <div class="legend" style="justify-content:center;margin-top:10px">
          <span><i style="background:#C026D3"></i>Booked 47</span>
          <span><i style="background:#06B6D4"></i>Open 76</span>
          <span><i style="background:var(--dashboard-line)"></i>Expired 28</span>
        </div>
      </div>"""

shipment_status_html = """      <!-- shipment status -->
      <div class="acard span2 fade-in" style="animation-delay:.45s">
        <div class="head-row">
          <div><h3>Shipment Status</h3><div class="hint">Completed vs Incomplete</div></div>
          <div style="display:flex; gap:10px; align-items:center;">
            <select aria-label="Type" style="padding:4px 8px;font-size:.65rem;border-radius:6px;">
              <option>All Types</option>
              <option>Export</option>
              <option>Import</option>
            </select>
            <button class="btn-atlas" style="padding:4px 8px;font-size:.65rem;border-radius:6px;min-width:auto;">Export</button>
          </div>
        </div>
        <div class="chartbox small"><canvas id="chShipmentStatus"></canvas></div>
      </div>"""

# Replace holo with carrier
content = content.replace(holo_exact, carrier_exact)

# Then remove original carrier and outcome, and replace with shipment status
# They are next to each other in the original HTML with some spaces in between
pattern = re.escape(carrier_exact) + r'\s*' + re.escape(outcome_exact)
content = re.sub(pattern, shipment_status_html, content)

ch_outcome_js = """    /* 3 · quote outcome ring */
    {
        const ctx = document.getElementById('chOutcome').getContext('2d');
        new Chart(ctx,{type:'doughnut',data:{labels:['Booked','Open','Expired'],
        datasets:[{data:[47,76,28],borderWidth:3,borderColor: isDark ? '#161326' : '#FFFFFF',borderRadius:10,
        backgroundColor:['#C026D3',cyanMain, isDark ? 'rgba(255,255,255,.14)' : 'rgba(0,0,0,.08)']}]},
        options:{maintainAspectRatio:false,cutout:'74%',rotation:-100,
        plugins:{legend:{display:false},tooltip:tt}}});
    }"""

ch_shipment_js = """    /* 3 · shipment status bar */
    {
        const ctx = document.getElementById('chShipmentStatus').getContext('2d');
        new Chart(ctx,{type:'bar',data:{labels:['W32','W33','W34','W35','W36','W37'],
        datasets:[
            {label:'Completed',data:[42,38,51,46,55,30],backgroundColor:'#10B981',borderRadius:4,barPercentage:.6},
            {label:'Incomplete',data:[12,14,9,11,8,22],backgroundColor:isDark ? 'rgba(255,255,255,.14)' : 'rgba(0,0,0,.08)',borderRadius:4,barPercentage:.6}
        ]},
        options:{maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom'},tooltip:tt},
        scales:{y:{beginAtZero:true,stacked:true,grid:{drawTicks:false},border:{display:false}},
                x:{stacked:true,grid:{display:false},border:{display:false}}}}});
    }"""

content = content.replace(ch_outcome_js, ch_shipment_js)

with open('app/templates/admin/shipment_intelligence.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully!")
