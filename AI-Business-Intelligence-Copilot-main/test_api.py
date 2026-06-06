import requests
import json

URL = "http://localhost:8000/chat"
payload = {
    "query": "Build a sales dashboard",
    "history": []
}

try:
    response = requests.post(URL, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        chars = data.get("charts", [])
        print(f"Number of charts: {len(chars)}")
        if chars:
            # Check for the palette colors in the first chart's data
            chart_json = json.dumps(chars[0])
            if "#00DBDE" in chart_json or "#FC00FF" in chart_json:
                print("PASSED: Vibrant palette detected in chart JSON!")
            else:
                print("FAILED: Vibrant palette NOT detected in chart JSON.")
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
