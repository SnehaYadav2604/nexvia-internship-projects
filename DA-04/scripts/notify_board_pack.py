import glob
import json
import os
import urllib.request

latest = sorted(glob.glob("reports/board_pack_*.pdf"))[-1]
message = f"Monthly board pack ready: {latest}"
print(message)

webhook = os.environ.get("SLACK_WEBHOOK_URL")
if webhook:
    req = urllib.request.Request(webhook, data=json.dumps({"text": message}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    print("Sent to Slack.")

    