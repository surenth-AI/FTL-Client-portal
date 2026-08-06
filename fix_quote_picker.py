with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('<!-- Quote picker -->')
idx2 = text.find('<!-- Linked quote banner -->')

replacement = """<!-- Quote picker -->
            <div class="quote-picker" id="quotePicker">
                <div class="picker-search">
                    <input type="text" id="pickerSearch" placeholder="Search your quotes by reference or route"
                        oninput="filterPicker()">
                </div>
                <div class="picker-list" id="pickerList">
                    {% if valid_quotes %}
                        {% for q in valid_quotes %}
                        <div class="picker-card" data-ref="{{ q.api_booking_ref or ('QUO-' ~ q.id) }}" data-route="{{ q.origin | default('') }} {{ q.destination | default('') }}">
                            <div class="picker-info">
                                <span class="picker-ref">{{ q.api_booking_ref or ('QUO-' ~ q.id) }}</span>
                                <span class="picker-route">{{ q.origin | default('') }} &rarr; {{ q.destination | default('') }}</span>
                                <span class="picker-meta"> {{ q.service_type | default('LCL') }} &middot; Standard Service <span
                                        class="picker-status {{ q.computed_status | lower | replace(' ', '-') }}">{{ q.computed_status }}</span></span>
                            </div>
                            <div style="display:flex; align-items:center; gap:1rem;">
                                <span class="picker-price">USD {{ "%.2f"|format(q.total_cost|float) if q.total_cost else 'TBC' }}</span>
                                <button class="btn btn-secondary btn-small" onclick="useQuote('{{ q.api_booking_ref or ('QUO-' ~ q.id) }}')">Use this quote</button>
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <div style="padding: 1rem; color: var(--text-muted); font-size: 0.9rem; text-align: center;">You have no active or expiring quotes.</div>
                    {% endif %}
                </div>
                <div class="form-help" style="margin-top:0.6rem;">Only Active and Expiring quotes can be converted to a booking. Booked or expired quotes won't appear here.</div>
            </div>

            """

if idx1 != -1 and idx2 != -1:
    text = text[:idx1] + replacement + text[idx2:]
    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed quote picker structure!")
else:
    print("Could not find boundaries")
