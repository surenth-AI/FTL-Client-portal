import os
import re

filepath = r'd:\FTL-DEV\app\routes\customer.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

target_post_logic = """    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        service_type = request.form.get('service_type', 'LCL')
        total_volume = 0.0
        cargo_items = []
        if service_type == 'LCL':
            item_qtys = request.form.getlist('item_qty[]')
            item_types = request.form.getlist('item_type[]')
            item_weights = request.form.getlist('item_weight[]')
            item_volumes = request.form.getlist('item_volume[]')
            for i in range(len(item_qtys)):
                vol = float(item_volumes[i]) if i < len(item_volumes) and item_volumes[i] else 0.0
                total_volume += vol
                cargo_items.append({'qty': item_qtys[i], 'type': item_types[i],
                                    'weight': item_weights[i], 'volume': vol})
        else:
            cont_types = request.form.getlist('cont_type[]')
            cont_qtys = request.form.getlist('cont_qty[]')
            c_volumes = request.form.getlist('cont_volume[]')
            for i in range(len(cont_types)):
                vol = float(c_volumes[i]) if i < len(c_volumes) and c_volumes[i] else 0.0
                qty = int(cont_qtys[i]) if i < len(cont_qtys) and cont_qtys[i] else 1
                total_volume += (vol * qty)
                cargo_items.append({'cont_type': cont_types[i], 'cont_qty': qty, 'volume': vol})
        session['search_query'] = {
            'origin': origin,
            'destination': destination,
            'volume': total_volume,
            'service_type': service_type,
            'cargo_items': cargo_items,
            'pickup_address': request.form.get('pickup_address'),
            'place_of_delivery': request.form.get('place_of_delivery')
        }
        return redirect(url_for('customer.rate_results'))"""

replacement_post_logic = """    if request.method == 'POST':
        import requests
        
        service_type = request.form.get('service_type', 'LCL')
        goods_types = request.form.getlist('goods_type[]')
        
        # Build API Payload
        payload = {
            "header": {
                "branchId": 0,
                "customerId": 0,
                "customerContactId": 0,
                "customerReference": request.form.get("customer_reference", ""),
                "trafficType": request.form.get("direction", ""),
                "freightTransportMode": request.form.get("transport_mode", ""),
                "freightTransportType": service_type,
                "movementType": request.form.get("movement_type", ""),
                "cargoClassification": "11" if "HAZARDOUS" in goods_types else "12",
                "incoTerm": request.form.get("freight_terms", ""),
                "incoLocation": "",
                "entryMethod": "PORTAL",
                "paymentMethod": request.form.get("payment_terms", ""),
                "specialInstructions": request.form.get("special_instructions", ""),
                "internalMemo": "",
                "validFrom": request.form.get("cargo_ready_date", ""),
                "validUntil": "",
                "currency": request.form.get("currency", "USD"),
                "cur1": "",
                "cur2": "",
                "roe1": 0,
                "roe2": 0,
                "routing": {
                    "porLocode": "",
                    "porLocation": request.form.get("pickup_address", ""),
                    "polLocode": "",
                    "polLocation": request.form.get("origin", ""),
                    "podLocode": "",
                    "podLocation": request.form.get("destination", ""),
                    "delLocode": "",
                    "delLocation": request.form.get("place_of_delivery", "")
                },
                "vesselVoyageId": 0,
                "pocIdPol": 0,
                "pocIdPod": 0,
                "haulageOriginNeeded": bool(request.form.get("pickup_address")),
                "haulageDestinationNeeded": bool(request.form.get("place_of_delivery"))
            },
            "commodities": [],
            "tariffLines": []
        }

        if service_type == 'LCL':
            item_qtys = request.form.getlist('item_qty[]')
            item_types = request.form.getlist('item_type[]')
            item_weights = request.form.getlist('item_weight[]')
            item_volumes = request.form.getlist('item_volume[]')
            item_descs = request.form.getlist('item_desc[]')
            
            for i in range(len(item_qtys)):
                is_haz = (goods_types[i] == 'HAZARDOUS') if i < len(goods_types) else False
                payload["commodities"].append({
                    "nrPackages": int(item_qtys[i]) if item_qtys[i] else 1,
                    "packageCode": item_types[i] if i < len(item_types) else "",
                    "packageTypeDescription": item_types[i] if i < len(item_types) else "",
                    "commodityDescription": item_descs[i] if i < len(item_descs) else "",
                    "weight": float(item_weights[i]) if i < len(item_weights) and item_weights[i] else 0.0,
                    "volume": float(item_volumes[i]) if i < len(item_volumes) and item_volumes[i] else 0.0,
                    "dimensions": {"amount": 0, "length": 0, "width": 0, "height": 0},
                    "imoDetails": {
                        "hasImo": is_haz,
                        "un": "", "class": "", "properShippingName": "", "packingGroup": ""
                    }
                })
        else:
            cont_types = request.form.getlist('cont_type[]')
            cont_qtys = request.form.getlist('cont_qty[]')
            c_weights = request.form.getlist('cont_weight[]')
            c_volumes = request.form.getlist('cont_volume[]')
            c_descs = request.form.getlist('cont_desc[]')
            
            for i in range(len(cont_types)):
                is_haz = (goods_types[i] == 'HAZARDOUS') if i < len(goods_types) else False
                payload["commodities"].append({
                    "nrPackages": int(cont_qtys[i]) if i < len(cont_qtys) and cont_qtys[i] else 1,
                    "packageCode": cont_types[i] if i < len(cont_types) else "",
                    "packageTypeDescription": cont_types[i] if i < len(cont_types) else "",
                    "commodityDescription": c_descs[i] if i < len(c_descs) else "",
                    "weight": float(c_weights[i]) if i < len(c_weights) and c_weights[i] else 0.0,
                    "volume": float(c_volumes[i]) if i < len(c_volumes) and c_volumes[i] else 0.0,
                    "dimensions": {"amount": 0, "length": 0, "width": 0, "height": 0},
                    "imoDetails": {
                        "hasImo": is_haz,
                        "un": "", "class": "", "properShippingName": "", "packingGroup": ""
                    }
                })

        try:
            headers = {'accept': 'application/json', 'x-api-key': '1', 'Content-Type': 'application/json'}
            api_resp = requests.post('http://realnexus.comit.cloud:5000/api/Quotations', json=payload, headers=headers, timeout=10)
            
            if api_resp.status_code == 201:
                data = api_resp.json()
                quo_id = f"{data.get('quoPrefix1', 'QUO')}-{data.get('quoPrefix2', '2026')}-{data.get('quotationId', '')}"
                flash(f"Success! Quotation {quo_id} has been created.", "success")
                
                # Mock up the rate results session so the redirect works nicely
                session['search_query'] = {
                    'origin': payload['header']['routing']['polLocation'],
                    'destination': payload['header']['routing']['podLocation'],
                    'volume': sum(c['volume'] for c in payload['commodities']),
                    'service_type': service_type,
                    'cargo_items': payload['commodities'],
                    'quote_id': quo_id
                }
                return redirect(url_for('customer.rate_results'))
            else:
                flash(f"Failed to create quotation. API responded with status {api_resp.status_code}.", "danger")
                print("API ERROR:", api_resp.text)
                return redirect(url_for('customer.rates'))
        except Exception as e:
            flash(f"API Error: {str(e)}", "danger")
            return redirect(url_for('customer.rates'))"""

content = content.replace(target_post_logic, replacement_post_logic)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated customer.py with Quotations API POST.")
