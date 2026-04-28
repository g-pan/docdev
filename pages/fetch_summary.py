import requests
from pathlib import Path

# Fetch OBT summary
obt_url = 'http://172.190.97.122/OBT/summary.html'
coverage_url = 'http://172.190.97.122/coverage/coverageSummary.html'

# Destination file paths
summary_path = Path('summary.html')
dashtest2_path = Path('dashtest2.html')

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
    dashtest2_path.write_text(response.text, encoding="utf-8", newline="\n")
    print('Coverage summary downloaded successfully and saved to dashtest2.html.')
except requests.RequestException as exc:
    print(f'Failed to download coverage summary: {exc}')