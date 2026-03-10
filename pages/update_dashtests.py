from bs4 import BeautifulSoup

# File paths
regress_path = "c:/DATA/docdev/pages/regress_quick.html"
dashtests_path = "c:/DATA/docdev/pages/dashtests.html"
version_col = "10.2.x"  # Set your target version column

# Extract summary from regress_quick.html
def get_regress_summary():
    with open(regress_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    summary = {}
    for suite in ["hthor", "thor", "roxie-workunit"]:
        div = soup.find("h2", string=lambda s: s and suite in s)
        if div:
            summary_div = div.find_next("div", class_="summary")
            if summary_div:
                passing = summary_div.find("p", string=lambda s: "Passing" in s)
                failure = summary_div.find("p", string=lambda s: "Failure" in s)
                if passing and failure:
                    p = int(passing.text.split(":")[1].strip())
                    f = int(failure.text.split(":")[1].strip())
                    total = p + f
                    percent = round(100 * p / total, 1) if total else 0
                    # Determine bullet color
                    if total == 0:
                        bullet = "bullet-red"
                    elif p == total:
                        bullet = "bullet-green"
                    elif p >= 0.7 * total:
                        bullet = "bullet-yellow"
                    else:
                        bullet = "bullet-red"
                    summary[suite] = {
                        "result": f'{p}/{total} ({percent}%)',
                        "bullet": bullet
                    }
                else:
                    summary[suite] = "--"
            else:
                summary[suite] = "--"
        else:
            summary[suite] = "--"
    return summary

# Update dashtests.html BVT section
def update_dashtests(summary):
    with open(dashtests_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # Find BVT section
    bvt_section = soup.find("td", class_="test-type", string="BVT")
    if not bvt_section:
        print("BVT section not found.")
        return
    # Find all rows in BVT section
    bvt_rows = bvt_section.find_parent("tbody").find_all("tr")
    for platform, suite in [("hthor", "hthor"), ("Thor", "thor"), ("Roxie", "roxie-workunit")]:
        for row in bvt_rows:
            platform_cell = row.find_all("td")[1] if len(row.find_all("td")) > 1 else None
            if platform_cell and platform_cell.text.strip().lower() == platform.lower():
                cells = row.find_all("td")
                header_row = soup.find("table").find("tr")
                headers = [th.text.strip() for th in header_row.find_all("th")]
                try:
                    col_idx = headers.index(version_col)
                except ValueError:
                    print(f"Version column '{version_col}' not found.")
                    continue
                cells[col_idx].clear()
                if summary[suite] == "--" or not summary[suite]:
                    cells[col_idx].string = "--"
                else:
                    bullet_html = f'<span class="{summary[suite]["bullet"]}">&#9679;</span> '
                    result_html = summary[suite]["result"]
                    cells[col_idx].append(BeautifulSoup(bullet_html + result_html, "html.parser"))
                break
    # Save updated file
    with open(dashtests_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    summary = get_regress_summary()
    update_dashtests(summary)
    print("dashtests.html updated with latest regress_quick summary.")
