#!/bin/bash
if [[ $(du -d 0 @@{log_path}@@ | awk  '{print $1}') -gt @@{size_limit}@@ ]]; then
  echo "INFO: Log size is more than 1GB. Clearing up old logs..."
  rm -f @@{log_path}@@/*\.log\.*
fi
