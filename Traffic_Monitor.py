from operator import attrgetter
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

class SimpleTrafficMonitor(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleTrafficMonitor, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    # Handling Asynchronous messages
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        tmFile = open("tmFile.txt","a+")
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                tmFile.write('register datapath: ' + str(datapath.id))
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                tmFile.write('unregister datapath: '+ str(datapath.id))
                del self.datapaths[datapath.id]
		tmFile.close()

    # Monitoring and collecting statistic information
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

        req = parser.OFPGroupStatsRequest(datapath, 0, ofp.OFPG_ALL)
        datapath.send_msg(req)

        req = ofp_parser.OFPMeterStatsRequest(datapath, 0, ofp.OFPM_ALL)
        datapath.send_msg(req)

    
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        '''body = ev.msg.body

        tmFile = open("tmFile.txt","a+")
        self.logger.info('datapath         in-port  eth-dst           out-port packets  bytes')
        self.logger.info('---------------- -------- ----------------- -------- -------- --------')
        tmFile.write('datapath         in-port  eth-dst           out-port packets  bytes')
        tmFile.write('---------------- -------- ----------------- -------- -------- --------')
        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.logger.info('%016x %8x %17s %8x %8d %8d',
                             ev.msg.datapath.id,
                             stat.match['in_port'], stat.match['eth_dst'],
                             stat.instructions[0].actions[0].port,
                             stat.packet_count, stat.byte_count)
            tmFile.write(
                             str(ev.msg.datapath.id)+" "+
                             str(stat.match['in_port'])+" "+ str(stat.match['eth_dst'])+ " "+
                             str(stat.instructions[0].actions[0].port)+ " "+
                             str(stat.packet_count)+ " "+ str(stat.byte_count))
        tmFile.close()'''
        tmFile = open("tmFile.txt","a+")
        flows = []
        for stat in ev.msg.body:
            flows.append('table_id=%s '
                     'duration_sec=%d duration_nsec=%d '
                     'priority=%d '
                     'idle_timeout=%d hard_timeout=%d flags=0x%04x '
                     'cookie=%d packet_count=%d byte_count=%d '
                     'match=%s instructions=%s' %
                     (stat.table_id,
                      stat.duration_sec, stat.duration_nsec,
                      stat.priority,
                      stat.idle_timeout, stat.hard_timeout, stat.flags,
                      stat.cookie, stat.packet_count, stat.byte_count,
                      stat.match, stat.instructions))
        self.logger.debug('FlowStats: %s', flows)
        tmFile.write(str(flows))
        tmFile.close()

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        tmFile = open("tmFile.txt","a+")
        self.logger.info('datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error')
        self.logger.info('---------------- -------- -------- -------- -------- -------- -------- --------')
        tmFile.write('datapath         port     rx-pkts  rx-bytes rx-error tx-pkts  tx-bytes tx-error')
        tmFile.write('---------------- -------- -------- -------- -------- -------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no,
                             stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            tmFile.write(
                             str(ev.msg.datapath.id)+" "+ str(stat.port_no) + " "+
                             str(stat.rx_packets)+" "+ str(stat.rx_bytes)+" "+ str(stat.rx_errors)+ " "+
                             str(stat.tx_packets)+ " "+ str(stat.tx_bytes)+" "+ str(stat.tx_errors))
	    tmFile.close()

    @set_ev_cls(ofp_event.EventOFPGroupStatsReply, MAIN_DISPATCHER)
    def group_stats_reply_handler(self, ev):
        tmFile = open("tmFile.txt","a+")
        groups = []
        for stat in ev.msg.body:
            groups.append('length=%d group_id=%d '
                      'ref_count=%d packet_count=%d byte_count=%d '
                      'duration_sec=%d duration_nsec=%d' %
                      (stat.length, stat.group_id,
                       stat.ref_count, stat.packet_count,
                       stat.byte_count, stat.duration_sec,
                       stat.duration_nsec))
        self.logger.debug('GroupStats: %s', groups)
        tmFile.write(str(groups))
        tmFile.close()

    @set_ev_cls(ofp_event.EventOFPMeterStatsReply, MAIN_DISPATCHER)
    def meter_stats_reply_handler(self, ev):
        tmFile = open("tmFile.txt","a+")
        meters = []
        for stat in ev.msg.body:
            meters.append('meter_id=0x%08x len=%d flow_count=%d '
                      'packet_in_count=%d byte_in_count=%d '
                      'duration_sec=%d duration_nsec=%d '
                      'band_stats=%s' %
                      (stat.meter_id, stat.len, stat.flow_count,
                       stat.packet_in_count, stat.byte_in_count,
                       stat.duration_sec, stat.duration_nsec,
                       stat.band_stats))
        self.logger.debug('MeterStats: %s', meters)
        tmFile.write(str(meters))
        tmFile.close()