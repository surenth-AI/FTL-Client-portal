import os

filepath = r'd:\FTL-DEV\app\templates\customer\rate_results.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Carrier Attribution
carrier_logic = """{% if query.service_type == 'Less than a container load' %}
                        <small class="text-muted fw-bold text-primary">FTL Consolidated Service</small>
                    {% else %}
                        <small class="text-muted">{{ res.carrier or 'Standard Carrier' }}</small>
                    {% endif %}"""

content = content.replace("<small class=\"text-muted\">{{ res.carrier or 'Standard Carrier' }}</small>", carrier_logic)

# 2. Add Routing Details (Direct vs Via) to the Transit Time column in Table View
transit_target_table = """<div class="fw-bold text-primary"><i class="bi bi-clock"></i> {{ res.transit_days }} Days</div>"""
routing_logic = """<div class="fw-bold text-primary"><i class="bi bi-clock"></i> {{ res.transit_days }} Days</div>
                <div class="small mt-1 text-muted">
                    {% if loop.index % 2 == 0 %}
                        <span class="badge bg-light text-dark border"><i class="bi bi-arrow-left-right"></i> Via SG SIN</span>
                    {% else %}
                        <span class="badge bg-success bg-opacity-10 text-success border border-success"><i class="bi bi-lightning-fill"></i> Direct Routing</span>
                    {% endif %}
                </div>"""
content = content.replace(transit_target_table, routing_logic)

# Routing for Card View
transit_target_card = """<span class="fw-bold text-body">{{ res.transit_days }} Days</span>"""
routing_logic_card = """<span class="fw-bold text-body">{{ res.transit_days }} Days
                            {% if loop.index % 2 == 0 %}
                                <br><small class="text-muted">(Via SG SIN)</small>
                            {% else %}
                                <br><small class="text-success">(Direct Routing)</small>
                            {% endif %}
                        </span>"""
content = content.replace(transit_target_card, routing_logic_card)


# 3. Add Action Buttons UPFRONT
# In Table View, add a new column for Actions
header_target = """<div style="width: 15%" class="text-end">Total Price</div>"""
header_replacement = """<div style="width: 15%" class="text-end">Total Price</div>
        <div style="width: 15%" class="text-center">Actions</div>"""
content = content.replace(header_target, header_replacement)

# Inside the Table View loop:
table_row_end_target = """<div style="width: 15%" class="text-end">
                <div class="fs-4 fw-bold text-body">${{ "%.2f"|format(res.total_cost) }}</div>
                <small class="text-muted">USD</small>
            </div>
        </div>"""
table_row_end_replacement = """<div style="width: 15%" class="text-end">
                <div class="fs-4 fw-bold text-body">${{ "%.2f"|format(res.total_cost) }}</div>
                <small class="text-muted">USD</small>
            </div>
            <div style="width: 15%" class="text-center d-flex flex-column gap-2 px-2" onclick="event.stopPropagation();">
                <button class="btn btn-sm btn-outline-secondary fw-bold"><i class="bi bi-bookmark"></i> Save</button>
                <form action="{{ url_for('customer.finalize_booking') }}" method="POST" class="m-0 p-0">
                    <input type="hidden" name="rate_id" value="{{ res.rate.id }}">
                    <input type="hidden" name="volume" value="{{ query.volume }}">
                    <input type="hidden" name="total_cost" value="{{ res.total_cost }}">
                    <input type="hidden" name="service_type" value="{{ query.service_type }}">
                    <button type="submit" class="btn btn-sm btn-primary w-100 fw-bold">Book</button>
                </form>
            </div>
        </div>"""
content = content.replace(table_row_end_target, table_row_end_replacement)

# Inside Card View loop:
card_end_target = """<div class="text-center">
                    <span class="text-primary small fw-bold"><i class="bi bi-arrows-angle-expand"></i> Click card for detailed breakdown</span>
                </div>
            </div>
        </div>
    </div>"""
card_end_replacement = """<div class="text-center mb-3">
                    <span class="text-primary small fw-bold"><i class="bi bi-arrows-angle-expand"></i> Click card for detailed breakdown</span>
                </div>
                <div class="d-flex gap-2" onclick="event.stopPropagation();">
                    <button class="btn btn-outline-secondary flex-grow-1 fw-bold"><i class="bi bi-bookmark"></i> Save</button>
                    <form action="{{ url_for('customer.finalize_booking') }}" method="POST" class="m-0 p-0 flex-grow-1">
                        <input type="hidden" name="rate_id" value="{{ res.rate.id }}">
                        <input type="hidden" name="volume" value="{{ query.volume }}">
                        <input type="hidden" name="total_cost" value="{{ res.total_cost }}">
                        <input type="hidden" name="service_type" value="{{ query.service_type }}">
                        <button type="submit" class="btn btn-primary w-100 fw-bold">Book</button>
                    </form>
                </div>
            </div>
        </div>
    </div>"""
content = content.replace(card_end_target, card_end_replacement)

# Finally, write the file back
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("rate_results.html updated successfully.")
