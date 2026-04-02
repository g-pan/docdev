#!/usr/bin/env python3
"""
Update pages/dashtests.html from pages/summary.html.

- Reads a stable template file (does NOT read/modify dashtests.html in-place).
- Updates all version columns for Regression + Unit Tests.
- Performance + Coverage: only master has real data; other versions are "N/A".
- Coverage is represented as 4 rows: source files, lines, functions, branches.
- Do NOT touch BVT section (everything after <!-- BVT --> is preserved from template).
- Also auto-fixes malformed template HTML where PERFORMANCE <tbody> isn't closed before COVERAGE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

SUMMARY_PATH = "pages/summary.html"
DASH_TEMPLATE_PATH = "pages/dashtests.TMPL.html"
DASH_PATH = "pages/dashtests.html"

ENGINE_DISPLAY = {"hthor": "hThor", "thor": "Thor", "roxie": "Roxie"}

TD_RE = re.compile(r"<td([^>]*)>(.*?)</td>", re.IGNORECASE | re.DOTALL)
TH_RE = re.compile(r"<th[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)


def _strip_tags(s: str) -> str:
    s = s.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _parse_colspan(td_attrs: str) -> int:
    m = re.search(r'colspan\s*=\s*["\']?(\d+)', td_attrs, re.IGNORECASE)
    return int(m.group(1)) if m else 1


def extract_versions(summary_html: str) -> List[str]:
    headers = [_strip_tags(h) for h in TH_RE.findall(summary_html)]
    versions = [h for h in headers if re.fullmatch(r"\d+\.\d+\.x|master", h)]
    if not versions:
        raise RuntimeError("Could not extract version headers from summary.html")
    return versions


def iter_tds(summary_html: str):
    for attrs, inner in TD_RE.findall(summary_html):
        yield attrs, _strip_tags(inner)


@dataclass(frozen=True)
class RowKey:
    group: str
    env: str
    name: str


def parse_summary_rows(summary_html: str, versions: List[str]) -> Dict[RowKey, Dict[str, str]]:
    """
    Build mapping for the rows we care about.

    We do not rely on <tr> correctness; we stream <td> tokens and assemble 'logical rows'
    based on the known schema: group, env, engine/metric, then len(versions) values.
    """
    results: Dict[RowKey, Dict[str, str]] = {}

    current_group = None
    current_env = None
    pending_name = None
    pending_values: List[str] = []

    def commit(group: str, env: str, name: str, vals: List[str]):
        if len(vals) != len(versions):
            return

        g = group.strip().lower()
        if g.startswith("regression"):
            group_norm = "Regression suite"
        elif g.startswith("unit"):
            group_norm = "Unit tests"
        elif g.startswith("performance"):
            group_norm = "Performance suite"
        elif g.startswith("code coverage"):
            group_norm = "Code coverage"
        else:
            return

        env_norm = env.strip()

        name_norm = name.strip()
        low = name_norm.lower()
        if low in ENGINE_DISPLAY:
            name_norm = ENGINE_DISPLAY[low]

        results[RowKey(group_norm, env_norm, name_norm)] = dict(zip(versions, vals))

    for attrs, text in iter_tds(summary_html):
        t = text

        if t in ("Regression suite", "Unit tests", "Performance suite", "Code coverage"):
            current_group = t
            pending_name = None
            pending_values = []
            continue

        if t in ("BM/VM", "BM", "VM"):
            current_env = t
            pending_name = None
            pending_values = []
            continue

        if not current_group or not current_env:
            continue

        if pending_name is None:
            pending_name = t
            pending_values = []
            continue

        span = _parse_colspan(attrs)
        pending_values.extend([t] * span)

        if len(pending_values) >= len(versions):
            commit(current_group, current_env, pending_name, pending_values[: len(versions)])
            pending_name = None
            pending_values = []

    return results


# -------------------------
# Bullet logic
# -------------------------

def get_bullet(value: str) -> str:
    m = re.search(r"\((\d+(?:\.\d+)?)%\)", value)
    if not m:
        return "bullet-red"
    pct = float(m.group(1))
    if pct == 100.0:
        return "bullet-green"
    if pct >= 99.0:
        return "bullet-yellow"
    return "bullet-red"


def get_bullet_coverage(value: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?)%", value)
    if not m:
        return "bullet-red"
    pct = float(m.group(1))
    if pct >= 80.0:
        return "bullet-green"
    if pct >= 60.0:
        return "bullet-yellow"
    return "bullet-red"


def fmt_cell(value: str, *, coverage: bool) -> str:
    if value in ("N/A", "", "--"):
        return "N/A"
    bullet = get_bullet_coverage(value) if coverage else get_bullet(value)
    return f'<span class="{bullet}">●</span> {value}'


# -------------------------
# Dashboard updating helpers
# -------------------------

def find_block(html: str, start_anchor: str, end_anchor: str) -> str:
    s = html.find(start_anchor)
    e = html.find(end_anchor)
    if s == -1 or e == -1 or e <= s:
        raise RuntimeError(f"Could not locate block anchors: {start_anchor} .. {end_anchor}")
    return html[s:e]


def replace_block(html: str, start_anchor: str, end_anchor: str, new_block: str) -> str:
    s = html.find(start_anchor)
    e = html.find(end_anchor)
    if s == -1 or e == -1 or e <= s:
        raise RuntimeError(f"Could not locate block anchors: {start_anchor} .. {end_anchor}")
    return html[:s] + new_block + html[e:]


def _td_text(td_html: str) -> str:
    inner = re.sub(r"^<td[^>]*>|</td>$", "", td_html, flags=re.IGNORECASE | re.DOTALL)
    return _strip_tags(inner).strip().lower()


def update_row_version_columns(
    row: str,
    versions: List[str],
    values: List[str],
    *,
    master_only: bool,
    coverage: bool,
) -> str:
    """
    Treat the LAST len(versions) cells as version columns and rewrite them.
    Works even when original cells used colspan because we rebuild the tail.
    """
    tds = re.findall(r"<td[^>]*>.*?</td>", row, flags=re.IGNORECASE | re.DOTALL)
    if len(tds) < len(versions) + 1:
        return row

    prefix_tds = tds[: len(tds) - len(versions)]

    new_tds = []
    for ver, val in zip(versions, values):
        if master_only and ver != "master":
            new_tds.append("<td>N/A</td>")
        else:
            new_tds.append(f"<td>{fmt_cell(val, coverage=coverage)}</td>")

    tail = re.split(r"</td>", row, flags=re.IGNORECASE)[-1]
    return "".join(prefix_tds + new_tds) + tail


def update_block_by_engine_text(
    block: str,
    engine_text: str,
    versions: List[str],
    values: List[str],
    *,
    master_only: bool,
    coverage: bool,
    occurrence: int = 1,
) -> str:
    """
    Update the Nth <tr> where ANY <td> text equals engine_text (case-insensitive).
    """
    rows = re.findall(r"<tr[^>]*>.*?</tr>", block, flags=re.IGNORECASE | re.DOTALL)
    want = engine_text.strip().lower()
    count = 0

    for row in rows:
        tds = re.findall(r"<td[^>]*>.*?</td>", row, flags=re.IGNORECASE | re.DOTALL)
        if not tds:
            continue

        if not any(_td_text(td) == want for td in tds):
            continue

        count += 1
        if count != occurrence:
            continue

        updated_row = update_row_version_columns(
            row,
            versions,
            values,
            master_only=master_only,
            coverage=coverage,
        )
        return block.replace(row, updated_row, 1)

    raise RuntimeError(f"Could not find row occurrence={occurrence} for engine text {engine_text!r} in block")


def _ensure_rowspan(td_html: str, rowspan: int) -> str:
    if re.search(r"\srowspan\s*=\s*['\"]?\d+['\"]?", td_html, flags=re.IGNORECASE):
        return re.sub(
            r"\srowspan\s*=\s*['\"]?\d+['\"]?",
            f' rowspan="{rowspan}"',
            td_html,
            flags=re.IGNORECASE,
        )
    return re.sub(r"^<td\b", f'<td rowspan="{rowspan}"', td_html, flags=re.IGNORECASE)


def build_coverage_block(versions: List[str], cov_title_td: str, rows: Dict[RowKey, Dict[str, str]]) -> str:
    """
    Build a 4-row coverage tbody with correct column alignment:
    Test Type | Environment | Engine(metric) | versions...
    """
    def get_vals(metric: str) -> List[str]:
        m = rows.get(RowKey("Code coverage", "BM/VM", metric), {})
        return [m.get(v, "N/A") or "N/A" for v in versions]

    cov_title_td = _ensure_rowspan(cov_title_td, 4)

    def version_cells(values: List[str], *, suffix: str = "") -> str:
        out = []
        for ver, val in zip(versions, values):
            if ver != "master":
                out.append("<td>N/A</td>")
            else:
                cell = fmt_cell(val, coverage=True)
                if suffix:
                    cell = f"{cell} {suffix}".strip()
                out.append(f"<td>{cell}</td>")
        return "".join(out)

    def row(metric: str, values: List[str], *, include_title: bool, suffix: str = "") -> str:
        title_td = cov_title_td if include_title else ""

        # IMPORTANT: make environment BM/VM span the 4 coverage rows too
        env_td = '<td class="platform-label" rowspan="4">BM/VM</td>' if include_title else ""

        metric_td = f"<td>{metric}</td>"
        return f"<tr>{title_td}{env_td}{metric_td}{version_cells(values, suffix=suffix)}</tr>\n"

    out = "<!-- COVERAGE -->\n<tbody class=\"type-group\">\n"
    out += row("source files", get_vals("source files"), include_title=True)
    out += row("lines", get_vals("lines"), include_title=False, suffix="lines")
    out += row("functions", get_vals("functions"), include_title=False)
    out += row("branches", get_vals("branches"), include_title=False)
    out += "</tbody>\n"
    return out


def close_tbody_before_coverage(dash_html: str) -> str:
    """
    Option A: auto-close PERFORMANCE tbody if it's missing </tbody> before <!-- COVERAGE -->.
    Only touches content between <!-- PERFORMANCE --> and <!-- COVERAGE -->.
    """
    perf_start = "<!-- PERFORMANCE -->"
    cov_start = "<!-- COVERAGE -->"

    ps = dash_html.find(perf_start)
    cs = dash_html.find(cov_start)
    if ps == -1 or cs == -1 or cs <= ps:
        return dash_html

    segment = dash_html[ps:cs].lower()
    if "</tbody>" in segment:
        return dash_html

    return dash_html[:cs] + "</tbody>\n" + dash_html[cs:]


def main():
    with open(SUMMARY_PATH, "r", encoding="utf-8", errors="replace") as f:
        summary_html = f.read()

    # IMPORTANT: read template, not the generated output
    with open(DASH_TEMPLATE_PATH, "r", encoding="utf-8", errors="replace") as f:
        dash_html = f.read()

    versions = extract_versions(summary_html)
    summary_rows = parse_summary_rows(summary_html, versions)

    def vals(key: RowKey) -> List[str]:
        m = summary_rows.get(key, {})
        return [m.get(v, "N/A") or "N/A" for v in versions]

    dash_html = close_tbody_before_coverage(dash_html)

    # REGRESSION
    reg_start = "<!-- REGRESSION -->"
    unit_start = "<!-- UNIT TESTS -->"
    reg_block = find_block(dash_html, reg_start, unit_start)

    reg_block2 = reg_block
    reg_block2 = update_block_by_engine_text(reg_block2, "hThor", versions, vals(RowKey("Regression suite", "BM/VM", "hThor")), master_only=False, coverage=False, occurrence=1)
    reg_block2 = update_block_by_engine_text(reg_block2, "Thor", versions, vals(RowKey("Regression suite", "BM/VM", "Thor")), master_only=False, coverage=False, occurrence=1)
    reg_block2 = update_block_by_engine_text(reg_block2, "Roxie", versions, vals(RowKey("Regression suite", "BM/VM", "Roxie")), master_only=False, coverage=False, occurrence=1)
    dash_html = dash_html.replace(reg_block, reg_block2)

    # UNIT TESTS
    perf_start = "<!-- PERFORMANCE -->"
    unit_block = find_block(dash_html, unit_start, perf_start)
    unit_block2 = update_block_by_engine_text(unit_block, "N/A", versions, vals(RowKey("Unit tests", "BM/VM", "N/A")), master_only=False, coverage=False, occurrence=1)
    dash_html = dash_html.replace(unit_block, unit_block2)

    # PERFORMANCE (BM then VM: "thor"/"roxie" appear twice)
    cov_start = "<!-- COVERAGE -->"
    perf_block = find_block(dash_html, perf_start, cov_start)

    perf_block2 = perf_block
    perf_block2 = update_block_by_engine_text(perf_block2, "thor", versions, vals(RowKey("Performance suite", "BM", "Thor")), master_only=True, coverage=False, occurrence=1)
    perf_block2 = update_block_by_engine_text(perf_block2, "roxie", versions, vals(RowKey("Performance suite", "BM", "Roxie")), master_only=True, coverage=False, occurrence=1)
    perf_block2 = update_block_by_engine_text(perf_block2, "thor", versions, vals(RowKey("Performance suite", "VM", "Thor")), master_only=True, coverage=False, occurrence=2)
    perf_block2 = update_block_by_engine_text(perf_block2, "roxie", versions, vals(RowKey("Performance suite", "VM", "Roxie")), master_only=True, coverage=False, occurrence=2)
    dash_html = dash_html.replace(perf_block, perf_block2)

    # COVERAGE (replace whole coverage block; keep BVT untouched)
    bvt_start = "<!-- BVT -->"
    cov_block = find_block(dash_html, cov_start, bvt_start)
    m_cov_title = re.search(r'(<td\s+class="test-type"[^>]*>.*?</td>)', cov_block, flags=re.IGNORECASE | re.DOTALL)
    if not m_cov_title:
        raise RuntimeError("Could not extract Coverage title cell from template HTML")
    cov_title_td = m_cov_title.group(1)

    new_cov_block = build_coverage_block(versions, cov_title_td, summary_rows)
    dash_html = replace_block(dash_html, cov_start, bvt_start, new_cov_block + bvt_start)

    with open(DASH_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(dash_html)

    print("OK: dashtests.html updated successfully from summary.html")


if __name__ == "__main__":
    main()