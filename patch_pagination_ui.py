with open('app/templates/customer/new_booking.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the simple pagination HTML
old_html = """                <!-- Pagination Controls -->
                <div class="picker-pagination" id="pickerPagination" style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem;">
                    <button class="btn btn-secondary btn-small" id="pickerPrevBtn" onclick="changePickerPage(-1)">Previous</button>
                    <span id="pickerPageInfo" style="font-size:0.85rem; color:var(--text-muted);">Page 1 of 1</span>
                    <button class="btn btn-secondary btn-small" id="pickerNextBtn" onclick="changePickerPage(1)">Next</button>
                </div>"""

new_html = """                <!-- Pagination Controls -->
                <div class="d-flex align-items-center justify-content-center mt-3 mb-2 flex-wrap gap-3 pagination-container" id="pickerPagination">
                    <nav aria-label="Pagination">
                        <ul class="pagination d-flex align-items-center m-0" style="gap: 0.25rem;" id="pickerPaginationList">
                            <!-- Injected by JS -->
                        </ul>
                    </nav>
                </div>"""

text = text.replace(old_html, new_html)

old_js = """            // Update controls
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
        }"""

new_js = """            // Render Pagination UI matching pagination.html
            const paginationList = document.getElementById('pickerPaginationList');
            if (!paginationList) return;
            
            let html = '';
            
            // Prev Button
            const prevDisabled = pickerCurrentPage === 1 ? 'disabled' : '';
            html += `<li class="page-item ${prevDisabled} m-0">
                        <a class="page-link shadow-sm rounded border-0 bg-white text-dark px-3 py-2" 
                           href="javascript:void(0)" onclick="if(${pickerCurrentPage} > 1) { pickerCurrentPage--; filterPicker(); }">
                             Previous
                        </a>
                    </li>`;
            
            html += `<div class="d-flex" style="gap: 0.25rem;">`;
            for (let i = 1; i <= totalPages; i++) {
                const activeClass = i === pickerCurrentPage ? 'active' : '';
                const linkClass = i === pickerCurrentPage ? 'bg-primary text-white fw-bold' : 'bg-white text-dark';
                html += `<li class="page-item ${activeClass}">
                            <a class="page-link shadow-sm rounded border-0 ${linkClass}" 
                               href="javascript:void(0)" onclick="pickerCurrentPage = ${i}; filterPicker();">${i}</a>
                        </li>`;
            }
            html += `</div>`;
            
            // Next Button
            const nextDisabled = pickerCurrentPage === totalPages ? 'disabled' : '';
            html += `<li class="page-item ${nextDisabled} m-0">
                        <a class="page-link shadow-sm rounded border-0 bg-white text-dark px-3 py-2" 
                           href="javascript:void(0)" onclick="if(${pickerCurrentPage} < ${totalPages}) { pickerCurrentPage++; filterPicker(); }">
                            Next 
                        </a>
                    </li>`;
            
            paginationList.innerHTML = html;
        }"""

text = text.replace(old_js, new_js)

with open('app/templates/customer/new_booking.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated pagination UI')
