import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import io
from pypdf import PdfReader

load_dotenv()

class AiExtractor:
    @staticmethod
    def extract_edi_data(file_bytes, filename):
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"success": False, "message": "Gemini API key not found in .env"}
        
        # Handle PDF vs Text
        if filename.lower().endswith('.pdf'):
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                file_content = ""
                for page in reader.pages:
                    file_content += page.extract_text() + "\n"
            except Exception as e:
                return {"success": False, "message": f"PDF extraction failed: {str(e)}"}
        else:
            file_content = file_bytes.decode('utf-8', errors='ignore')
        
        genai.configure(api_key=api_key)
        
        # Using Gemini 1.5 Flash as it is highly efficient for data extraction
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a logistics data extraction expert. 
        Extract shipment information from the following file content (Filename: {filename}).
        
        The output MUST be a valid JSON object with the following fields:
        - mbl_number (string)
        - hbl_number (string)
        - vessel_name (string)
        - voyage_number (string)
        - port_of_loading (string)
        - port_of_discharge (string)
        - consignee_name (string)
        - total_packages (integer)
        - package_type (string)
        - gross_weight (float)
        - volume_cbm (float)
        - items (list of objects with: description, quantity, weight, volume, hs_code)
        
        If a field is not found, use null or empty string.
        Do not include any conversational text, only the JSON.
        
        FILE CONTENT:
        {file_content[:15000]} # Limit content size for safety
        """
        
        try:
            response = model.generate_content(prompt)
            # Extract JSON from response (handling potential markdown blocks)
            text = response.text
            print(f"AI RAW RESPONSE FOR {filename}: {text[:200]}...") # Debug log
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                 text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text.strip())
            return {"success": True, "data": data}
        except Exception as e:
            print(f"AI ERROR: {str(e)}") # Debug log
            return {"success": False, "message": f"AI Extraction failed: {str(e)}"}
