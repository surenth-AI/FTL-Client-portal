import re

file_path = r'd:\FTL-DEV\app\templates\customer\my_quotes.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add pagination macro import at the top
if '{% from "components/pagination.html" import render_pagination %}' not in content:
    content = content.replace('{% extends "base.html" %}', '{% extends "base.html" %}\n{% from "components/pagination.html" import render_pagination %}')

# 2. Add breakdown CSS
css_to_add = """
    .breakdown-toggle {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--mq-primary-green-dark);
        background: var(--mq-green-bg);
        border: none;
        border-radius: 6px;
        padding: 0.4rem 0.75rem;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        transition: background 0.15s ease;
    }
    .breakdown-toggle:hover { background: #d1fae5; }
    .breakdown-toggle .chev { transition: transform 0.2s ease; font-size: 0.65rem; }
    .breakdown-toggle.open .chev { transform: rotate(180deg); }

    .breakdown-panel {
        display: none;
        background: var(--mq-bg-white);
        border-top: 1px solid var(--mq-border-color);
        padding: 1.25rem;
        border-bottom-left-radius: 12px;
        border-bottom-right-radius: 12px;
    }
    .breakdown-panel.open {
        display: block;
    }
    .breakdown-inner {
        width: 100%;
        margin: 0 auto;
    }
    .breakdown-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1rem;
        font-size: 0.78rem;
    }
    .breakdown-table th,
    .breakdown-table td {
        padding: 0.6rem 0.8rem;
        text-align: left;
        border-bottom: 1px solid var(--mq-border-color);
    }
    .breakdown-table th {
        font-weight: 600;
        color: var(--mq-text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.7rem;
    }
    .breakdown-table th.num,
    .breakdown-table td.num {
        text-align: right;
    }
    .breakdown-table .code-cell {
        font-family: monospace;
        font-size: 0.75rem;
        color: var(--mq-primary-blue-dark);
        background: #eff6ff;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
    }
    .breakdown-table .base-cell {
        font-size: 0.75rem;
        color: var(--mq-text-secondary);
        background: var(--mq-bg-gray);
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        border: 1px solid var(--mq-border-color);
    }
    .breakdown-table .final-cell {
        font-weight: 700;
        color: var(--mq-text-primary);
    }
"""

if '.breakdown-panel {' not in content:
    content = content.replace('.breakdown-toggle {', css_to_add + '\n    /* removed old toggle */\n    .old-toggle {')
    # If the old toggle wasn't there, we replace '.empty-state {'
    if '.old-toggle {' not in content:
        content = content.replace('.empty-state {', css_to_add + '\n    .empty-state {')

# 3. Replace the View Breakdown button
old_button = '<a href="{{ url_for(\'customer.quote_detail\', quote_id=q.id) }}" class="breakdown-toggle" style="text-decoration: none;">📊 View Breakdown</a>'
new_button = '<button onclick="toggleQuoteBreakdown({{ q.id }}, this)" class="breakdown-toggle">📊 View Breakdown <span class="chev">▾</span></button>'
content = content.replace(old_button, new_button)

# 4. Insert the hidden panel after offer-footer
panel_html = """
                <!-- Inline Breakdown Panel -->
                <div id="breakdown-panel-{{ q.id }}" class="breakdown-panel" style="background: var(--mq-bg-gray);">
                    <div class="breakdown-inner">
                        <div id="breakdown-content-{{ q.id }}" class="text-center text-muted py-3" style="font-size: 0.8rem;">
                            <div class="spinner-border spinner-border-sm text-primary" role="status"></div> Loading breakdown...
                        </div>
                    </div>
                </div>
            </div>
"""
# Replace the end of the card
if 'id="breakdown-panel' not in content:
    content = content.replace('</div>\n            </div>\n        {% endfor %}', '</div>\n' + panel_html + '        {% endfor %}')
    content = content.replace('</div>\n        {% endfor %}', '</div>\n' + panel_html + '        {% endfor %}')


# 5. Add Pagination block
old_pagination_block = """    <!-- Pagination -->
    {% if pagination and pagination.pages > 1 %}
    <nav aria-label="Quote pages" class="mt-4 mb-2">
        <ul class="pagination d-flex justify-content-between align-items-center w-100 m-0">
            <!-- Previous Button on Left -->
            <li class="page-item {% if not pagination.has_prev %}disabled{% endif %} m-0">
                <a class="page-link shadow-sm rounded border-0 bg-white text-dark px-3 py-2" href="{{ url_for('customer.my_quotes', page=pagination.prev_num) if pagination.has_prev else '#' }}">← Previous</a>
            </li>
            
            <!-- Page Numbers in Center -->
            <div class="d-flex" style="gap: 0.25rem;">
                {% for page_num in pagination.iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2) %}
                    {% if page_num %}
                        <li class="page-item {% if page_num == pagination.page %}active{% endif %}">
                            <a class="page-link shadow-sm rounded border-0 {% if page_num == pagination.page %}bg-primary text-white fw-bold{% else %}bg-white text-dark{% endif %}" 
                               href="{{ url_for('customer.my_quotes', page=page_num) }}">{{ page_num }}</a>
                        </li>
                    {% else %}
                        <li class="page-item disabled"><span class="page-link border-0 bg-transparent text-muted">...</span></li>
                    {% endif %}
                {% endfor %}
            </div>
            
            <!-- Next Button on Right -->
            <li class="page-item {% if not pagination.has_next %}disabled{% endif %} m-0">
                <a class="page-link shadow-sm rounded border-0 bg-white text-dark px-3 py-2" href="{{ url_for('customer.my_quotes', page=pagination.next_num) if pagination.has_next else '#' }}">Next →</a>
            </li>
        </ul>
    </nav>
    {% endif %}"""

