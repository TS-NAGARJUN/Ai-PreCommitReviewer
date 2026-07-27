import json
import urllib.request

payload = {"repoPath": r"d:\AI-PreCommitReviewer"}
req = urllib.request.Request(
    'https://ai-precommitreviewer.onrender.com/review',
    data=json.dumps(payload).encode(),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(resp.status)
        print(resp.read().decode())
except Exception as e:
    print(type(e).__name__, e)
    if hasattr(e, 'read'):
        print(e.read().decode())
