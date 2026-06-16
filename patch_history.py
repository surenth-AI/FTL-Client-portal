import os

# Patch rate_results.html for Auto-saving
filepath_results = r'd:\FTL-DEV\app\templates\customer\rate_results.html'
with open(filepath_results, 'r', encoding='utf-8') as f:
    content_res = f.read()

autosave_js = """
    // Autosave cheapest quote if user leaves without booking
    let isBooking = false;
    document.querySelectorAll('form').forEach(f => f.addEventListener('submit', () => isBooking = true));
    
    window.addEventListener('beforeunload', function (e) {
        if (isBooking) return;
        let history = JSON.parse(localStorage.getItem('ftl_search_history') || '[]');
        history.unshift({
            date: new Date().toLocaleString(),
            origin: "{{ query.origin }}",
            destination: "{{ query.destination }}",
            service: "{{ query.service_type }}",
            details: "Auto-saved (Cheapest Quote)"
        });
        localStorage.setItem('ftl_search_history', JSON.stringify(history.slice(0, 15)));
    });
</script>
"""
content_res = content_res.replace('</script>', autosave_js, 1)

with open(filepath_results, 'w', encoding='utf-8') as f:
    f.write(content_res)

# Patch rates.html for History Logs
filepath_rates = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath_rates, 'r', encoding='utf-8') as f:
    content_rates = f.read()

target_history = """            history = [
                { date: '2026-05-20 09:30 AM', origin: 'Shanghai (CNSHA)', destination: 'Hamburg (DEHAM)', service: 'Port to Port (Less than a container load)', details: 'General Cargo, 2.50 CBM' },
                { date: '2026-05-22 04:15 PM', origin: 'Singapore (SGPIN)', destination: 'Rotterdam (NLRTM)', service: 'Port to Port (Full container load)', details: 'General Cargo, 1 × Container' },
                { date: '2026-05-24 11:05 AM', origin: 'Shanghai (CNSHA)', destination: 'Los Angeles (USLAX)', service: 'Port to Port (Less than a container load)', details: 'General Cargo, 5.20 CBM' }
            ];"""

replacement_history = """            history = [
                { date: '2026-06-08 10:15 AM', origin: 'Shanghai (CNSHA)', destination: 'Los Angeles (USLAX)', service: 'Less than a container load', details: 'Auto-saved by system (Cheapest)' },
                { date: '2026-06-07 04:30 PM', origin: 'Singapore (SGSIN)', destination: 'Unknown (XYZ)', service: 'Search Log', details: '<span class="text-danger"><i class="bi bi-x-circle"></i> No Results Found</span>' },
                { date: '2026-06-06 09:12 AM', origin: 'Rotterdam (NLRTM)', destination: 'New York (USNYC)', service: 'Full container load', details: '<span class="text-primary"><i class="bi bi-person-workspace"></i> Generated via ATLAS by Sales Staff</span>' }
            ];"""

content_rates = content_rates.replace(target_history, replacement_history)

with open(filepath_rates, 'w', encoding='utf-8') as f:
    f.write(content_rates)

print("History and Autosave logic patched.")
