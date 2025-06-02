import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

SMARTLING_USER_ID = os.getenv('SMARTLING_USER_ID', '')
SMARTLING_SECRET = os.getenv('SMARTLING_SECRET', '')
SMARTLING_PROJECT_ID = os.getenv('SMARTLING_PROJECT_ID', '')

# Helper to update .env file

def update_env_var(key: str, value: str):
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f'{key}='):
            lines[i] = f'{key}={value}\n'
            found = True
            break
    if not found:
        lines.append(f'{key}={value}\n')
    with open(env_path, 'w') as f:
        f.writelines(lines)
