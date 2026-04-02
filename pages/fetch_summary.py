import requests

url = 'http://172.190.97.122/OBT/summary.html'

# Destination file path (must match updater + workflow git add)
file_path = 'pages/summary.html'

response = requests.get(url, timeout=30)

if response.status_code == 200:
    with open(file_path, 'w', encoding='utf-8', newline='\n') as file:
        file.write(response.text)
    print('Summary downloaded successfully.')
else:
    raise SystemExit(f'Failed to download summary: {response.status_code}')