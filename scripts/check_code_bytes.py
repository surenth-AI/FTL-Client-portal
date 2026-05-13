with open(r"d:\AXE Global\ntex\app\services\excel_importer.py", "rb") as f:
    content = f.read()

# Find the line with "team freight"
line_num = 0
for line in content.splitlines():
    line_num += 1
    if b"team freight" in line:
        print(f"Line {line_num}: {line}")
        print(f"Hex: {line.hex()}")
