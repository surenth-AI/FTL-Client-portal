import os

file_path = r"d:\AXE Global\ntex\Sample csv\TEAM FREIGHT AS 01-03-2026 - 31-03-2026.xlsx"
filename = os.path.basename(file_path)

print(f"Filename: '{filename}'")
print(f"Hex of filename: {filename.encode('utf-8').hex()}")

# Check if 'team freight' is in it
if "team freight" in filename.lower():
    print("Direct match: True")
else:
    print("Direct match: False")

# Check with regex or by normalizing spaces
import re
normalized = re.sub(r'\s+', ' ', filename.lower())
if "team freight" in normalized:
    print("Normalized match: True")
else:
    print("Normalized match: False")