if old_pagination_block in content:
    content = content.replace(old_pagination_block, "    <!-- Pagination -->\n    {{ render_pagination(pagination, 'customer.my_quotes') }}")


# 6. Add JS logic
js_code = """
    function toggleQuoteBreakdown(quoteId, btn) {
        const panel = document.getElementById('breakdown-panel-' + quoteId);
        const contentDiv = document.getElementById('breakdown-content-' + quoteId);
        const isOpen = panel.classList.contains('open');

        if (isOpen) {
            panel.classList.remove('open');
            btn.classList.remove('open');
            btn.innerHTML = '📊 View Breakdown <span class="chev">▾</span>';
        } else {
            panel.classList.add('open');
            btn.classList.add('open');
            btn.innerHTML = '📊 Hide Breakdown <span class="chev">▴</span>';

            if (!panel.dataset.loaded) {
                fetch(`/api/quote/${quoteId}/breakdown`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.breakdown && data.breakdown.length > 0) {
                            let rows = '';
                            data.breakdown.forEach(line => {
                                const chargeCode = line.chargeCode || line.id || 'N/A';
                                const description = line.chargeName || line.description || 'Standard Charge';
                                const unitCode = line.unitCode || 'ACT';
                                const qty = line.quantity || 1;
                                const curr = line.currency || 'USD';
                                const amt = parseFloat(line.amount).toFixed(2);
                                
                                rows += `<tr>
                                    <td><span class="code-cell">${chargeCode}</span></td>
                                    <td>${description}</td>
                                    <td><span class="base-cell">${unitCode}</span></td>
                                    <td class="num">${qty}</td>
                                    <td class="num">${curr} ${amt}</td>
                                    <td class="num fx-cell">1 ${curr} = 1.0000 USD</td>
                                    <td class="num final-cell">USD ${amt}</td>
                                </tr>`;
                            });

                            contentDiv.innerHTML = `
                                <table class="breakdown-table" style="background: var(--mq-bg-white); border: 1px solid var(--mq-border-color); border-radius: 8px; overflow: hidden; margin-bottom: 0;">
                                    <thead style="background: #f1f5f9;">
                                        <tr>
                                            <th>Code</th>
                                            <th>Name</th>
                                            <th>Base</th>
                                            <th class="num">Units</th>
                                            <th class="num">Unit Price</th>
                                            <th class="num">Rate of Exchange</th>
                                            <th class="num">Final Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${rows}
                                    </tbody>
                                </table>`;
                        } else {
                            contentDiv.innerHTML = `<div class="py-4 text-center">No breakdown details available for this quote.</div>`;
                        }
                        panel.dataset.loaded = "true";
                    })
                    .catch(err => {
                        contentDiv.innerHTML = `<div class="py-4 text-center text-danger">Failed to load breakdown.</div>`;
                    });
            }
        }
    }

    // High-performance AJAX Pagination
    document.addEventListener('DOMContentLoaded', function() {
        document.body.addEventListener('click', function(e) {
            let target = e.target.closest('.pagination .page-link');
            if (target && target.getAttribute('href') && target.getAttribute('href') !== '#') {
                e.preventDefault();
                let url = target.getAttribute('href');
                let offersList = document.querySelector('.offers-list');
                let paginationNav = document.querySelector('.pagination-container') || target.closest('nav');
                
                if (offersList) offersList.style.opacity = '0.5';
                
                fetch(url)
                    .then(response => response.text())
                    .then(html => {
                        let parser = new DOMParser();
                        let doc = parser.parseFromString(html, 'text/html');
                        
                        let newOffers = doc.querySelector('.offers-list');
                        if (newOffers && offersList) {
                            offersList.innerHTML = newOffers.innerHTML;
                            offersList.style.opacity = '1';
                        }
                        
                        let newNav = doc.querySelector('.pagination-container') || doc.querySelector('.pagination').parentNode;
                        if (newNav && paginationNav) {
                            paginationNav.innerHTML = newNav.innerHTML;
                        }
                        
                        window.history.pushState({path: url}, '', url);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    })
                    .catch(err => {
                        console.error('Pagination failed', err);
                        window.location.href = url; 
                    });
            }
        });
    });
"""
if 'toggleQuoteBreakdown' not in content:
    content = content.replace('function copyRef(el) {', js_code + '\n    function copyRef(el) {')


with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch applied.")
