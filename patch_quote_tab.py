import re

def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Update onclick
    old_onclick = "onclick=\"window.location.href=`{{ url_for('customer.my_quotes') }}`\""
    new_onclick = "onclick=\"selectBookingMode('quote')\""
    text = text.replace(old_onclick, new_onclick)

    # 2. Update selectBookingMode
    old_func = """function selectBookingMode(mode) {
            bookingMode = mode;
            document.getElementById('oceanTabHeader').classList.toggle('active', mode === 'ocean');
            document.getElementById('airTabHeader').classList.toggle('active', mode === 'air');
            document.getElementById('quoteTabHeader').classList.toggle('active', mode === 'quote');
            const airBanner = document.getElementById('airBanner');
            const stepsRibbon = document.getElementById('stepsRibbon');
            const panelsContainer = document.querySelector('.panels-container');
            if (mode === 'air') {
                airBanner.style.display = 'block';
                stepsRibbon.style.display = 'none';
                panelsContainer.style.display = 'none';
                document.getElementById('quotePicker').classList.remove('show');
            } else {
                airBanner.style.display = 'none';
                stepsRibbon.style.display = 'flex';
                panelsContainer.style.display = 'block';
                document.getElementById('quotePicker').classList.remove('show');
            }
        }"""
    
    new_func = """function selectBookingMode(mode) {
            bookingMode = mode;
            document.getElementById('oceanTabHeader').classList.toggle('active', mode === 'ocean');
            document.getElementById('airTabHeader').classList.toggle('active', mode === 'air');
            document.getElementById('quoteTabHeader').classList.toggle('active', mode === 'quote');
            const airBanner = document.getElementById('airBanner');
            const stepsRibbon = document.getElementById('stepsRibbon');
            const panelsContainer = document.querySelector('.panels-container');
            const quotePicker = document.getElementById('quotePicker');
            if (mode === 'air') {
                airBanner.style.display = 'block';
                stepsRibbon.style.display = 'none';
                panelsContainer.style.display = 'none';
                quotePicker.classList.remove('show');
            } else if (mode === 'quote') {
                airBanner.style.display = 'none';
                stepsRibbon.style.display = 'none';
                panelsContainer.style.display = 'none';
                quotePicker.classList.add('show');
            } else {
                airBanner.style.display = 'none';
                stepsRibbon.style.display = 'flex';
                panelsContainer.style.display = 'block';
                quotePicker.classList.remove('show');
            }
        }"""
    
    # We will use regex just in case formatting slightly differs
    if 'if (mode === \'quote\') {' not in text:
        # replace the function manually
        idx = text.find('function selectBookingMode')
        end_idx = text.find('}', text.find('}', text.find('}', idx) + 1) + 1) + 1
        if idx != -1:
            text = text[:idx] + new_func + text[end_idx:]

    # 3. Update useQuote
    if "selectBookingMode('ocean');" not in text:
        text = text.replace("document.getElementById('quotePicker').classList.remove('show');\n            document.getElementById('linkedQuoteBanner').classList.add('show');", 
                            "selectBookingMode('ocean');\n            document.getElementById('linkedQuoteBanner').classList.add('show');")

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched quote tab logic successfully.")

if __name__ == '__main__':
    main()
