#!/usr/bin/env python3
"""
Simple line-by-line update: summary.html -> dashtests.html
Per-line extraction with correct line numbers
"""

import re

def extract_value(line):
    """Extract text content between td tags, handling <br> if present."""
    line = line.replace('<br>', ' ')
    match = re.search(r'>([^<]+)<', line)
    return match.group(1).strip() if match else ""

def get_bullet(value):
    """Determine bullet color from percentage value."""
    match = re.search(r'\((\d+\.\d+)%\)', value)
    if not match:
        return 'bullet-red'
    
    pct = float(match.group(1))
    return 'bullet-green' if pct == 100.0 else 'bullet-yellow' if pct >= 99.0 else 'bullet-red'

def get_bullet_coverage(value):
    """Coverage has different thresholds."""
    match = re.search(r'(\d+\.\d+)%', value)
    if not match:
        return 'bullet-red'
    
    pct = float(match.group(1))
    return 'bullet-green' if pct >= 80.0 else 'bullet-yellow' if pct >= 60.0 else 'bullet-red'

def main():
    # Read summary.html
    with open('pages/summary.html', 'r', encoding='utf-8') as f:
        summary = f.readlines()
    
    # Read dashtests.html
    with open('pages/dashtests.html', 'r', encoding='utf-8') as f:
        dash = f.readlines()
    
    # Extract from summary.html (0-based indexing, so line 17 = index 16)
    
    # REGRESSION - Hthor (lines 17-22, 0-index=16-21)
    hthor = [extract_value(summary[i]) for i in range(16, 22)]
    
    # REGRESSION - Thor (lines 25-30, 0-index=24-29)
    thor = [extract_value(summary[i]) for i in range(24, 30)]
    
    # REGRESSION - Roxie (lines 33-38, 0-index=32-37)
    roxie = [extract_value(summary[i]) for i in range(32, 38)]
    
    # UNIT TESTS (lines 44-49, 0-index=43-48)
    unit = [extract_value(summary[i]) for i in range(43, 49)]
    
    # PERFORMANCE (lines 56, 60, 65, 69, 0-index=55, 59, 64, 68)
    perf_bm_thor = extract_value(summary[55])
    perf_bm_roxie = extract_value(summary[59])
    perf_vm_thor = extract_value(summary[64])
    perf_vm_roxie = extract_value(summary[68])
    
    # COVERAGE - lines (line 80, 0-index=79)
    coverage = extract_value(summary[79])
    
    # Update dashtests.html
    
    # REGRESSION - Hthor (lines 112-117, 0-index=111-116)
    for i, val in enumerate(hthor):
        bullet = get_bullet(val)
        dash[111 + i] = f'<td><span class="{bullet}">●</span> {val}</td>\n'
    
    # REGRESSION - Thor (lines 121-126, 0-index=120-125)
    for i, val in enumerate(thor):
        bullet = get_bullet(val)
        dash[120 + i] = f'<td><span class="{bullet}">●</span> {val}</td>\n'
    
    # REGRESSION - Roxie (lines 130-135, 0-index=129-134)
    for i, val in enumerate(roxie):
        bullet = get_bullet(val)
        dash[129 + i] = f'<td><span class="{bullet}">●</span> {val}</td>\n'
    
    # UNIT TESTS (lines 154-159, 0-index=153-158)
    for i, val in enumerate(unit):
        bullet = get_bullet(val)
        dash[153 + i] = f'<td><span class="{bullet}">●</span> {val}</td>\n'
    
    # PERFORMANCE - BM thor (line 179, 0-index=178)
    dash[178] = f'<td><span class="{get_bullet(perf_bm_thor)}">●</span> {perf_bm_thor}</td>\n'
    
    # PERFORMANCE - BM roxie (line 184, 0-index=183)
    dash[183] = f'<td><span class="{get_bullet(perf_bm_roxie)}">●</span> {perf_bm_roxie}</td>\n'
    
    # PERFORMANCE - VM thor (line 190, 0-index=189)
    dash[189] = f'<td><span class="{get_bullet(perf_vm_thor)}">●</span> {perf_vm_thor}</td>\n'
    
    # PERFORMANCE - VM roxie (line 195, 0-index=194)
    dash[194] = f'<td><span class="{get_bullet(perf_vm_roxie)}">●</span> {perf_vm_roxie}</td>\n'
    
    # COVERAGE (line 218, 0-index=217)
    dash[217] = f'<td><span class="{get_bullet_coverage(coverage)}">●</span> {coverage} lines</td>\n'
    
    # Write output
    with open('pages/dashtests.html', 'w', encoding='utf-8') as f:
        f.writelines(dash)
    
    print("✓ dashtests.html updated successfully")

if __name__ == '__main__':
    main()