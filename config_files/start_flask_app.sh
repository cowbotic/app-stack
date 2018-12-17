#!/bin/bash

#If there is a debug file, just run the app in debug mode
if [ -e /debug ]; then
        echo "App running in debug mode"
        python3 app.py
#Otherwise, install OS packages and python libraries and start in standard mode
else
  if [ -e os-packets.txt ]; then
    apk add --no-cache $(cat os-packets.txt)
  fi
  if [ -e requirements.txt ]; then
    pip3 install -r python_libraries.txt
  fi
  echo "App running in production mode"
  nginx && uwsgi --ini /flask-app.ini
fi