# IDS-on-SDN-using-Machine-Learnng
Work in progress:


Plan:
Intrusion detection system for a software defined network using Random Forest method for  classification of flows. 
Created an application for IDS on the SDN controller (Ryu) using Python


Implementation so far:


Created two applications:


mal.py ---> to collect the training data by querying the data plane for switch statistics


mal_ids.py -----> monitors the real time traffic from the switch and displays a message if an intrusion is detected



Future Scope:


To read Group and Meter tables stats for more fine tuned functioning
