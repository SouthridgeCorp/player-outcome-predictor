#!/bin/bash
python -m venv venv
source venv/bin/activate
echo "activated virtual enviroment - venv"
if [ -f requirements.txt ]
then
  echo "Installing requirements"
  pip install -r requirements.txt
else
  echo "ERROR: requirements.txt not found"
fi
