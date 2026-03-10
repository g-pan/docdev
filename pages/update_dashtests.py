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
                    summary[suite] = f"{p}/{total} ({percent}%)"
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
    for platform, suite in [("hthor", "hthor"), ("Thor", "thor"), ("Roxie", "roxie-workunit")]:
        row = bvt_section.find_parent("tr").find_next_sibling("tr") if platform != "hthor" else bvt_section.find_parent("tr")
        if row:
            cells = row.find_all("td")
            # Find the correct column index for version_col
            header_row = soup.find("table").find("tr")
            headers = [th.text.strip() for th in header_row.find_all("th")]
            try:
                col_idx = headers.index(version_col)
            except ValueError:
                print(f"Version column '{version_col}' not found.")
                continue
            # Update cell
            cells[col_idx].string = summary[suite]
    # Save updated file
    with open(dashtests_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

if __name__ == "__main__":
    summary = get_regress_summary()
    update_dashtests(summary)
    print("dashtests.html updated with latest regress_quick summary.")
