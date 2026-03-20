from bs4 import BeautifulSoup
import os

import re
from bs4 import BeautifulSoup
import os

SUMMARY_PATH = "c:/DATA/docdev/pages/summary.html"
DASHTESTS_PATH = "c:/DATA/docdev/pages/dashtests.html"

# Map group/engine to dashtests.html row order
ROW_MAP = {
    'Regression suite': ['Hthor', 'Thor', 'Roxie'],
    'Unit tests': ['Hthor', 'Thor', 'Roxie'],
    'Performance suite': [('BM', 'thor'), ('BM', 'roxie'), ('VM', 'thor'), ('VM', 'roxie')],
}

VERSION_COLS = ["9.10.x", "9.12.x", "9.14.x", "10.0.x", "10.2.x", "master"]


def extract_summary_data():
    with open(SUMMARY_PATH, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")
    data = {}
    i = 1  # skip header
    def get_bullet_and_html(cell, add_bullet=True):
        html = ''.join(str(x) for x in cell.contents)
        text = cell.get_text().strip().lower()
        # Skip bullet if not requested, or if cell is blank, 'n/a', 'no data', or has colspan
        if (
            not add_bullet
            or text == ''
            or text == 'n/a'
            or text == 'no data'
            or cell.has_attr('colspan')
        ):
            return html
        percent = None
        m = re.search(r'(\d{1,3}(?:\.\d+)?)%', cell.get_text())
        if m:
            percent = float(m.group(1))
        if percent is None:
            bullet = '<span class="bullet-red">●</span> '
        elif percent == 100.0:
            bullet = '<span class="bullet-green">●</span> '
        elif percent >= 70.0:
            bullet = '<span class="bullet-yellow">●</span> '
        else:
            bullet = '<span class="bullet-red">●</span> '
        return bullet + html

    while i < len(rows):
        cells = rows[i].find_all("td")
        if not cells:
            i += 1
            continue
        group = cells[0].get_text(strip=True)
        if group == "Regression suite":
            data['Regression suite'] = {}
            for j, engine in enumerate(['Hthor', 'Thor', 'Roxie']):
                row = rows[i + j]
                tds = row.find_all("td")
                # version columns start at index 3
                # For col 9 (index 5 in tds[3:9]), do not add bullet
                data['Regression suite'][engine] = [
                    get_bullet_and_html(td, add_bullet=(col != 5))
                    for col, td in enumerate(tds[3:9])
                ]
            i += 3
        elif group == "Unit tests":
            data['Unit tests'] = {}
            row = rows[i]
            tds = row.find_all("td")
            # skip N/A in engine col, versions start at index 3
            data['Unit tests']['Hthor'] = [get_bullet_and_html(td, add_bullet=(col != 5)) for col, td in enumerate(tds[3:9])]
            data['Unit tests']['Thor'] = [get_bullet_and_html(td, add_bullet=(col != 5)) for col, td in enumerate(tds[3:9])]
            data['Unit tests']['Roxie'] = [get_bullet_and_html(td, add_bullet=(col != 5)) for col, td in enumerate(tds[3:9])]
            i += 1
        elif group == "Performance suite":
            data['Performance suite'] = {}
            for j in range(4):
                row = rows[i + j]
                tds = row.find_all("td")
                env = tds[1].get_text(strip=True)
                engine = tds[2].get_text(strip=True)
                key = (env, engine)
                # version columns start at index 3
                data['Performance suite'][key] = [get_bullet_and_html(td) for td in tds[3:9]]
            i += 4
        else:
            i += 1
    return data

from bs4 import Comment

def find_section_by_comment(soup, comment_text):
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if comment_text in comment:
            return comment.find_next("tbody")
    return None

def update_dashtests(data):
    with open(DASHTESTS_PATH, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # REGRESSION
    reg_section = find_section_by_comment(soup, "REGRESSION")
    reg_rows = reg_section.find_all("tr") if reg_section else []
    for idx, engine in enumerate(['Hthor', 'Thor', 'Roxie']):
        if idx < len(reg_rows):
            tds = reg_rows[idx].find_all("td")
            for col, val in enumerate(data['Regression suite'][engine]):
                tds[col + 3].clear()
                tds[col + 3].append(BeautifulSoup(val, "html.parser"))
    # UNIT
    unit_section = find_section_by_comment(soup, "UNIT TESTS")
    unit_rows = unit_section.find_all("tr") if unit_section else []
    # Always update all three engines if possible
    for idx, engine in enumerate(['Hthor', 'Thor', 'Roxie']):
        if idx < len(unit_rows):
            tds = unit_rows[idx].find_all("td")
            for col, val in enumerate(data['Unit tests'][engine]):
                tds[col + 3].clear()
                tds[col + 3].append(BeautifulSoup(val, "html.parser"))
    # PERFORMANCE
    perf_section = find_section_by_comment(soup, "PERFORMANCE")
    perf_rows = perf_section.find_all("tr") if perf_section else []
    perf_keys = [('BM', 'thor'), ('BM', 'roxie'), ('VM', 'thor'), ('VM', 'roxie')]
    for idx, key in enumerate(perf_keys):
        if key in data['Performance suite']:
            tds = perf_rows[idx].find_all("td")
            for col, val in enumerate(data['Performance suite'][key]):
                tds[col + 3].clear()
                tds[col + 3].append(BeautifulSoup(val, "html.parser"))
    # Write back
    with open(DASHTESTS_PATH, "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    data = extract_summary_data()
    update_dashtests(data)
