#!/bin/bash
set -ex

# Ensure we're not increasing above a load of 125
if [ "@@{load}@@" -gt "125" ]
then
  echo "Already at maximum load"
  return 0
fi

echo "Increasing load variable"
echo "load=$((@@{load}@@ + 100))"
