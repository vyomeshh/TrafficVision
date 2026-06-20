import sqlite3, json
conn = sqlite3.connect('app/database/trafficvision.db')
c = conn.cursor()
c.execute("SELECT logs FROM system_logs WHERE detection_id='TR-C29ED1'")
row = c.fetchone()
if row:
    logs = json.loads(row[0])
    for l in logs: print(l['message'])
