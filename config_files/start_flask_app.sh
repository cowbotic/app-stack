#!/bin/bash

echo "--Start Script"
#If there is a debug file, just run the app in debug mode
if [ -e /debug ]; then
        echo "App running in debug mode"
        python3 app.py
#Otherwise, install OS packages and python libraries and start in standard mode
else
  if [ -e /flask-app/os-packets.txt ]; then
    echo "Installing OS packages"
    apk add --no-cache $(cat /flask-app/os-packets.txt) > /dev/null
  fi
  if [ -e /flask-app/python_libraries.txt ]; then
    echo "Installing Python packages"
    pip3 install -r /flask-app/python_libraries.txt > /dev/null
  fi
  echo "App running in production mode"
  nginx && uwsgi --ini /flask_app.ini
fi
echo "--End Start Script"