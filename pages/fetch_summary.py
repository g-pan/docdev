import requests

# URL to fetch the summary
url = 'http://172.190.97.122/OBT/summary.html'

# Destination file path
file_path = 'summary.html'

# Fetch the summary
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Write the content to the file
    with open(file_path, 'w') as file:
        file.write(response.text)
    print('Summary downloaded successfully.')
else:
    print('Failed to download summary:', response.status_code)