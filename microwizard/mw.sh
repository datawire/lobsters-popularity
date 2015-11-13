#!/bin/bash -eu

# file: mw.sh

function init {
  pip install -r requirements.txt
}

function run {
  exec python popularity.py development config.yml
}

command=$1

cd /usr/src/service
if [ "$command" = "init" ]; then
  init
elif [ "$command" = "run" ]; then
  run
else
  echo "unknown command (name: $command)"
  exit 1
fi