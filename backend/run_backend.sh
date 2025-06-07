#!/bin/zsh
if ! command -v python3 &> /dev/null; then
  echo "Python 3 is not installed. Please install Python 3."
  exit 1
fi

if ! command -v pip3 &> /dev/null; then
  echo "pip3 is not installed. Please install pip3."
  exit 1
fi

if [ -f requirements.txt ]; then
  echo "Installing Python dependencies..."
  pip3 install -r requirements.txt
else
  echo "requirements.txt not found!"
  exit 1
fi

if ! python3 -c "import uvicorn" 2>/dev/null; then
  echo "uvicorn not found, installing..."
  pip3 install uvicorn
fi

exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
