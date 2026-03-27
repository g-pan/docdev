#!/usr/bin/env python3
"""
Update dashtests.html with data from summary.html using line-based parsing.
Uses EXACT line numbers as documented in the summary.html structure.
"""

import re
import sys
from bs4 import BeautifulSoup

# Relative paths within the pages directory
SUMMARY_PATH = "pages/summary.html"
DASHTESTS_PATH = "pages/dashtests.html"

def extract_data_from_line(line):
    """Extract text content from a <td> line."""
    match = re.search(r'>[^<]+<', line)
    return match.group(1).strip() if match else ""

def get_percent(text):
    """Extract percentage value from text like '1036/1036 (100.0%)'."""
    match = re.search(r'\((\d{1,3}(?:\.\d+)?)%\)', text)
    if not match:
        # Try without parentheses for coverage data like "41.5%"
        match = re.search(r'(\d{1,3}(?:\.\d+)?)%', text)
    return float(match.group(1)) if match else None

def get_bullet_color_standard(percent):
    """Get bullet color for standard tests: green if 100%, yellow otherwise."""
    if percent is None:
        return "bullet-red"
    return "bullet-green" if percent == 100.0 else "bullet-yellow"

def get_bullet_color_coverage(percent):
    """Get bullet color for coverage: green ≥80%, yellow 60-79%, red <60%."""
    if percent is None:
        return "bullet-red"
    if percent >= 80.0:
        return "bullet-green"
    elif percent >= 60.0:
        return "bullet-yellow"
    else:
        return "bullet-red"

def update_cell_with_bullet(dash_soup, cell, text, bullet_color):
    """Update a cell with colored bullet and text, preserving structure."""
    bullet_span = cell.find("span")
    
    if bullet_span:
        # Update existing bullet color
        bullet_span["class"] = [bullet_color]
        # Update text after bullet
        if bullet_span.next_sibling:
            bullet_span.next_sibling.replace_with(" " + text)
        else:
            bullet_span.insert_after(" " + text)
    else:
        # Create new bullet and text
        cell.clear()
        new_span = dash_soup.new_tag("span", **{"class": bullet_color})
        new_span.string = "●"
        cell.append(new_span)
        cell.append(" " + text)

