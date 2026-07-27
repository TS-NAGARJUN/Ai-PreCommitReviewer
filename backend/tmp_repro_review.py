import os
from fastapi.testclient import TestClient
from app.main import app

os.environ['ANTIGRAVITY_API_KEY'] = 'dummy'
os.environ['GROQ_API_KEY'] = 'dummy'

client = TestClient(app)
response = client.post('/review', json={'repoPath': r'd:\AI-PreCommitReviewer'})
print(response.status_code)
print(response.text)
