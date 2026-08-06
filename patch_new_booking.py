import re

def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Replace the pickerList content
    old_picker_list = """                <div class="picker-list" id="pickerList">
                    <div class="picker-card" data-ref="FTL-QR-548213" data-route="Antwerp Nhava Sheva">
                        <div class="picker-info">
                            <span class="picker-ref">FTL-QR-548213</span>
                            <span class="picker-route">Antwerp (BEANR) &rarr; Nhava Sheva (INNSA)</span>
                            <span class="picker-meta">📦 LCL &middot; Direct Service <span
                                    class="picker-status expiring">Expiring Soon</span></span>
                        </div>
                        <div style="display:flex; align-items:center; gap:1rem;">
                            <span class="picker-price">USD 71.80</span>
                            <button class="btn btn-secondary btn-small" onclick="useQuote('FTL-QR-548213')">Use this
                                quote</button>
                        </div>
                    </div>
                    <div class="picker-card" data-ref="FTL-QR-219804" data-route="Barcelona Shanghai">
                        <div class="picker-info">
                            <span class="picker-ref">FTL-QR-219804</span>
                            <span class="picker-route">Barcelona (ESBCN) &rarr; Shanghai (CNSHA)</span>
                            <span class="picker-meta">📦 LCL &middot; Standard Service <span
                                    class="picker-status active">Active</span></span>
                        </div>
                        <div style="display:flex; align-items:center; gap:1rem;">
                            <span class="picker-price">USD 145.30</span>
                            <button class="btn btn-secondary btn-small" onclick="useQuote('FTL-QR-219804')">Use this
                                quote</button>
                        </div>
                    </div>
                </div>"""

    new_picker_list = """                <div class="picker-list" id="pickerList">
                    {% if valid_quotes %}
                        {% for q in valid_quotes %}
                        <div class="picker-card" data-ref="{{ q.api_booking_ref or ('QUO-' ~ q.id) }}" data-route="{{ q.origin | default('') }} {{ q.destination | default('') }}">
                            <div class="picker-info">
                                <span class="picker-ref">{{ q.api_booking_ref or ('QUO-' ~ q.id) }}</span>
                                <span class="picker-route">{{ q.origin | default('') }} &rarr; {{ q.destination | default('') }}</span>
                                <span class="picker-meta">📦 {{ q.service_type | default('LCL') }} &middot; Standard Service <span
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
                </div>"""

    # Use regex to replace the pickerList div because formatting might differ slightly
    text = re.sub(r'<div class="picker-list" id="pickerList">.*?</div>\s*</div>', new_picker_list + '\n            </div>', text, flags=re.DOTALL)
    print("Replaced pickerList")

    # 2. Replace quoteData
    new_quote_data = """        const quoteData = {
            {% for q in valid_quotes %}
            "{{ q.api_booking_ref or ('QUO-' ~ q.id) }}": {
                route: "{{ q.origin | default('') }} &rarr; {{ q.destination | default('') }}",
                price: "USD {{ '%.2f'|format(q.total_cost|float) if q.total_cost else 'TBC' }}",
                originType: 'port',
                originCountry: '',
                originLocation: "{{ q.origin | default('') }}",
                destType: 'port',
                destCountry: '',
                destLocation: "{{ q.destination | default('') }}",
                pieces: 1,
                packageType: 'pallets',
                goodsType: 'GENERAL',
                weight: {{ q.volume * 167 if q.volume else 1000 }},
                volume: {{ q.volume if q.volume else 2 }},
                readyDate: "{{ q.etd.strftime('%Y-%m-%d') if q.etd else (q.created_at.strftime('%Y-%m-%d') if q.created_at else '') }}"
            }{% if not loop.last %},{% endif %}
            {% endfor %}
        };"""

    text = re.sub(r'const quoteData = \{.*?\};', new_quote_data, text, flags=re.DOTALL)
    print("Replaced quoteData")

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == '__main__':
    main()
