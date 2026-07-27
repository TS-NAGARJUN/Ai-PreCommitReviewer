import os
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from app.main import app

load_dotenv(dotenv_path='.env', override=False)

client = TestClient(app)
response = client.post('/review', json={'repoPath': r'd:\AI-PreCommitReviewer'})
print('status=', response.status_code)
print(response.text)
