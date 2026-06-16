import os
import re

filepath = r'd:\FTL-DEV\app\templates\customer\rates.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add fields to Panel 3 (Terms & Services)
# We will insert them right after the Incoterm div.
target_panel3 = """                        <div class="mb-4">
                            <label class="premium-label required">Incoterm</label>
                            <select class="premium-input" id="wizIncoterm" name="freight_terms" required>
                                <option value="">Select incoterm...</option>
                                <option value="EXW">EXW - Ex Works</option>
                                <option value="FCA">FCA - Free Carrier</option>
                                <option value="FAS">FAS - Free Alongside Ship</option>
                                <option value="FOB">FOB - Free On Board</option>
                                <option value="CFR">CFR - Cost and Freight</option>
                                <option value="CIF">CIF - Cost, Insurance and Freight</option>
                                <option value="CPT">CPT - Carriage Paid To</option>
                                <option value="CIP">CIP - Carriage and Insurance Paid To</option>
                                <option value="DAP">DAP - Delivered At Place</option>
                                <option value="DPU">DPU - Delivered at Place Unloaded</option>
                                <option value="DDP">DDP - Delivered Duty Paid</option>
                                <option value="DDU">DDU - Delivered Duty Unpaid</option>
                            </select>
                        </div>"""

replacement_panel3 = """                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label class="premium-label required">Incoterm</label>
                                <select class="premium-input" id="wizIncoterm" name="freight_terms" required>
                                    <option value="">Select incoterm...</option>
                                    <option value="EXW">EXW - Ex Works</option>
                                    <option value="FCA">FCA - Free Carrier</option>
                                    <option value="FAS">FAS - Free Alongside Ship</option>
                                    <option value="FOB">FOB - Free On Board</option>
                                    <option value="CFR">CFR - Cost and Freight</option>
                                    <option value="CIF">CIF - Cost, Insurance and Freight</option>
                                    <option value="CPT">CPT - Carriage Paid To</option>
                                    <option value="CIP">CIP - Carriage and Insurance Paid To</option>
                                    <option value="DAP">DAP - Delivered At Place</option>
                                    <option value="DPU">DPU - Delivered at Place Unloaded</option>
                                    <option value="DDP">DDP - Delivered Duty Paid</option>
                                    <option value="DDU">DDU - Delivered Duty Unpaid</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="premium-label required">Payment Terms</label>
                                <select class="premium-input" name="payment_terms" required>
                                    <option value="">Select payment terms...</option>
                                    <option value="PO">Prepaid (PO)</option>
                                    <option value="CC">Collect (CC)</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="premium-label required">Currency</label>
                                <select class="premium-input" name="currency" required>
                                    <option value="USD">USD - US Dollar</option>
                                    <option value="EUR">EUR - Euro</option>
                                    <option value="GBP">GBP - British Pound</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="premium-label">Customer Reference</label>
                                <input type="text" class="premium-input" name="customer_reference" placeholder="Optional PO or Ref Number">
                            </div>
                            <div class="col-12">
                                <label class="premium-label">Special Instructions</label>
                                <textarea class="premium-input" name="special_instructions" rows="2" placeholder="Any specific requirements or instructions..."></textarea>
                            </div>
                        </div>"""

content = content.replace(target_panel3, replacement_panel3)


# 2. Add Description to FCL row generator
target_fcl_row = """            <div class="row g-2 mb-2">
                <div class="col-6">
                    <label class="premium-label mb-1">Weight (kg)</label>
                    <input type="number" name="cont_weight[]" class="premium-input w-100" placeholder="0.0" step="0.01">
                </div>
                <div class="col-6">
                    <label class="premium-label mb-1">Volume (cbm)</label>
                    <input type="number" name="cont_volume[]" class="premium-input w-100" placeholder="0.00" step="0.01">
                </div>
            </div>"""

replacement_fcl_row = """            <div class="row g-2 mb-2">
                <div class="col-6">
                    <label class="premium-label mb-1">Weight (kg)</label>
                    <input type="number" name="cont_weight[]" class="premium-input w-100" placeholder="0.0" step="0.01">
                </div>
                <div class="col-6">
                    <label class="premium-label mb-1">Volume (cbm)</label>
                    <input type="number" name="cont_volume[]" class="premium-input w-100" placeholder="0.00" step="0.01">
                </div>
            </div>
            
            <div class="mb-2">
                <label class="premium-label mb-1">Description</label>
                <input type="text" name="cont_desc[]" class="premium-input w-100" placeholder="e.g. General Cargo, Electronics...">
            </div>"""

content = content.replace(target_fcl_row, replacement_fcl_row)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added new fields to rates.html")
