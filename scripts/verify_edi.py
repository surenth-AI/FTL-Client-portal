import requests
import json

def test_edi_ingest():
    url = "http://127.0.0.1:5000/edi/ingest"
    
    payload = {
        "mbl_number": "MBL12345678",
        "hbl_number": "HBL98765432",
        "vessel_name": "COSCO SHIPPING HAMBURG",
        "voyage_number": "045E",
        "port_of_loading": "Shenzhen",
        "port_of_discharge": "Hamburg",
        "eta_pod": "2026-05-15T14:00:00",
        "shipper_name": "Shenzhen Export Corp",
        "consignee_name": "European Retailers AG",
        "cargo_description": "Electronics and Hardware",
        "weight_kg": 4500.5,
        "volume_cbm": 12.4
    }

    print(f"Sending EDI payload to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_edi_ingest()
