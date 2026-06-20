import requests, json
with open('../data/uploads/TR-C29ED1.jpg', 'rb') as f:
    res = requests.post('http://localhost:8002/api/detect', files={'file': f})
    data = res.json()
    print("Vehicles:", data.get('vehicles_detected'))
    print("Violations:", data.get('violations_count'))
    for v in data.get('violations', []):
        print(v)
