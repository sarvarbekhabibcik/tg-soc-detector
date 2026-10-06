import os, subprocess, json, time, requests
from collections import deque

TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["TG_CHAT"]

THRESHOLD = 5      # неудачных входов
WINDOW = 60        # за столько секунд = brute-force
POLL = 5           # период опроса лога, сек
ADMINS_SID = "S-1-5-32-544"   # группа Администраторы на любом языке Windows

PS = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625,4720,4732,4698,1102} -MaxEvents 50 -ErrorAction SilentlyContinue |
ForEach-Object {
  [pscustomobject]@{
    rid  = $_.RecordId
    eid  = $_.Id
    time = $_.TimeCreated.ToString('s')
    p    = @($_.Properties | ForEach-Object { "$($_.Value)" })
  }
} | ConvertTo-Json -Compress -Depth 3
"""

def send(text):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as ex:
        print("send error:", ex)

def get_events():
    r = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    out = r.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    return data if isinstance(data, list) else [data]

def fmt(e):
    p, t = e["p"], e["time"]
    if e["eid"] == 4625:
        return (f"🚨 Неудачный вход (4625)\nUser: {p[5]}\nIP: {p[19]}\n"
                f"Time: {t}\nMITRE: T1110 Brute Force")
    if e["eid"] == 4720:
        return (f"⚠️ Создан пользователь (4720)\nNew: {p[0]}\nBy: {p[4]}\n"
                f"Time: {t}\nMITRE: T1136.001 Create Account")
    if e["eid"] == 4732:
        return (f"⚠️ Добавлен в Администраторы (4732)\nGroup: {p[2]}\nMember: {p[1]}\n"
                f"By: {p[6]}\nTime: {t}\nMITRE: T1098 Account Manipulation")
    if e["eid"] == 4698:
        return (f"⚠️ Создана задача планировщика (4698)\nTask: {p[4]}\nBy: {p[1]}\n"
                f"Time: {t}\nMITRE: T1053.005 Scheduled Task")
    if e["eid"] == 1102:
        return (f"🔥 ОЧИЩЕН ЖУРНАЛ БЕЗОПАСНОСТИ (1102)\nTime: {t}\n"
                f"MITRE: T1070.001 Clear Windows Event Logs")
    return f"Event {e['eid']} at {t}"

seen = {e["rid"] for e in get_events()}
fails = deque()
last_bf = 0
send("✅ Детектор запущен")

while True:
    try:
        for e in sorted(get_events(), key=lambda x: x["rid"]):
            if e["rid"] in seen:
                continue
            seen.add(e["rid"])
            if e["eid"] == 4732 and e["p"][4] != ADMINS_SID:
                continue
            send(fmt(e))
            if e["eid"] == 4625:
                now = time.time()
                fails.append(now)
                while fails and now - fails[0] > WINDOW:
                    fails.popleft()
                if len(fails) >= THRESHOLD and now - last_bf > WINDOW:
                    last_bf = now
                    send(f"🔥 BRUTE-FORCE: {len(fails)} неудачных входов "
                         f"за {WINDOW} сек\nMITRE: T1110")
    except Exception as ex:
        print("loop error:", ex)
    time.sleep(POLL)