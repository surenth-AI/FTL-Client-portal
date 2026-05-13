import os
import sys
import json
import subprocess
from flask import Blueprint, render_template, request, flash, current_app

tracking_bp = Blueprint('tracking', __name__, url_prefix='/tracking')

@tracking_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        container_no = request.form.get('container_no', '').strip().upper()
        if not container_no:
            flash("Please enter a valid container number or reference.", "error")
            return render_template('tracking/index.html')
            
        # FOR DEMO PURPOSES: We return a high-fidelity mock journey for any input
        # This ensures the user always sees a 'wowed' result as requested.
        mock_data = {
            "container_info": {
                "container_no": container_no,
                "type": "40' High Cube",
                "status": "In Transit",
                "last_location": "Singapore Transshipment Hub",
                "vessel": "AXEGLOBAL PIONEER V.042"
            },
            "journey_milestones": [
                {
                    "date": "2026-04-10 08:30",
                    "location": "Port of Shanghai, China",
                    "activity": "Gate-in at Terminal",
                    "status": "Completed"
                },
                {
                    "date": "2026-04-12 14:15",
                    "location": "Port of Shanghai, China",
                    "activity": "Loaded on Vessel AXEGLOBAL PIONEER",
                    "status": "Completed"
                },
                {
                    "date": "2026-04-18 22:00",
                    "location": "Singapore Transshipment Hub",
                    "activity": "Discharged from Vessel",
                    "status": "Completed"
                },
                {
                    "date": "2026-04-20 10:45",
                    "location": "Singapore Transshipment Hub",
                    "activity": "In Transit - Pending Onward Connection",
                    "status": "Active"
                },
                {
                    "date": "2026-04-28 (Est)",
                    "location": "Port of Rotterdam, Netherlands",
                    "activity": "Expected Arrival at Port",
                    "status": "Pending"
                }
            ]
        }
        
        return render_template('tracking/results.html', parsed_data=mock_data, container_no=container_no)
            
    return render_template('tracking/index.html')
