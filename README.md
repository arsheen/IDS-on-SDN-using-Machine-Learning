

Implemented a network intrusion detection system for a software defined network using Random Forest method for classification of port and flow statistics.

Project Execution:

Create a mininet topology.
ssh to the mininet virtual machine.
Run the collectStats.py file on the ryu controller. (Data from collectStat.py file is used for training the algorithm.)
Now, run IDS_RyuApp.py to check whether current traffic is clean or malacious using machine learning algorithm.
