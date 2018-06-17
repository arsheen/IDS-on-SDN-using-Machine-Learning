# IDS using ML RyuApp

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

# instantiating the Random Forest Classifier 
rf_flow = RandomForestClassifier(n_estimators = 10)
rf_port = RandomForestClassifier(n_estimators = 10)
rf_group = RandomForestClassifier(n_estimators = 10)

flag_flow = True
flag_port = True
flag_group = True

class IDS_Application(simple_switch_13.SimpleSwitch13):
	
	def __init__(self, *args, **kwargs):
		super(IDS_Application, self).__init__(*args, **kwargs)
		self.datapaths = {}

		# Create a CSV file to store the Test data		
		file = open("/home/arsheen/Downloads/MalPredictFlowStatsfile.txt","a+")
		file.write('dp_id,in_port,eth_dst,packets,bytes\n')
		file.write('516,1,1,10002203,238000000\n')
		file.write('516,1,1,40022000,2380000000\n')
		file.close()

		file = open("/home/arsheen/Downloads/MalPredictPortStatsfile.txt","a+")
		file.write('dp_id,port_no,rx_bytes,rx_pkts,tx_bytes,tx_pkts\n')
		file.write('1,2,10,10,10,10\n')
		file.close()

		self.monitor_thread = hub.spawn(self.main)

	
    # Asynchronous message to inform controller of the status of links in the network
	@set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
	def state_change_handler(self, ev):
		datapath = ev.datapath
		if ev.state == MAIN_DISPATCHER:
			if datapath.id not in self.datapaths:
				self.datapaths[datapath.id] = datapath

		elif ev.state == DEAD_DISPATCHER:
			if datapath.id in self.datapaths:
				del self.datapaths[datapath.id]


	def main(self):
		training_flag = True
		while True:
			# Train the model once			
			if training_flag:
				self.IDS_training()
				training_flag = False

			for dp in self.datapaths.values():
				# Give 30 second wait time to create topology
				if training_flag:
					hub.sleep(30)
				self.request_stats(dp)

			# Implement IDS application every 30 seconds			
			self.IDS_impl()
			hub.sleep(30)

	# Remove unnecessary columns and calculate and store only current number of packets and bytes that have arrived instead of cummulative count
	# For each flow entry
	def data_cleaning_flow(self, input_path,output_path):
		file = open(input_path,"r")
		file1 = open(output_path,"a+")
		b = [0,0,0,0,0]
		a = []
		c = [0,0,0,0,0]
		dict = {}
		first_line_flag_flow = True
		for line in file:
			a = line.split(",")
			if first_line_flag_flow:
				file1.write(str(a[3])+","+str(a[4]))
				first_line_flag_flow = False
			else:
				key = str(a[0])+"_"+str(a[1])+"_"+str(a[2])
				if key in dict:
					ab = dict[key].split(",")
					for i in range(len(ab)):
						if i == 2:
							continue
						else:
							c[i] = int(a[i]) - int(ab[i])
					file1.write(str(c[3])+","+ str(c[4])+"\n")
					dict[key] =( str(a[0])+ "," +str(a[1]) + "," + str(a[2])+ "," + str(a[3])+"," + str(a[4]))
				else:
					dict[key] = (str(a[0])+ "," +str(a[1]) + "," + str(a[2])+ "," + str(a[3])+"," + str(a[4]))
					file1.write(str(a[3])+","+str(a[4])+"\n")
		file.close()
		file1.close()

	''' Remove unnecessary columns and calculate and store only current number of packets and bytes that have 
	arrived instead of cummulative count'''
	# for each port entry
	def data_cleaning_port(self, input_path, output_path):
		file = open(input_path,"r")
		file1 = open(output_path,"a+")
		b = [0,0,0,0,0,0]
		a = []
		c = [0,0,0,0,0,0]
		dict = {}
		first_line_flag_port = True
		for line in file:
			a = line.split(",")
			if first_line_flag_port:
				file1.write(str(a[2])+ "," + str(a[3])+","+str(a[4])+ "," + str(a[5]))
				first_line_flag_port = False
			else:
				key = str(a[0])+ "_" +str(a[1])
				if key in dict:
					ab = dict[key].split(",")
					for i in range(len(ab)):
						c[i] = int(a[i]) - int(ab[i])
					file1.write(str(c[2])+ "," + str(c[3])+","+str(c[4])+ "," + str(c[5])+"\n")
					dict[key] =( str(a[0])+ "," +str(a[1]) + "," + str(a[2])+ "," + str(a[3])+"," + str(a[4])+ "," + str(a[5]))
				else:
					dict[key] = (str(a[0])+ "," +str(a[1]) + "," + str(a[2])+ "," + str(a[3])+"," + str(a[4])+ "," + str(a[5]))
					file1.write(str(a[2])+ "," + str(a[3])+","+str(a[4])+ "," + str(a[5])+"\n")
		file.close()
		file1.close()


	# Model training
	def IDS_training(self):
		# Read cleaned flow statistics data
		self.data_cleaning_flow('/home/arsheen/Downloads/FlowStatsfile.txt','/home/arsheen/Downloads/FlowStatsfile_cleaned.txt')
		flow_without_key = pd.read_csv('/home/arsheen/Downloads/MalFlowStatsfile_cleaned.txt')
		flow_stat_input_target = pd.read_csv('/home/arsheen/Downloads/MalFlowStatsfile_target.txt')

		# Read cleaned port statistics data
		self.data_cleaning_port('/home/arsheen/Downloads/PortStatsfile.txt','/home/arsheen/Downloads/PortStatsfile_cleaned.txt')
		port_without_key = pd.read_csv('/home/arsheen/Downloads/MalPortStatsfile_cleaned.txt')
		port_stat_input_target = pd.read_csv('/home/arsheen/Downloads/MalPortStatsfile_target.txt')

		# Convert flow statistics data from string to int and fit it on the machine learning model
		flow_without_key = flow_without_key.apply(pd.to_numeric)
		flow_stat_input_target = flow_stat_input_target.apply(pd.to_numeric, errors='ignore')
		rf_flow.fit(flow_without_key,flow_stat_input_target.values.ravel())

		# Convert port statistics data from string to int and fit it on the machine learning model
		port_without_key = port_without_key.apply(pd.to_numeric)
		port_stat_input_target = port_stat_input_target.apply(pd.to_numeric)
		rf_port.fit(port_without_key,port_stat_input_target.values.ravel())
		

	# Check for the accuracy of the model 
	def check_accuracy(self,model,input_data, input_target):
		cross_val_score_stat = cross_val_score(model, input_data, input_target, scoring = 'accuracy', cv = 10)
		mean_cross_val_score = cross_val_score_stat.mean()
		print(mean_cross_val_score)


	# IDS Implementation: monitoring real time traffic and predicting whether it is malicious.
	def IDS_impl(self):
		self.data_cleaning_flow('/home/arsheen/Downloads/PredictFlowStatsfile.txt','/home/arsheen/Downloads/PredictFlowStatsfile_cleaned.txt')
		self.data_cleaning_port('/home/arsheen/Downloads/PredictPortStatsfile.txt','/home/arsheen/Downloads/PredictPortStatsfile_cleaned.txt')	
		
		#Read cleaned file
		flow_predict_without_key = pd.read_csv('/home/arsheen/Downloads/PredictFlowStatsfile_cleaned.txt')
		port_predict_without_key = pd.read_csv('/home/arsheen/Downloads/PredictPortStatsfile_cleaned.txt')
		
		#convert to numeric form
		flow_predict_without_key = flow_predict_without_key.apply(pd.to_numeric)
		port_predict_without_key = port_predict_without_key.apply(pd.to_numeric)
		
		#convert to list form for iteration
		flow_predict_list=list(flow_predict_without_key.values.tolist())

		#Use test data to check for intrusion
		for i in flow_predict_list:			
			if i==['packets','bytes']:
				continue
			else:
				temp = list(i)
				test = []				
				test.append(temp)
				# Binary classification				
				flag_flow = rf_flow.predict(test)
				if flag_flow == 1:
					self.anomaly_specific_actions(True,True)
				else:
					self.anomaly_specific_actions(False,True)
			

		port_predict_list=list(port_predict_without_key.values.tolist())
		for j in port_predict_list:
			if j==['rx_bytes','rx_pkts','tx_bytes','tx_pkts']:
				continue
			else:
				temp = list(j)
				test = []				
				test.append(temp)
				# Binary classification
				flag_port = rf_port.predict(test)
				if flag_port == 1:
					self.anomaly_specific_actions(True,True)
				else:
					self.anomaly_specific_actions(True,False)
		
	# Controller to Switch request for stats
	def request_stats(self, datapath):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser

		# to collect dp_id, pkt_count, byte_count
		req = parser.OFPFlowStatsRequest(datapath)      
		datapath.send_msg(req)

		# to collect dp_id, port_no, rx_bytes, rx_pkts, tx_bytes, tx_pkts	
		req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)     
		datapath.send_msg(req)


	# Switch to Controller reply with statistics
	@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
	def flow_stats_reply_handler(self, ev):
		body = ev.msg.body
		file = open("MalPredictFlowStatsfile.txt","a+")
		for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'],flow.match['eth_dst'])):
			file.write("\n"+str(ev.msg.datapath.id) + ","+ str(stat.match['in_port'])+ "," + str(stat.match['eth_dst'])+ "," + 
				str(stat.packet_count) + "," + str(stat.byte_count))
		file.close()

	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def port_stats_reply_handler(self, ev):
		body = ev.msg.body
		file = open("MalPredictPortStatsfile.txt","a+")
		for stat in sorted(body, key=attrgetter('port_no')):
			file.write("\n"+str(ev.msg.datapath.id) + "," + str(stat.port_no) + "," +
			str(stat.rx_bytes)+ "," + str(stat.rx_packets) + "," + str(stat.tx_bytes) + "," + str(stat.tx_packets))
		file.close()


	#Anomaly specific actions
	def anomaly_specific_actions(self,flag_flow, flag_port):
		if (not flag_flow) or (not flag_port):
			self.logger.debug("Intrusion Detected")
			print("Intrusion Detected")
		else:
			self.logger.debug("Everything is awesome")
			print("Everything is awesome")
		
