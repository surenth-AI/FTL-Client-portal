def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Remove the old field
    old_field = """                                <div class="form-group">
                                    <label class="form-label">Requested Cargo Ready Date <span
                                            class="required">*</span></label>
                                    <input type="date" class="form-input" id="cargoReadyDate" required>
                                </div>"""

    if old_field in text:
        text = text.replace(old_field, "")
        print("Removed old field")
    else:
        print("Could not find old field")

    # 2. Add the field to the sailing card
    old_sailing_card = """                            <div class="sailing-card">
                                <div class="sailing-info">
                                    <div class="sailing-vessel" id="sailingVesselText">—</div>
                                    <div class="sailing-dates" id="sailingDatesText">—</div>
                                </div>
                                <button type="button" class="btn btn-secondary btn-small"
                                    onclick="toggleSailingPicker()">Change Sailing</button>
                            </div>"""

    new_sailing_card = """                            <div class="sailing-card">
                                <div class="sailing-info">
                                    <div class="sailing-vessel" id="sailingVesselText">—</div>
                                    <div class="sailing-dates" id="sailingDatesText">—</div>
                                </div>
                                <div style="display:flex; align-items:flex-end; gap: 1rem;">
                                    <div class="form-group" style="margin-bottom: 0;">
                                        <label class="form-label" for="cargoReadyDate" style="font-size: 0.75rem; color: var(--text-secondary);">Cargo Ready Date <span class="required">*</span></label>
                                        <input type="date" class="form-input" id="cargoReadyDate" onchange="filterSailingsByDate()" required style="padding: 0.25rem 0.5rem; min-height: 32px;">
                                    </div>
                                    <button type="button" class="btn btn-secondary btn-small"
                                        onclick="toggleSailingPicker()" style="height: 32px;">Change Sailing</button>
                                </div>
                            </div>"""

    if old_sailing_card in text:
        text = text.replace(old_sailing_card, new_sailing_card)
        print("Added new field to sailing card")
    else:
        print("Could not find sailing card")

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)

if __name__ == '__main__':
    main()
