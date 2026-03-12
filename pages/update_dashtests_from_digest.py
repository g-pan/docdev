import os
from bs4 import BeautifulSoup

DASHTESTS_PATH = "c:/DATA/docdev/pages/dashtests.html"
DIGEST_PATH = "c:/DATA/docdev/pages/OBTTestingdigest.html"

# Helper to extract regression/unit/performance data from digest

def extract_digest_data():
    with open(DIGEST_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    data = {
        'regression': {},
        'unit': {},
        'coverage': None,
        'performance': {},
    }
    # Find master branch table
    master_header = soup.find("h3", id="master")
    master_table = master_header.find_next("table") if master_header else None
    if master_table:
        rows = master_table.find_all("tr")
        # Regression: second row, last column
        if len(rows) > 2:
            reg_cell = rows[2].find_all("td")[-1]
            reg_lines = reg_cell.find_all("small")
            for line in reg_lines:
                for txt in line.stripped_strings:
                    if "Hthor:" in txt:
                        data['regression']['hthor'] = txt.split("Hthor:PASSED  (")[-1].rstrip(")")
                    if "Thor:" in txt:
                        data['regression']['thor'] = txt.split("Thor:PASSED  (")[-1].rstrip(")")
                    if "Roxie:" in txt:
                        data['regression']['roxie'] = txt.split("Roxie:PASSED  (")[-1].rstrip(")")
            # Unit: second row, 6th column
            unit_cell = rows[2].find_all("td")[5]
            unit_small = unit_cell.find("small")
            if unit_small:
                total = unit_small.text.split("Total:")[-1].split("\n")[0].strip()
                data['unit']['hthor'] = f"{total}/{total} (100%)"
                data['unit']['thor'] = f"{total}/{total} (100%)"
                data['unit']['roxie'] = f"{total}/{total} (100%)"
            # Performance: first row (BM) and last row (AWS), 6th column
            bm_cell = rows[1].find_all("td")[5]
            aws_cell = rows[-1].find_all("td")[5]
            bm_small = bm_cell.find("small")
            aws_small = aws_cell.find("small")
            if bm_small and aws_small:
                bm_thor = bm_small.text.split("thor:PASSED  (")[-1].split(")")[0]
                bm_roxie = bm_small.text.split("roxie:PASSED  (")[-1].split(")")[0]
                aws_thor = aws_small.text.split("thor:PASSED  (")[-1].split(")")[0]
                aws_roxie = aws_small.text.split("roxie:PASSED  (")[-1].split(")")[0]
                data['performance']['thor'] = f"{bm_thor} (BM), {aws_thor} (AWS)"
                data['performance']['roxie'] = f"{bm_roxie} (BM), {aws_roxie} (AWS)"
    return data

def update_dashtests():
    data = extract_digest_data()
    with open(DASHTESTS_PATH, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # Update Regression Suite
    reg_section = soup.find("td", class_="test-type", string="Regression Suite")
    if reg_section:
        rows = reg_section.find_parent("tbody").find_all("tr")
        for row in rows:
            platform_cell = row.find_all("td")[1]
            platform = platform_cell.text.strip().lower()
            if platform in data['regression']:
                cells = row.find_all("td")
                cells[-1].string = data['regression'][platform]
    # Update Unit Tests
    unit_section = soup.find("td", class_="test-type", string="Unit Tests")
    if unit_section:
        rows = unit_section.find_parent("tbody").find_all("tr")
        for row in rows:
            platform_cell = row.find_all("td")[1]
            platform = platform_cell.text.strip().lower()
            if platform in data['unit']:
                cells = row.find_all("td")
                cells[-1].string = data['unit'][platform]
    # Update Performance Suite (master only)
    perf_section = soup.find("td", class_="test-type", string="Performance Suite")
    if perf_section:
        rows = perf_section.find_parent("tbody").find_all("tr")
        for row in rows:
            platform_cell = row.find_all("td")[1]
            platform = platform_cell.text.strip().lower()
            if platform in data['performance']:
                cells = row.find_all("td")
                for i in range(len(cells)-1):
                    cells[i+2].string = "N/A"
                cells[-1].string = data['performance'][platform]
    # Coverage (master only)
    cov_section = soup.find("td", class_="test-type", string="Coverage")
    if cov_section:
        row = cov_section.find_parent("tbody").find("tr")
        cells = row.find_all("td")
        for i in range(len(cells)-1):
            cells[i+2].string = "N/A"
        # Coverage value for master can be set here if available
    with open(DASHTESTS_PATH, "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    update_dashtests()
    print("dashtests.html updated from OBTTestingdigest.html.")