def main():
    print("Starting dashboard update...")
    
    # Read summary.html as lines
    try:
        with open(SUMMARY_PATH, 'r', encoding='utf-8') as f:
            summary_lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: {SUMMARY_PATH} not found!")
        sys.exit(1)
    
    print(f"Loaded {len(summary_lines)} lines from summary.html")
    
    # Load dashtests.html with BeautifulSoup
    try:
        with open(DASHTESTS_PATH, 'r', encoding='utf-8') as f:
            dash_soup = BeautifulSoup(f, 'html.parser')
    except FileNotFoundError:
        print(f"ERROR: {DASHTESTS_PATH} not found!")
        sys.exit(1)
    
    # Get the table and tbody sections from dashtests
    dash_table = dash_soup.find("table", class_="test-table")
    if not dash_table:
        print("ERROR: Could not find table with class 'test-table' persona")
        sys.exit(1)
    
    dash_tbodies = dash_table.find_all("tbody")
    print(f"Found {len(dash_tbodies)} tbody sections in dashtests.html")
    
    # === REGRESSION SUITE (Lines 13-39: Hthor 15-23, Thor 24-31, Roxie 32-39) ===
    print("\nUpdating Regression Suite...")
    dash_reg_tbody = dash_tbodies[0]
    dash_reg_rows = dash_reg_tbody.find_all("tr")
    
    # Hthor: Lines 16-21 (data cells with version results)
    print("  Processing Hthor...")
    hthor_data_lines = [16, 17, 18, 19, 20, 21]
    hthor_data = [extract_data_from_line(summary_lines[i-1]) for i in hthor_data_lines]
    print(f"    Hthor data: {hthor_data}")
    
    dash_hthor_cells = dash_reg_rows[0].find_all("td")
    for idx, data in enumerate(hthor_data):
        if data:
            percent = get_percent(data)
            bullet_color = get_bullet_color_standard(percent)
            update_cell_with_bullet(dash_soup, dash_hthor_cells[idx+3], data, bullet_color)
    
    # Thor: Lines 25-30
    print("  Processing Thor...")
    thor_data_lines = [25, 26, 27, 28, 29, 30]
    thor_data = [extract_data_from_line(summary_lines[i-1]) for i in thor_data_lines]
    print(f"    Thor data: {thor_data}")
    
    dash_thor_cells = dash_reg_rows[1].find_all("td")
    for idx, data in enumerate(thor_data):
        if data:
            percent = get_percent(data)
            bullet_color = get_bullet_color_standard(percent)
            update_cell_with_bullet(dash_soup, dash_thor_cells[idx+1], data, bullet_color)
    
    # Roxie: Lines 33-38
    print("  Processing Roxie...")
    roxie_data_lines = [33, 34, 35, 36, 37, 38]
    roxie_data = [extract_data_from_line(summary_lines[i-1]) for i in roxie_data_lines]
    print(f"    Roxie data: {roxie_data}")
    
    dash_roxie_cells = dash_reg_rows[2].find_all("td")
    for idx, data in enumerate(roxie_data):
        if data:
            percent = get_percent(data)
            bullet_color = get_bullet_color_standard(percent)
            update_cell_with_bullet(dash_soup, dash_roxie_cells[idx+1], data, bullet_color)
    
    # === UNIT TESTS (Lines 40-50) ===
    print("\nUpdating Unit Tests...")
    dash_unit_tbody = dash_tbodies[1]
    dash_unit_row = dash_unit_tbody.find("tr")
    dash_unit_cells = dash_unit_row.find_all("td")
    
    unit_data_lines = [44, 45, 46, 47, 48, 49]
    unit_data = [extract_data_from_line(summary_lines[i-1]) for i in unit_data_lines]
    print(f"  Unit test data: {unit_data}")
    
    for idx, data in enumerate(unit_data):
        if data:
            percent = get_percent(data)
            bullet_color = get_bullet_color_standard(percent)
            update_cell_with_bullet(dash_soup, dash_unit_cells[idx+3], data, bullet_color)
    
    # === PERFORMANCE SUITE (Lines 51-70, only master column) ===
    print("\nUpdating Performance Suite...")
    dash_perf_tbody = dash_tbodies[2]
    dash_perf_rows = dash_perf_tbody.find_all("tr")
    
    # BM-thor: Line 56
    perf_bm_thor = extract_data_from_line(summary_lines[55])
    print(f"  BM-thor: {perf_bm_thor}")
    dash_perf_cells_0 = dash_perf_rows[0].find_all("td")
    percent = get_percent(perf_bm_thor)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_0[-1], perf_bm_thor, bullet_color)
    
    # BM-roxie: Line 60
    perf_bm_roxie = extract_data_from_line(summary_lines[59])
    print(f"  BM-roxie: {perf_bm_roxie}")
    dash_perf_cells_1 = dash_perf_rows[1].find_all("td")
    percent = get_percent(perf_bm_roxie)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_1[-1], perf_bm_roxie, bullet_color)
    
    # VM-thor: Line 65
    perf_vm_thor = extract_data_from_line(summary_lines[64])
    print(f"  VM-thor: {perf_vm_thor}")
    dash_perf_cells_2 = dash_perf_rows[2].find_all("td")
    percent = get_percent(perf_vm_thor)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_2[-1], perf_vm_thor, bullet_color)
    
    # VM-roxie: Line 69
    perf_vm_roxie = extract_data_from_line(summary_lines[68])
    print(f"  VM-roxie: {perf_vm_roxie}")
    dash_perf_cells_3 = dash_perf_rows[3].find_all("td")
    percent = get_percent(perf_vm_roxie)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_3[-1], perf_vm_roxie, bullet_color)
    
    # === CODE COVERAGE (Lines 71-89, lines of interest: 76 and 80) ===
    print("\nUpdating Code Coverage...")
    dash_cov_tbody = dash_tbodies[3]
    dash_cov_row = dash_cov_tbody.find("tr")
    dash_cov_cells = dash_cov_row.find_all("td")
    cov_cell = dash_cov_cells[-1]
    
    # Line 76 and Line 80
    lines_percent = extract_data_from_line(summary_lines[75])
    functions_percent = extract_data_from_line(summary_lines[79])
    print(f"  Lines %: {lines_percent}")
    print(f"  Functions %: {functions_percent}")
    
    # Bullet color based on lines %
    lines_val = get_percent(lines_percent)
    bullet_color = get_bullet_color_coverage(lines_val if lines_val else 0)
    
    # Update cell
    cov_cell.clear()
    bullet_span = dash_soup.new_tag("span", **{"class": bullet_color})
    bullet_span.string = "●"
    cov_cell.append(bullet_span)
    cov_cell.append(" ")
    
    # Add text with <br> tag
    lines_tag = dash_soup.new_string(f"{lines_percent} lines")
    cov_cell.append(lines_tag)
    br_tag = dash_soup.new_tag("br")
    cov_cell.append(br_tag)
    functions_tag = dash_soup.new_string(f"{functions_percent} functions")
    cov_cell.append(functions_tag)
    
    # Write back to dashtests.html
    with open(DASHTESTS_PATH, 'w', encoding='utf-8') as f:
        f.write(str(dash_soup))
    
    print("\nDashboard update completed successfully!")

if __name__ == "__main__":
    main()