#!/usr/bin/env bash
# filepath: /home/anthony/dev/Big-Data/Final_Project/SQL-o1/kill_llm_api.sh
# Kill any running API server on port 8000 or 8100

for port in 8000 8100; do
  pid=$(lsof -t -i:$port)
  if [ ! -z "$pid" ]; then
    echo "Killing process $pid on port $port..."
    kill -9 $pid
  else
    echo "No process found on port $port."
  fi
done