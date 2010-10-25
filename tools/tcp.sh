#!/bin/bash
# this scripts runs your bot using TCP server
# change your nickname - i.e. testbot123
rm MyBot.log
java TCP "72.44.46.68" "995" "reborn-2" "python ../MyBot.py --log MyBot.log" "10000"
