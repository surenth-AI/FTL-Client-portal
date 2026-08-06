def main():
    with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Update changeQuote
    old_changequote = """        function changeQuote() {
            document.getElementById('quotePicker').classList.add('show');
        }"""
        
    new_changequote = """        function changeQuote() {
            clearLinkedQuote();
            selectBookingMode('quote');
        }"""

    if old_changequote in text:
        text = text.replace(old_changequote, new_changequote)
        print('Updated changeQuote')
    else:
        print('Could not find changeQuote block')

    # 2. Update useQuote end
    old_usequote_end = """            updateDocumentRequirements();
            updateRateSummary();
            showAlert('Quote ' + ref + ' linked. Route and cargo details have been pre-filled \u2014 feel free to adjust them.');"""
            
    new_usequote_end = """            updateDocumentRequirements();
            updateRateSummary();
            updateReview();
            showAlert('Quote ' + ref + ' linked. Route and cargo details have been pre-filled \u2014 feel free to adjust them.');"""

    if old_usequote_end in text:
        text = text.replace(old_usequote_end, new_usequote_end)
        print('Updated useQuote end')
    else:
        print('Could not find useQuote end block')
        # Try alternate without unicode char
        old_usequote_end_alt = "updateRateSummary();\n            showAlert('Quote ' + ref + ' linked."
        new_usequote_end_alt = "updateRateSummary();\n            updateReview();\n            showAlert('Quote ' + ref + ' linked."
        if old_usequote_end_alt in text:
             text = text.replace(old_usequote_end_alt, new_usequote_end_alt)
             print('Updated useQuote end alt')

    with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
        f.write(text)

    print('Updated new_booking.html')

if __name__ == '__main__':
    main()
