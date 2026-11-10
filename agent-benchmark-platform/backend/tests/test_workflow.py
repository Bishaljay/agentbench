import os, sys, tempfile
from pathlib import Path
os.environ['BENCHMARK_DB']=str(Path(tempfile.mkdtemp())/'test.db')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from main import app
from worker import work_once
client=TestClient(app)
def test_complete_workflow():
 assert client.post('/api/auth/register',json={'username':'tester','password':'password123'}).status_code==200
 assert client.post('/api/auth/login',json={'username':'tester','password':'wrongpass'}).status_code==401
 token=client.post('/api/auth/login',json={'username':'tester','password':'password123'}).json()['token']; h={'Authorization':'Bearer '+token}
 agents=client.get('/api/agents',headers=h).json(); suites=client.get('/api/benchmarks',headers=h).json()
 r=client.post('/api/runs',headers=h,json={'agent_id':agents[0]['id'],'benchmark_id':suites[0]['id']}); assert r.status_code==200
 assert work_once(); result=client.get('/api/runs/'+str(r.json()['id']),headers=h).json(); assert result['status']=='COMPLETED'; assert len(result['tasks'])==3
 assert client.get('/api/leaderboard',headers=h).json()[0]['score']==100
 for fmt in ('json','csv'): assert client.get(f"/api/reports/{r.json()['id']}/{fmt}",headers=h).status_code==200
 assert client.get('/api/runs',headers=h).json()
 # Slow agent exceeds timeout on reliability suite; failure remains visible.
 r=client.post('/api/runs',headers=h,json={'agent_id':agents[2]['id'],'benchmark_id':suites[2]['id']}).json(); work_once(); detail=client.get('/api/runs/'+str(r['id']),headers=h).json(); assert any(t['status']=='TIMEOUT' for t in detail['tasks'])
 # Failure and controlled retry are persisted.
 for agent,expected in [(agents[3],'FAILED'),(agents[4],'COMPLETED')]:
  r=client.post('/api/runs',headers=h,json={'agent_id':agent['id'],'benchmark_id':suites[2]['id']}).json(); work_once(); detail=client.get('/api/runs/'+str(r['id']),headers=h).json(); assert detail['status']==expected
  if agent['kind']=='recovery': assert any(t['retries']==1 for t in detail['tasks'])
 assert client.post('/api/agents',headers=h,json={'name':'unsafe','kind':'arbitrary'}).status_code==400
 assert client.get('/api/agents').status_code==401
