#!/usr/bin/env python3
import re

SUMMARY_PATH = "pages/summary.html"

def extract_data_from_line(line):
    """Extract text content from a <td> line."""
    match = re.search(r'>([^<]+)<', line)
    return match.group(1).strip() if match else ""

with open(SUMMARY_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=" * 70)
print("ACTUAL LINE CONTENT FROM summary.html")
print("=" * 70)

# Show lines around headers
print("\nHEADER AREA (Lines 1-15):")
for i in range(0, 15):
    print(f"Line {i+1:3d}: {lines[i].rstrip()}")

# Show lines around Regression data
print("\nREGRESSION AREA (Lines 12-40):")
for i in range(11, 40):
    data = extract_data_from_line(lines[i])
    print(f"Line {i+1:3d}: {lines[i].rstrip()}")
    if data:
        print(f"         EXTRACTED: '{data}'")

# Show Unit Tests area
print("\nUNIT TESTS AREA (Lines 38-50):")
for i in range(37, 50):
    data = extract_data_from_line(lines[i])
    print(f"Line {i+1:3d}: {lines[i].rstrip()}")
    if data:
        print(f"         EXTRACTED: '{data}'")