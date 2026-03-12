import os
import pprint
import requests
from dotenv import load_dotenv

load_dotenv('C:/projects/Bay-Blog/selenium-trends/.env')

base = os.environ['N8N_BASE_URL'].rstrip('/')
api_key = os.environ['N8N_API_KEY']
workflow_id = os.environ['N8N_WORKFLOW_ID']

wf = requests.get(
    f'{base}/api/v1/workflows/{workflow_id}',
    headers={'X-N8N-API-KEY': api_key},
    timeout=30,
).json()

for node in wf.get('nodes', []):
    if node.get('name') in ('AI Rewrite (Mistral-7B)', 'Parse Mistral JSON'):
        print('NODE', node.get('name'))
        pprint.pp(node.get('parameters'))
        print('continueOnFail', node.get('continueOnFail'), 'onError', node.get('onError'))
        print('---')
