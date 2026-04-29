#!/usr/bin/env python3
"""
Generate dashboard pages from pages/summary.html.

Design goals:
- Treat summary.html as the source of truth for timestamp, headers, and data cells.
- Use dashtests.TMPL.html only for page shell and first-column test labels/info links.
- Generate dashtests.html without the Performance suite section.
- Generate dashtest2.html from the parsed Performance rows.

This intentionally avoids recalculating bullets or rebuilding formatted values. The
summary file already provides display-ready cell content.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = SCRIPT_DIR / "summary.html"
TEMPLATE_PATH = SCRIPT_DIR / "dashtests.TMPL.html"
OUTPUT_MAIN_PATH = SCRIPT_DIR / "dashtests.html"
OUTPUT_PERF_PATH = SCRIPT_DIR / "dashtest2.html"
BVT_JSON_PATH = SCRIPT_DIR.parent / "bvt" / "BVT.json"

TD_RE = re.compile(r"<td([^>]*)>(.*?)</td>", re.IGNORECASE | re.DOTALL)
TH_RE = re.compile(r"<th[^>]*>(.*?)</th>", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class RowKey:
    group: str
    env: str
    name: str


def strip_tags(value: str) -> str:
    value = value.replace("<br>", " ").replace("<br/>", " ").replace("<br />", " ")
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return unescape(value).strip()


def sanitize_cell_html(value: str) -> str:
    value = value.strip() or "N/A"
    if "<a" in value.lower() and "</a>" not in value.lower():
        value += "</a>"
    # Replace relative links with absolute FQDN links
    value = replace_relative_links(value)
    return value


def replace_relative_links(html: str) -> str:
    """Replace relative links like ./digest.html with absolute FQDN."""
    base_url = "http://172.190.97.122/OBT/"
    # Match href="./filename.html..." and replace with absolute URL
    def replace_href(match):
        href = match.group(1)
        if href.startswith("./"):
            # Remove ./ and prepend base URL
            href = base_url + href[2:]
        elif href.startswith("/"):
            # Already absolute path, use base URL without /
            href = base_url.rstrip("/") + href
        elif not href.startswith("http"):
            # Relative without ./, prepend base URL
            href = base_url + href
        return f'href="{href}"'
    
    # Replace href attributes in anchor tags
    html = re.sub(r'href="([^"]*)"', replace_href, html, flags=re.IGNORECASE)
    return html


def parse_colspan(td_attrs: str) -> int:
    match = re.search(r"colspan\s*=\s*[\"']?(\d+)", td_attrs, re.IGNORECASE)
    return int(match.group(1)) if match else 1


def preserve_td_attrs(attrs: str) -> str:
    """Strip layout attrs (colspan, rowspan) but keep presentation attrs (style, align)."""
    result = re.sub(r"\s*\bcolspan\s*=\s*['\"]?\d+['\"]?", "", attrs, flags=re.IGNORECASE)
    result = re.sub(r"\s*\browspan\s*=\s*['\"]?\d+['\"]?", "", result, flags=re.IGNORECASE)
    return (" " + result.strip()) if result.strip() else ""


def set_rowspan(td_html: str, rowspan: int) -> str:
    if re.search(r"\srowspan\s*=\s*['\"]?\d+['\"]?", td_html, flags=re.IGNORECASE):
        return re.sub(
            r"\srowspan\s*=\s*['\"]?\d+['\"]?",
            f' rowspan="{rowspan}"',
            td_html,
            flags=re.IGNORECASE,
        )
    return re.sub(r"^<td\b", f'<td rowspan="{rowspan}"', td_html, flags=re.IGNORECASE)


def normalize_group(text: str) -> str:
    low = text.strip().lower()
    if low.startswith("regression"):
        return "Regression suite"
    if low.startswith("unit"):
        return "Unit tests"
    if low.startswith("performance"):
        return "Performance suite"
    if low.startswith("code coverage") or low.startswith("coverage"):
        return "Code coverage"
    if low.startswith("build verification") or low == "bvt":
        return "BVT"
    return ""


def normalize_name(text: str) -> str:
    low = text.strip().lower()
    if low == "hthor":
        return "hThor"
    if low == "thor":
        return "Thor"
    if low == "roxie":
        return "Roxie"
    return text.strip()


def extract_timestamp(summary_html: str) -> str:
    match = re.search(r"<h3[^>]*>.*?</h3>", summary_html, flags=re.IGNORECASE | re.DOTALL)
    return match.group(0).strip() if match else ""


def extract_headers(summary_html: str) -> List[str]:
    headers = [strip_tags(h) for h in TH_RE.findall(summary_html)]
    if not headers:
        raise RuntimeError("Could not extract table headers from summary.html")
    return headers


def parse_summary_rows(summary_html: str, version_count: int) -> Tuple[Dict[RowKey, List[str]], List[str]]:
    rows: Dict[RowKey, List[str]] = {}
    group_order: List[str] = []

    current_group = ""
    current_env = ""
    pending_name = ""
    pending_values: List[str] = []

    def commit(group: str, env: str, name: str, values: List[str]) -> None:
        normalized_group = normalize_group(group)
        if not normalized_group:
            return
        key = RowKey(normalized_group, env.strip(), normalize_name(name))
        rows[key] = values[:version_count]
        if normalized_group not in group_order:
            group_order.append(normalized_group)

    for attrs, inner in TD_RE.findall(summary_html):
        text = strip_tags(inner)
        normalized_group = normalize_group(text)

        if normalized_group in {
            "Regression suite",
            "Unit tests",
            "Performance suite",
            "Code coverage",
            "BVT",
        }:
            current_group = normalized_group
            pending_name = ""
            pending_values = []
            continue

        if text in {"BM/VM", "BM", "VM"}:
            current_env = text
            pending_name = ""
            pending_values = []
            continue

        if not current_group or not current_env:
            continue

        if not pending_name:
            pending_name = text
            pending_values = []
            continue

        colspan = parse_colspan(attrs)
        if colspan > 1:
            # Colspan N/A cells — expand into individual plain cells
            pending_values.extend(["<td>N/A</td>"] * colspan)
        else:
            td_attrs = preserve_td_attrs(attrs)
            pending_values.append(f"<td{td_attrs}>{sanitize_cell_html(inner)}</td>")

        if len(pending_values) >= version_count:
            commit(current_group, current_env, pending_name, pending_values)
            pending_name = ""
            pending_values = []

    return rows, group_order


def extract_template_shell(template_html: str) -> Tuple[str, str]:
    table_match = re.search(r"<table\b[^>]*>.*?</table>", template_html, flags=re.IGNORECASE | re.DOTALL)
    if not table_match:
        raise RuntimeError("Could not find template table in dashtests.TMPL.html")
    return template_html[: table_match.start()], template_html[table_match.end() :]


def extract_template_title_cells(template_html: str) -> Dict[str, str]:
    markers = {
        "Regression suite": "REGRESSION",
        "Unit tests": "UNIT TESTS",
        "Performance suite": "PERFORMANCE",
        "Code coverage": "COVERAGE",
        "BVT": "BVT",
    }

    title_cells: Dict[str, str] = {}
    for group, marker in markers.items():
        pattern = rf"<!--\s*{re.escape(marker)}\s*-->.*?(<td\s+class=\"test-type\"[^>]*>.*?</td>)"
        match = re.search(pattern, template_html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title_cells[group] = match.group(1)

    return title_cells


def fallback_title_cell(group: str) -> str:
    label = group.replace("suite", "Suite")
    return f'<td class="test-type">{label}</td>'


def build_header_row(headers: List[str]) -> str:
    return "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>\n"


def build_group_tbody(
    group: str,
    group_rows: List[Tuple[RowKey, List[str]]],
    title_cell_html: str,
) -> str:
    if not group_rows:
        return ""

    title_cell_html = set_rowspan(title_cell_html, len(group_rows))
    tbody_class = "type-group bvt-group" if group == "BVT" else "type-group"
    lines = [f'<tbody class="{tbody_class}">']

    index = 0
    while index < len(group_rows):
        env = group_rows[index][0].env
        env_end = index
        while env_end < len(group_rows) and group_rows[env_end][0].env == env:
            env_end += 1
        env_span = env_end - index

        for row_index in range(index, env_end):
            row_key, values = group_rows[row_index]
            cells = ["<tr>"]
            if row_index == 0:
                cells.append(title_cell_html)
            if row_index == index:
                if env_span > 1:
                    cells.append(f'<td class="platform-label" rowspan="{env_span}">{row_key.env}</td>')
                else:
                    cells.append(f'<td class="platform-label">{row_key.env}</td>')
            cells.append(f"<td>{row_key.name}</td>")
            cells.extend(values)  # values are already full <td>...</td> HTML
            cells.append("</tr>")
            lines.append("".join(cells))

        index = env_end

    lines.append("</tbody>")
    return "\n".join(lines) + "\n"


def get_master_col_index(headers: List[str]) -> int:
    """Find the index of the 'master' column in the values list (relative to versions only)."""
    for i, header in enumerate(headers[3:]):
        if header.strip().lower() == "master":
            return i  # Return index relative to the version columns (0-based)
    return len(headers) - 4  # Default to last version column index


def build_main_table(
    headers: List[str],
    rows: Dict[RowKey, List[str]],
    group_order: List[str],
    title_cells: Dict[str, str],
) -> str:
    grouped_rows: Dict[str, List[Tuple[RowKey, List[str]]]] = {}
    for key, values in rows.items():
        grouped_rows.setdefault(key.group, []).append((key, values))

    parts = ['<table class="test-table">', build_header_row(headers)]
    master_idx = get_master_col_index(headers)
    
    for group in group_order:
        title_cell = title_cells.get(group, fallback_title_cell(group))
        group_rows = grouped_rows.get(group, [])
        if not group_rows:
            continue
        
        # For Performance suite, show only master column value; rest are N/A
        if group == "Performance suite":
            perf_rows_filtered = []
            for key, values in group_rows:
                # Extract master column value, keep rest as N/A
                na_cells = ["<td>N/A</td>"] * len(values)
                if master_idx < len(values):
                    na_cells[master_idx] = values[master_idx]
                perf_rows_filtered.append((key, na_cells))
            parts.append(build_group_tbody(group, perf_rows_filtered, title_cell))
        else:
            parts.append(build_group_tbody(group, group_rows, title_cell))
    
    parts.append("</table>")
    return "\n".join(parts)


def build_performance_table(
    headers: List[str],
    rows: Dict[RowKey, List[str]],
    title_cells: Dict[str, str],
) -> str:
    performance_rows = [(key, values) for key, values in rows.items() if key.group == "Performance suite"]
    if not performance_rows:
        return '<table class="test-table">\n' + build_header_row(headers) + "</table>"

    title_cell = title_cells.get("Performance suite", fallback_title_cell("Performance suite"))
    tbody = build_group_tbody("Performance suite", performance_rows, title_cell)
    return '<table class="test-table">\n' + build_header_row(headers) + tbody + "</table>"


def compose_document(prefix: str, suffix: str, timestamp_html: str, table_html: str) -> str:
    timestamp = f"{timestamp_html}\n" if timestamp_html else ""
    return f"{prefix}{timestamp}{table_html}\n{suffix}"


def load_bvt_release() -> Optional[Dict[str, Any]]:
    if not BVT_JSON_PATH.exists():
        return None

    try:
        payload = json.loads(BVT_JSON_PATH.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None

    releases = payload.get("Releases") if isinstance(payload, dict) else None
    if not isinstance(releases, list) or not releases:
        return None

    first = releases[0]
    return first if isinstance(first, dict) else None


def status_badge(value: str) -> str:
    normalized = value.strip().lower()
    color = "#16a34a" if normalized in {"passed", "pass", "ok", "success"} else "#dc2626"
    if normalized not in {"passed", "pass", "ok", "success", "failed", "fail", "error"}:
        color = "#f59e0b"
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:999px;color:#fff;'
        f'font-weight:600;background:{color};">{escape(value)}</span>'
    )


def build_bvt_card(bvt_release: Dict[str, Any]) -> str:
    release_name = str(bvt_release.get("name", "N/A"))
    overall_result = str(bvt_release.get("result", "unknown"))

    check_items: List[Tuple[str, str]] = []
    for key, value in bvt_release.items():
        if key in {"name", "result"}:
            continue
        check_items.append((str(key).strip(), str(value).strip()))

    if not check_items:
        check_items = [("No checks found", "unknown")]

    rows: List[str] = []
    for index, (check_name, check_status) in enumerate(check_items):
        cells = ["<tr>"]
        if index == 0:
            cells.append(f'<td rowspan="{len(check_items)}">{escape(release_name)}</td>')
            cells.append(f'<td rowspan="{len(check_items)}">{status_badge(overall_result)}</td>')
        cells.append(f"<td>{escape(check_name)}</td>")
        cells.append(f"<td>{status_badge(check_status)}</td>")
        cells.append("</tr>")
        rows.append("".join(cells))

    return (
        '\n<div style="max-width:1100px;margin:1.25em auto 0;">\n'
        '  <h3 style="margin:0 0 0.5em 0;">Build Verification Test (BVT)</h3>\n'
        '  <table class="test-table" style="min-width:700px;max-width:1100px;">\n'
        '    <tr><th>Release</th><th>Overall</th><th>Check</th><th>Status</th></tr>\n'
        f"{chr(10).join(rows)}\n"
        '  </table>\n'
        '</div>\n'
    )


def main() -> None:
    summary_html = SUMMARY_PATH.read_text(encoding="utf-8", errors="replace")
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8", errors="replace")

    timestamp_html = extract_timestamp(summary_html)
    headers = extract_headers(summary_html)
    version_count = max(len(headers) - 3, 0)
    if version_count == 0:
        raise RuntimeError("Expected at least three leading headers and one version column in summary.html")

    rows, group_order = parse_summary_rows(summary_html, version_count)
    prefix, suffix = extract_template_shell(template_html)
    title_cells = extract_template_title_cells(template_html)

    main_table = build_main_table(headers, rows, group_order, title_cells)
    bvt_release = load_bvt_release()
    bvt_card_html = build_bvt_card(bvt_release) if bvt_release else ""
    main_html = compose_document(prefix, suffix, timestamp_html, main_table + bvt_card_html)
    OUTPUT_MAIN_PATH.write_text(main_html, encoding="utf-8", newline="\n")

    print("OK: generated dashtests.html from summary.html")


if __name__ == "__main__":
    main()
