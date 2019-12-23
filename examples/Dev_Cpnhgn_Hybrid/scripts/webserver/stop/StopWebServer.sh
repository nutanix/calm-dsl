#!/bin/bash
set -ex

sudo kill $(ps aux | grep flask | grep Sl | awk '{print $2}') || true
