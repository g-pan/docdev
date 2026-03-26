import re
from bs4 import BeautifulSoup

SUMMARY_PATH = "c:/DATA/docdev/pages/summary.html"
DASHTESTS_PATH = "c:/DATA/docdev/pages/dashtests.html"

def get_percent(text):
    m = re.search(r"\((\d{1,3}(?:\.\d+)?)%\)", text)
    return float(m.group(1)) if m else None

def get_bullet_color(percent, green_val=100.0, yellow_val=100.0):
    if percent is None:
        return "bullet-red"
    if percent == green_val:
        return "bullet-green"
    elif percent < yellow_val:
        return "bullet-yellow"
    else:
        return "bullet-green"

def find_row_by_label(rows, label, col_idx=0):
    for row in rows:
        tds = row.find_all(['td', 'th'])
        if tds and label.lower() in tds[col_idx].get_text(strip=True).lower():
            return row
    return None

def main():
    # Load summary.html
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        summary_soup = BeautifulSoup(f, "html.parser")
    summary_table = summary_soup.find("table")
    summary_rows = summary_table.find_all("tr")

    # Load dashtests.html
    with open(DASHTESTS_PATH, encoding="utf-8") as f:
        dash_soup = BeautifulSoup(f, "html.parser")
    dash_table = dash_soup.find("table")
    dash_rows = dash_table.find_all("tr")
    summary_headers = [th.get_text(strip=True) for th in summary_rows[0].find_all("th")]
    dash_headers = [th.get_text(strip=True) for th in dash_rows[0].find_all("th")]

    # --- COVERAGE GROUP UPDATE (LINE-BASED FALLBACK) ---
    # Read summary.html as plain text and extract coverage values by line number
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        summary_lines = f.readlines()
    perf_idx = None
    for i, line in enumerate(summary_lines):
        if 'Performance suite' in line:
            perf_idx = i
    cov_val = ''
    lines_val = ''
    if perf_idx is not None:
        # Find the next <tr> after last performance row (should be Code coverage)
        for j in range(perf_idx+1, len(summary_lines)):
            if '<tr' in summary_lines[j]:
                # Now skip 4 <td> lines to get to the 5th <td> (coverage value)
                td_count = 0
                for k in range(j+1, len(summary_lines)):
                    if '<td' in summary_lines[k]:
                        td_count += 1
                        if td_count == 5:
                            cov_val = summary_lines[k].split('>')[-1].split('<')[0].strip()
                            break
                # Now, after the next </tr>, find the next <td> line (lines value)
                tr_found = False
                for m in range(k, len(summary_lines)):
                    if '</tr>' in summary_lines[m]:
                        tr_found = True
                    elif tr_found and '<td' in summary_lines[m]:
                        # Skip 2 <td> lines to get to the 3rd <td> (lines value)
                        td2_count = 1
                        for n in range(m+1, len(summary_lines)):
                            if '<td' in summary_lines[n]:
                                td2_count += 1
                                if td2_count == 3:
                                    lines_val = summary_lines[n].split('>')[-1].split('<')[0].strip()
                                    break
                        break
                break
    # If both values found, update the Coverage cell
    if cov_val and lines_val:
        print(f"[DEBUG] Extracted cov_val: '{cov_val}', lines_val: '{lines_val}'")
        dash_cov_tbody = dash_table.find_all("tbody")[3]
        dash_cov_row = dash_cov_tbody.find_all("tr")[0]
        dash_cov_tds = dash_cov_row.find_all("td")
        cov_cell = dash_cov_tds[-1]
        cov_cell.clear()
        cov_cell.append(f"{cov_val} lines<br>{lines_val} functions")
    # Load summary.html
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        summary_soup = BeautifulSoup(f, "html.parser")
    summary_table = summary_soup.find("table")
    summary_rows = summary_table.find_all("tr")

    # Load dashtests.html
    with open(DASHTESTS_PATH, encoding="utf-8") as f:
        dash_soup = BeautifulSoup(f, "html.parser")
    dash_table = dash_soup.find("table")
    dash_rows = dash_table.find_all("tr")
    summary_headers = [th.get_text(strip=True) for th in summary_rows[0].find_all("th")]
    dash_headers = [th.get_text(strip=True) for th in dash_rows[0].find_all("th")]

    # --- UNIT TESTS GROUP UPDATE ---
    dash_unit_tbody = dash_table.find_all("tbody")[1]
    dash_unit_row = dash_unit_tbody.find_all("tr")[0]
    dash_unit_tds = dash_unit_row.find_all("td")
    summary_unit_row = None
    for row in summary_rows:
        tds = row.find_all("td")
        if tds and 'unit tests' in tds[0].get_text(strip=True).lower():
            summary_unit_row = row
            break
    if summary_unit_row:
        sum_tds = summary_unit_row.find_all("td")
        for col_idx, col_name in enumerate(summary_headers[3:]):
            dash_cell = dash_unit_tds[col_idx+3]
            sum_cell = sum_tds[col_idx+3] if len(sum_tds) > col_idx+3 else None
            if not sum_cell:
                continue
            text = sum_cell.get_text(" ", strip=True)
            percent = get_percent(text)
            bullet_span = dash_cell.find("span")
            bullet_class = get_bullet_color(percent)
            if not bullet_span:
                dash_cell.clear()
                new_span = dash_soup.new_tag("span", **{"class": bullet_class})
                new_span.string = "●"
                dash_cell.append(new_span)
                dash_cell.append(" " + text)
            else:
                bullet_span["class"] = [bullet_class]
                if bullet_span.next_sibling:
                    bullet_span.next_sibling.replace_with(" " + text)
                else:
                    bullet_span.insert_after(" " + text)

    # --- REGRESSION GROUP UPDATE ---
    dash_reg_tbody = dash_table.find_all("tbody")[0]
    dash_reg_rows = dash_reg_tbody.find_all("tr")
    summary_reg_rows = []
    for row in summary_rows[1:4]:
        tds = row.find_all("td")
        if tds:
            summary_reg_rows.append(row)
    for dash_row in dash_reg_rows:
        dash_tds = dash_row.find_all("td")
        if len(dash_tds) < 9:
            continue
        dash_engine = dash_tds[2].get_text(strip=True).lower()
        sum_row = None
        for srow in summary_reg_rows:
            stds = srow.find_all("td")
            if len(stds) >= 3 and stds[2].get_text(strip=True).lower() == dash_engine:
                sum_row = srow
                break
        if not sum_row:
            continue
        sum_tds = sum_row.find_all("td")
        for col_idx, col_name in enumerate(summary_headers[3:]):
            dash_cell = dash_tds[col_idx+3]
            sum_cell = sum_tds[col_idx+3] if len(sum_tds) > col_idx+3 else None
            if not sum_cell:
                continue
            text = sum_cell.get_text(" ", strip=True)
            percent = get_percent(text)
            bullet_span = dash_cell.find("span")
            bullet_class = get_bullet_color(percent)
            if not bullet_span:
                dash_cell.clear()
                new_span = dash_soup.new_tag("span", **{"class": bullet_class})
                new_span.string = "●"
                dash_cell.append(new_span)
                dash_cell.append(" " + text)
            else:
                bullet_span["class"] = [bullet_class]
                if bullet_span.next_sibling:
                    bullet_span.next_sibling.replace_with(" " + text)
                else:
                    bullet_span.insert_after(" " + text)

    # --- COVERAGE GROUP UPDATE (SIMPLIFIED) ---
    dash_cov_tbody = dash_table.find_all("tbody")[3]
    dash_cov_row = dash_cov_tbody.find_all("tr")[0]
    dash_cov_tds = dash_cov_row.find_all("td")
    cov_cell = dash_cov_tds[-1]

    # Find the Code coverage row in summary (by label, after last PERFORMANCE row)
    perf_end_idx = None
    for idx, row in enumerate(summary_rows):
        tds = row.find_all("td")
        if tds and 'Performance suite' in tds[0].get_text(strip=True):
            perf_end_idx = idx
    cov_row = None
    lines_row = None
    functions_row = None
    if perf_end_idx is not None:
        print(f"[DEBUG] perf_end_idx: {perf_end_idx}")
        # Search for 'Code coverage' row after last performance row
        for idx in range(perf_end_idx+1, len(summary_rows)):
            tds = summary_rows[idx].find_all("td")
            if tds:
                print(f"[DEBUG] Row {idx} first td: {tds[0].get_text(strip=True)}")
            if tds and 'code coverage' in tds[0].get_text(strip=True).lower():
                cov_row = summary_rows[idx]
                print(f"[DEBUG] Found Code coverage row at {idx}")
                # The next row with 'lines' in the first td is the 'lines' row
                for j in range(idx+1, len(summary_rows)):
                    tds2 = summary_rows[j].find_all("td")
                    print(f"[DEBUG] Candidate row {j} HTML: {str(summary_rows[j])}")
                    if tds2:
                        print(f"[DEBUG] Candidate row {j} first td: '{tds2[0].get_text(strip=True)}'")
                    if tds2 and 'lines' in tds2[0].get_text(strip=True).lower():
                        lines_row = summary_rows[j]
                        print(f"[DEBUG] Found lines row at {j}")
                    if tds2 and 'functions' in tds2[0].get_text(strip=True).lower():
                        functions_row = summary_rows[j]
                        print(f"[DEBUG] Found functions row at {j}")
                    if lines_row and functions_row:
                        break
                break
    if lines_row and functions_row:
        lines_tds = lines_row.find_all("td")
        functions_tds = functions_row.find_all("td")
        print("[DEBUG] lines_tds:", [td.get_text(strip=True) for td in lines_tds])
        print("[DEBUG] functions_tds:", [td.get_text(strip=True) for td in functions_tds])
        lines_val = lines_tds[-1].get_text(strip=True) if len(lines_tds) > 0 else ""
        functions_val = functions_tds[-1].get_text(strip=True) if len(functions_tds) > 0 else ""
        print(f"[DEBUG] Using lines_val: {lines_val}, functions_val: {functions_val}")
        cov_cell.clear()
        cov_cell.append(f"{lines_val} lines<br>{functions_val} functions")

    # Write back
    with open(DASHTESTS_PATH, "w", encoding="utf-8") as f:
        f.write(str(dash_soup))

if __name__ == "__main__":
    main()
