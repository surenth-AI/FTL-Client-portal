import re

def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

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
                if (quotePicker) quotePicker.classList.remove('show');
            } else if (mode === 'quote') {
                airBanner.style.display = 'none';
                stepsRibbon.style.display = 'none';
                panelsContainer.style.display = 'none';
                if (quotePicker) quotePicker.classList.add('show');
            } else {
                airBanner.style.display = 'none';
                stepsRibbon.style.display = 'flex';
                panelsContainer.style.display = 'block';
                if (quotePicker) quotePicker.classList.remove('show');
            }
        }"""
    
    # regex replace selectBookingMode
    pattern = r"function selectBookingMode\(mode\) \{.*?(?=\n\s+const quoteData)"
    text = re.sub(pattern, new_func + "\n", text, flags=re.DOTALL)

    # regex replace useQuote
    pattern_uq = r"document\.getElementById\('quotePicker'\)\.classList\.remove\('show'\);\s*document\.getElementById\('linkedQuoteBanner'\)\.classList\.add\('show'\);"
    replacement_uq = "selectBookingMode('ocean');\n            document.getElementById('linkedQuoteBanner').classList.add('show');"
    text = re.sub(pattern_uq, replacement_uq, text)

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Force patched selectBookingMode")

if __name__ == '__main__':
    main()
