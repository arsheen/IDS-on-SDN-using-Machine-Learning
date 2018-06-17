# Collect Statistic Model

from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

class CollectTrainingStatsApp(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(CollectTrainingStatsApp, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self.monitor)
        
        file = open("FlowStatsfile.txt","a+")
        file.write('dp_id,in_port,eth_dst,packets,bytes')
        file.close()

        file = open("PortStatsfile.txt","a+")
        file.write('dp_id,port_no,rx_bytes,rx_pkts,tx_bytes,tx_pkts')
        file.close()


        file = open("FlowStatsfile_target.txt","a+")
        file.write('target')
        file.close()

        file = open("PortStatsfile_target.txt","a+")
        file.write('target')
        file.close()


    #Asynchronous message
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
               	self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]


    def monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(10)


    def request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # To collect dp_id, pkt_count, byte_count
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        # To collect dp_id, port_no, rx_bytes, rx_pkts, tx_bytes, tx_pkts
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)     
        datapath.send_msg(req)


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        file = open("FlowStatsfile.txt","a+")
        file1=open("FlowStatsfile_target.txt","a+")
        self.logger.info('datapath         in-port  eth-dst           out-port packets  bytes')
        self.logger.info('---------------- -------- ----------------- -------- -------- --------')
        for stat in sorted([flow for flow in body if (flow.priority == 1) ], key=lambda flow: 
            (flow.match['in_port'],flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',ev.msg.datapath.id,stat.match['in_port'], 
                stat.match['eth_dst'],stat.instructions[0].actions[0].port,stat.packet_count, stat.byte_count)
            file.write("\n"+str(ev.msg.datapath.id) + ","+ str(stat.match['in_port'])+ "," + 
                str(stat.match['eth_dst'])+ "," + str(stat.packet_count) + "," + str(stat.byte_count))
            file1.write("\n0")
        file.close()
        file1.close()



    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        file = open("PortStatsfile.txt","a+")
        file1 = open("PortStatsfile_target.txt","a+")
        self.logger.info('datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- -------- -------- -------- -------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            if stat.port_no <= 10:
                self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
          
                file.write("\n{},{},{},{},{},{}".format(ev.msg.datapath.id, stat.port_no, stat.rx_bytes,
                 stat.rx_packets, stat.tx_bytes, stat.tx_packets))
                file1.write("\n0")          

        file.close()
        file1.close()




