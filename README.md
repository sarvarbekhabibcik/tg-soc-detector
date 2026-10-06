\# tg-soc-detector



Windows Security log monitor with Telegram alerts (mini SOC detection lab).



\## Detections



| Event ID | Detection | MITRE ATT\&CK |

|---|---|---|

| 4625 (5 in 60 s = brute-force) | Failed logons | T1110 |

| 4720 | User account created | T1136.001 |

| 4732 | User added to Administrators | T1098 |

| 4698 | Scheduled task created | T1053.005 |

| 1102 | Security log cleared | T1070.001 |



\## Setup



1\. Create a bot via @BotFather, get the token and your chat id.

2\. `pip install requests`

3\. Set environment variables `TG\_TOKEN` and `TG\_CHAT`.

4\. Enable audit policies (Logon, User Account Management, Security Group Management, Other Object Access Events).

5\. Run `python detect.py` as Administrator.



\## Screenshots



(add Telegram alert screenshots here)

