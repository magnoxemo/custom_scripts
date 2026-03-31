#!/usr/bin/env bash

WATCH_FILE="$1"

if [ -z "$WATCH_FILE" ]; then
  echo "Usage: $0 <file>"
  exit 1
fi

last_hash=""

while true; do
  current_hash=$(sha256sum "$WATCH_FILE" 2>/dev/null | awk '{print $1}')

  if [[ "$current_hash" != "$last_hash" ]]; then
    echo "Change detected in $WATCH_FILE"
    make
    last_hash="$current_hash"
  fi

  sleep 20
done
