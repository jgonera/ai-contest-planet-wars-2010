Planet Wars Starter Kit
=======================

This package in an alternative Python starter kit for Planet Wars Google AI
Challenge (http://ai-contest.com/). It is a modified RebelXT's version.

You can find example bots in ``example`` directory. If you want to use one of
them, copy it to the main directory and rename it to ``MyBot.py``.

Requirements
------------

* Python 2.5
* Java 1.6 (to connect to the TCP server)

Included tools
--------------

Some helpful tools can be found in the ``tools`` directory.

1. To run a game against a DualBot on map 5, run

	./dual.sh 5

2. To play all official sample bots on all 100 maps, run

	./batch.sh

   This will take a few minutes to run...

3. To play other people's bots in REAL TIME without having to submit
   your code to the contest server, compile TCP.java by running

	javac TCP.java

   Then you can run the following command to play on the TCP server:

	./tcp.sh

   See http://www.benzedrine.cx/planetwars/ for more details. 
   Thanks dhartmei for setting up the server!

4. To replay a game locally after is has been played on the server, run
   replay.sh script and pass game page URL as a parameter. 
   This is very useful for debugging your bot.

	./replay.sh http://ai-contest.com/visualizer.php?game_id=4607627

