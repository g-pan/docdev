from pathlib import Path

import requests
from pathlib import Path
import re

# Fetch OBT summary
obt_url = 'http://172.190.97.122/OBT/summary.html'
coverage_url = 'http://172.190.97.122/coverage/coverageSummary.html'
coverage_base_url = 'http://172.190.97.122/coverage/'

SCRIPT_DIR = Path(__file__).resolve().parent

# Destination file paths
summary_path = SCRIPT_DIR / 'summary.html'
dashtest2_path = SCRIPT_DIR / 'dashtest2.html'
template_path = SCRIPT_DIR / 'dashtests.TMPL.html'


def extract_template_shell(template_html: str) -> tuple[str, str]:
    table_match = re.search(r"<table\b[^>]*>.*?</table>", template_html, flags=re.IGNORECASE | re.DOTALL)
    if not table_match:
        raise RuntimeError("Could not find template table in dashtests.TMPL.html")
    return template_html[: table_match.start()], template_html[table_match.end() :]


def extract_timestamp(html: str) -> str:
    match = re.search(r"<h3[^>]*>.*?</h3>", html, flags=re.IGNORECASE | re.DOTALL)
    return match.group(0).strip() if match else ""


def extract_table(html: str) -> str:
    match = re.search(r"<table\b[^>]*>.*?</table>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise RuntimeError("Could not find table in coverageSummary.html")
    return match.group(0)


def normalize_anchor_closing_tags(html: str) -> str:
    def ensure_closed(match: re.Match[str]) -> str:
        start_tag = match.group(1)
        inner = match.group(2)
        end_tag = match.group(3)
        if '<a' in inner.lower() and '</a>' not in inner.lower():
            inner += '</a>'
        return f"{start_tag}{inner}{end_tag}"

    return re.sub(r"(<t[hd][^>]*>)(.*?)(</t[hd]>)", ensure_closed, html, flags=re.IGNORECASE | re.DOTALL)


def replace_relative_links(html: str) -> str:
    def replace_href(match: re.Match[str]) -> str:
        href = match.group(1)
        if href.startswith('./'):
            href = coverage_base_url + href[2:]
        elif href.startswith('/'):
            href = coverage_base_url.rstrip('/') + href
        elif not href.lower().startswith('http'):
            href = coverage_base_url + href
        return f'href="{href}"'

    return re.sub(r'href="([^"]*)"', replace_href, html, flags=re.IGNORECASE)


def normalize_coverage_table(table_html: str) -> str:
    table_html = re.sub(r"<table\b[^>]*>", '<table class="test-table">', table_html, count=1, flags=re.IGNORECASE)
    table_html = table_html.replace('<br>', '', 1)
    table_html = normalize_anchor_closing_tags(table_html)
    table_html = replace_relative_links(table_html)
    return table_html


def compose_document(prefix: str, suffix: str, timestamp_html: str, table_html: str) -> str:
    timestamp = f"{timestamp_html}\n" if timestamp_html else ""
    return f"{prefix}{timestamp}{table_html}\n{suffix}"

def main() -> None:
    print("Fetching OBT summary...")
    try:
        response = requests.get(obt_url, timeout=30)
        response.raise_for_status()
        summary_path.write_text(response.text, encoding="utf-8", newline="\n")
        print('OBT summary downloaded successfully.')
    except requests.RequestException as exc:
        print(f'Failed to download OBT summary: {exc}')

    print("Fetching coverage summary...")
    try:
        response = requests.get(coverage_url, timeout=30)
        response.raise_for_status()

        template_html = template_path.read_text(encoding="utf-8", errors="replace")
        prefix, suffix = extract_template_shell(template_html)
        timestamp_html = extract_timestamp(response.text)
        table_html = extract_table(response.text)
        normalized_table = normalize_coverage_table(table_html)

        dashtest2_html = compose_document(prefix, suffix, timestamp_html, normalized_table)
        dashtest2_path.write_text(dashtest2_html, encoding="utf-8", newline="\n")
        print('Coverage summary downloaded, styled, and saved to pages/dashtest2.html.')
    except requests.RequestException as exc:
        print(f'Failed to download coverage summary: {exc}')


if __name__ == '__main__':
    main()
