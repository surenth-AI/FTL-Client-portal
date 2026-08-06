with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

pagination_html = """                </div>
                <!-- Pagination Controls -->
                <div class="picker-pagination" id="pickerPagination" style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem;">
                    <button class="btn btn-secondary btn-small" id="pickerPrevBtn" onclick="changePickerPage(-1)">Previous</button>
                    <span id="pickerPageInfo" style="font-size:0.85rem; color:var(--text-muted);">Page 1 of 1</span>
                    <button class="btn btn-secondary btn-small" id="pickerNextBtn" onclick="changePickerPage(1)">Next</button>
                </div>"""

text = text.replace('</div>\n                <div class="form-help" style="margin-top:0.6rem;">', pagination_html + '\n                <div class="form-help" style="margin-top:0.6rem;">')

# Now update the javascript
js_code = """
        let pickerCurrentPage = 1;
        const pickerItemsPerPage = 5;

        function filterPicker() {
            const term = document.getElementById('pickerSearch').value.toLowerCase().trim();
            const cards = Array.from(document.querySelectorAll('.picker-card'));
            
            // First filter
            const visibleCards = cards.filter(card => {
                const haystack = (card.dataset.ref + ' ' + card.dataset.route).toLowerCase();
                const isMatch = !term || haystack.includes(term);
                return isMatch;
            });
            
            // Then paginate
            const totalPages = Math.ceil(visibleCards.length / pickerItemsPerPage) || 1;
            if (pickerCurrentPage > totalPages) pickerCurrentPage = totalPages;
            
            const startIdx = (pickerCurrentPage - 1) * pickerItemsPerPage;
            const endIdx = startIdx + pickerItemsPerPage;
            
            cards.forEach(card => card.style.display = 'none'); // hide all
            
            visibleCards.slice(startIdx, endIdx).forEach(card => card.style.display = ''); // show paginated
            
            // Update controls
            const prevBtn = document.getElementById('pickerPrevBtn');
            const nextBtn = document.getElementById('pickerNextBtn');
            const info = document.getElementById('pickerPageInfo');
            
            if (prevBtn) prevBtn.disabled = pickerCurrentPage === 1;
            if (nextBtn) nextBtn.disabled = pickerCurrentPage === totalPages;
            if (info) info.textContent = `Page ${pickerCurrentPage} of ${totalPages}`;
        }

        function changePickerPage(delta) {
            pickerCurrentPage += delta;
            filterPicker();
        }
"""

# Replace the original filterPicker
old_filter = """function filterPicker() {
            const term = document.getElementById('pickerSearch').value.toLowerCase().trim();
            document.querySelectorAll('.picker-card').forEach(card => {
                const haystack = (card.dataset.ref + ' ' + card.dataset.route).toLowerCase();
                card.style.display = !term || haystack.includes(term) ? '' : 'none';
            });
        }"""

text = text.replace(old_filter, js_code)

# Add initialization logic to selectBookingMode
old_select = """document.getElementById('pickerSearch').value = '';
            filterPicker();"""
new_select = """document.getElementById('pickerSearch').value = '';
            pickerCurrentPage = 1;
            filterPicker();"""

text = text.replace(old_select, new_select)

with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Added JS and HTML for pagination')
