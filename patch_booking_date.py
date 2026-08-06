def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # Add Date Input
    date_input = '''                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label class="form-label" for="cargoReadyDate">Requested Cargo Ready Date</label>
                                <input type="date" id="cargoReadyDate" class="form-input" onchange="filterSailingsByDate()">
                            </div>
                            <div class="sailing-card">'''
    if 'cargoReadyDate' not in text:
        text = text.replace('<div class="sailing-card">', date_input, 1)

    # Add JS Logic
    js_to_add = '''
        function filterSailingsByDate() {
            const dateStr = document.getElementById('cargoReadyDate').value;
            if (dateStr) {
                sailings = mockSailings.filter(s => new Date(s.etd) >= new Date(dateStr));
            } else {
                sailings = [...mockSailings];
            }
            selectedSailingIndex = 0;
            if (sailings.length > 0) {
                renderSailingCard();
            } else {
                document.getElementById('sailingVesselText').innerHTML = 'No available sailings';
                document.getElementById('sailingDatesText').textContent = 'Please choose a different date';
            }
            if (document.getElementById('sailingPicker').classList.contains('show')) {
                renderSailingPickerList();
            }
        }
        
        function renderSailingCard'''
    if 'filterSailingsByDate' not in text:
        text = text.replace('function renderSailingCard', js_to_add)

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Patched successfully')

if __name__ == '__main__':
    main()
