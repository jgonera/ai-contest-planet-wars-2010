#!/bin/bash
# this scripts runs your bot using TCP server
# change your nickname - i.e. testbot123
java TCP "72.44.46.68" "995" "reborn-3.2" "python ../MyBot.py --log logs/`date -u +"%Y.%m.%d-%X"`.log" "10000"
