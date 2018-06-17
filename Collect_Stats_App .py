# Collect Statistic Model

from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

class CollectStatsApp(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(CollectStatsApp, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

        file = open("FlowStatsfile.txt","a+")
        file.write('dp_id,packets,bytes')
        file.close()

        file = open("PortStatsfile.txt","a+")
        file.write('dp_id,port_no,rx_bytes,rx_pkts,tx_bytes,tx_pkts')
        file.close()

        file = open("GroupStatsfile.txt","a+")
        file.write('group_id,byte_count,packet_count')
        file.close()

        #current_port_byte_count = 0/ ""
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath

        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)      #. dp_id, pkt_count, byte_count
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)     # dp_id, port_no, rx_bytes, rx_pkts, tx_bytes, tx_pkts
        datapath.send_msg(req)

        req = parser.OFPGroupStatsRequest(datapath, 0, ofproto.OFPG_ALL)        # group_id, byte_count, packet_count
        datapath.send_msg(req)

        #req = ofp_parser.OFPMeterStatsRequest(datapath, 0, ofproto.OFPM_ALL)
        #datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        file = open("FlowStatsfile.txt","a+")
        self.logger.info('datapath         in-port  eth-dst           out-port packets  bit')
        self.logger.info('---------------- -------- ----------------- -------- ------- -----')
        for stat in sorted([flow for flow in body if flow.priority == 1], key=lambda flow: (flow.match['in_port'],flow.match['eth_dst'])):

            self.logger.info('%016x %8x %17s %8x %8d %8d',ev.msg.datapath.id,stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,(stat.packet_count), (stat.byte_count))

            file.write("\n"+str(ev.msg.datapath.id) + "," + str(stat.packet_count) + "," + str(stat.byte_count))

        file.close()

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        file = open("PortStatsfile.txt","a+")
        self.logger.info('datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- -------- -------- -------- -------- -------- --------')


        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                                ev.msg.datapath.id, stat.port_no,
                                stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                                stat.tx_packets, stat.tx_bytes, stat.tx_errors)

            file.write("\n"+str(ev.msg.datapath.id) + "," + str(stat.port_no) +
                                "," + str(stat.rx_bytes)+ "," + str(stat.rx_packets) + ","
                                + str(stat.tx_bytes) + "," + str(stat.tx_packets))
	    file.close()

    @set_ev_cls(ofp_event.EventOFPGroupStatsReply, MAIN_DISPATCHER)
    def group_stats_reply_handler(self, ev):
        groups = []
        file = open("GroupStatsfile.txt","a+")
        for stat in ev.msg.body:
            groups.append('length=%d group_id=%d ref_count=%d packet_count=%d byte_count=%d duration_sec=%d duration_nsec=%d' %
                      (stat.length, stat.group_id,stat.ref_count, stat.packet_count,stat.byte_count, stat.duration_sec,stat.duration_nsec))
            file.write("\n"+str(stat.group_id) + " " + str(stat.byte_count) + " " + str(stat.packet_count))
        self.logger.debug('GroupStats: %s', groups)
        file.close()
