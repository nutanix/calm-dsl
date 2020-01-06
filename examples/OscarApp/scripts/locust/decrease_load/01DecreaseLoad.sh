#!/bin/bash
set -ex

# Ensure we're not decreasing below a load of 25
if [ "@@{load}@@" -le "25" ]
then
  echo "Already at minimum load"
  return 0
fi

echo "Decreasing load variable"
echo "load=$((@@{load}@@ - 25))"
