#!/usr/bin/env python3
"""
Update dashtests.html with data from summary.html using line-based parsing.
This script extracts test results from the OBT summary.html file and updates
the corresponding cells in dashtests.html with colored bullets based on pass rates.
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

def validate_headers(summary_lines, dash_soup):
    """Validate that headers match between summary and dashtests."""
    # Expected headers
    expected = ["Test Type", "Environment", "Engine", "9.10.x", "9.12.x", 
                "9.14.x", "10.0.x", "10.2.x", "master"]
    
    # Extract summary headers from lines 3-11
    summary_headers = []
    for i in range(2, 11):  # Lines 3-11 (0-indexed: 2-10)
        header = extract_data_from_line(summary_lines[i])
        if header:
            summary_headers.append(header)
    
    # Extract dashtests headers
    dash_table = dash_soup.find("table", class_="test-table")
    dash_header_row = dash_table.find("tr")
    dash_headers = [th.get_text(strip=True) for th in dash_header_row.find_all("th")]
    
    # Compare
    if summary_headers != expected or dash_headers != expected:
        print("ERROR: Header mismatch detected!")
        print(f"Expected: {expected}")
        print(f"Summary headers: {summary_headers}")
        print(f"Dashtests headers: {dash_headers}")
        return False
    
    return True

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
    
    # Load dashtests.html with BeautifulSoup
    try:
        with open(DASHTESTS_PATH, 'r', encoding='utf-8') as f:
            dash_soup = BeautifulSoup(f, 'html.parser')
    except FileNotFoundError:
        print(f"ERROR: {DASHTESTS_PATH} not found!")
        sys.exit(1)
    
    # Validate headers
    if not validate_headers(summary_lines, dash_soup):
        sys.exit(1)
    
    print("Headers validated successfully.")
    
    # Get the table and tbody sections from dashtests
    dash_table = dash_soup.find("table", class_="test-table")
    dash_tbodies = dash_table.find_all("tbody")
    
    # === REGRESSION SUITE (3 rows: Hthor, Thor, Roxie) ===
    print("Updating Regression Suite...")
    dash_reg_tbody = dash_tbodies[0]
    dash_reg_rows = dash_reg_tbody.find_all("tr")
    
    # Hthor: lines 16-21 (0-indexed: 15-20)
    hthor_data = [extract_data_from_line(summary_lines[i]) for i in range(15, 21)]
    dash_hthor_cells = dash_reg_rows[0].find_all("td")
    for idx, data in enumerate(hthor_data):
        percent = get_percent(data)
        bullet_color = get_bullet_color_standard(percent)
        update_cell_with_bullet(dash_soup, dash_hthor_cells[idx+3], data, bullet_color)
    
    # Thor: lines 24-29 (0-indexed: 23-28)
    thor_data = [extract_data_from_line(summary_lines[i]) for i in range(23, 29)]
    dash_thor_cells = dash_reg_rows[1].find_all("td")
    for idx, data in enumerate(thor_data):
        percent = get_percent(data)
        bullet_color = get_bullet_color_standard(percent)
        update_cell_with_bullet(dash_soup, dash_thor_cells[idx+1], data, bullet_color)
    
    # Roxie: lines 32-37 (0-indexed: 31-36)
    roxie_data = [extract_data_from_line(summary_lines[i]) for i in range(31, 37)]
    dash_roxie_cells = dash_reg_rows[2].find_all("td")
    for idx, data in enumerate(roxie_data):
        percent = get_percent(data)
        bullet_color = get_bullet_color_standard(percent)
        update_cell_with_bullet(dash_soup, dash_roxie_cells[idx+1], data, bullet_color)
    
    # === UNIT TESTS (1 row) ===
    print("Updating Unit Tests...")
    dash_unit_tbody = dash_tbodies[1]
    dash_unit_row = dash_unit_tbody.find("tr")
    dash_unit_cells = dash_unit_row.find_all("td")
    
    # Lines 43-48 (0-indexed: 42-47)
    unit_data = [extract_data_from_line(summary_lines[i]) for i in range(42, 48)]
    for idx, data in enumerate(unit_data):
        percent = get_percent(data)
        bullet_color = get_bullet_color_standard(percent)
        update_cell_with_bullet(dash_soup, dash_unit_cells[idx+3], data, bullet_color)
    
    # === PERFORMANCE SUITE (4 rows, only master column) ===
    print("Updating Performance Suite...")
    dash_perf_tbody = dash_tbodies[2]
    dash_perf_rows = dash_perf_tbody.find_all("tr")
    
    # BM-thor: line 55 (0-indexed: 54)
    perf_bm_thor = extract_data_from_line(summary_lines[54])
    dash_perf_cells_0 = dash_perf_rows[0].find_all("td")
    percent = get_percent(perf_bm_thor)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_0[-1], perf_bm_thor, bullet_color)
    
    # BM-roxie: line 59 (0-indexed: 58)
    perf_bm_roxie = extract_data_from_line(summary_lines[58])
    dash_perf_cells_1 = dash_perf_rows[1].find_all("td")
    percent = get_percent(perf_bm_roxie)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_1[-1], perf_bm_roxie, bullet_color)
    
    # VM-thor: line 64 (0-indexed: 63)
    perf_vm_thor = extract_data_from_line(summary_lines[63])
    dash_perf_cells_2 = dash_perf_rows[2].find_all("td")
    percent = get_percent(perf_vm_thor)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_cells_2[-1], perf_vm_thor, bullet_color)
    
    # VM-roxie: line 68 (0-indexed: 67)
    perf_vm_roxie = extract_data_from_line(summary_lines[67])
    dash_perf_rows_3 = dash_perf_rows[3].find_all("td")
    percent = get_percent(perf_vm_roxie)
    bullet_color = get_bullet_color_standard(percent)
    update_cell_with_bullet(dash_soup, dash_perf_rows_3[-1], perf_vm_roxie, bullet_color)
    
    # === CODE COVERAGE (1 cell, master column only) ===
    print("Updating Code Coverage...")
    dash_cov_tbody = dash_tbodies[3]
    dash_cov_row = dash_cov_tbody.find("tr")
    dash_cov_cells = dash_cov_row.find_all("td")
    cov_cell = dash_cov_cells[-1]
    
    # Lines % from line 79 (0-indexed: 78)
    lines_percent = extract_data_from_line(summary_lines[78])
    
    # Functions % from line 83 (0-indexed: 82)
    functions_percent = extract_data_from_line(summary_lines[82])
    
    # Format: "41.5% lines<br>32.8% functions"
    cov_text = f"{lines_percent} lines<br/>{functions_percent} functions"
    
    # Bullet color based on lines %
    lines_val = get_percent(lines_percent + ")")  # Add ) to match regex
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
    
    print("Dashboard update completed successfully!")

if __name__ == "__main__":
    main()