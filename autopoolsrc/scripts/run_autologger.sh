#!/bin/bash
cd /home/autologger
source al-env/bin/activate
cd run
python small_run.py > debug.txt
