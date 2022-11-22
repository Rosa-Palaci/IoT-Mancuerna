#!/usr/bin/python

'Example of UAVs represented as stations using CoppeliaSim'

import time
import os

from mininet.log import setLogLevel, info
from mn_wifi.link import wmediumd, adhoc
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mn_wifi.telemetry import telemetry
from mn_wifi.wmediumdConnector import interference
from mn_wifi.link import Intf


def topology():

    "Create a network."
    net = Mininet_wifi(link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    dr1 = net.addStation('dr1', mac='00:00:00:00:00:01', ip='10.0.0.1/8',
                         position='30,60,0')
    dr2 = net.addStation('dr2', mac='00:00:00:00:00:02', ip='10.0.0.2/8',
                         position='70,30,0')
    dr3 = net.addStation('dr3', mac='00:00:00:00:00:03', ip='10.0.0.3/8',
                         position='10,20,0')
    h1 = net.addStation('h1', mac='00:00:00:00:00:04', ip='10.0.0.4/8', 
                        position='50,50,0')

    net.setPropagationModel(model="logDistance", exp=4.5)

    info("*** Configuring nodes\n")
    net.configureNodes()

    net.addLink(dr1, cls=adhoc, intf='dr1-wlan0',
                ssid='adhocNet', proto='batman_adv',
                mode='g', channel=5, ht_cap='HT40+')

    net.addLink(dr2, cls=adhoc, intf='dr2-wlan0',
                ssid='adhocNet', proto='batman_adv',
                mode='g', channel=5, ht_cap='HT40+')

    net.addLink(dr3, cls=adhoc, intf='dr3-wlan0',
                ssid='adhocNet', proto='batman_adv',
                mode='g', channel=5, ht_cap='HT40+')

    net.addLink(h1, cls=adhoc, intf='h1-wlan0',
                ssid='adhocNet', proto='batman_adv',
                mode='g', channel=5, ht_cap='HT40+')

    info("*** Starting network\n")
    net.build()

    nodes = net.stations
    telemetry(nodes=nodes, single=True, data_type='position')

    sta_drone = []
    for n in net.stations:
        sta_drone.append(n.name)
    sta_drone_send = ' '.join(map(str, sta_drone))
    sta_drone_send = 'dr1 dr2 dr3'

    # # set_socket_ip: localhost must be replaced by ip address
    # # of the network interface of your system
    # # The same must be done with socket_client.py
    info("*** Starting Socket Server\n")
    net.socketServer(ip='127.0.0.1', port=12345)

    info("*** Starting CoppeliaSim\n")
    path = os.path.dirname(os.path.abspath(__file__))
    os.system('{}/CoppeliaSim_Edu_V4_1_0_Ubuntu/coppeliaSim.sh -s {}'
              '/simulation.ttt -gGUIITEMS_2 &'.format(path, path))
    time.sleep(10)

    info("*** Perform a simple test\n")
    simpleTest = 'python {}/simpleTest.py '.format(path) + sta_drone_send + ' &'
    os.system(simpleTest)

    time.sleep(5)

    info("*** Configure the node position\n")
    setNodePosition = 'python {}/setNodePosition.py '.format(path) + sta_drone_send + ' &'
    os.system(setNodePosition)

    info("*** Add Example node connected to physical interface\n")
    info( '*** Adding controller\n' )
    net.addController(name='c0')

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1')
    Intf( 'enp0s3', node=s1 )

    info( '*** Add hosts\n')

    info( '*** Add links\n')
    net.addLink(h1, s1)

    info( '*** Starting network\n')
    net.start()
    # Get ip to the internet on h1
    h1.cmdPrint('dhclient h1-eth1')
    # Allow h1 to function as router
    h1.cmdPrint('sysctl -w net.ipv4.ip_forward=1')
    # Use NAT to forward drones to the internet
    h1.cmdPrint('iptables -t nat -A POSTROUTING -o h1-eth1 -j MASQUERADE')
    
    # Add h1 as default gateways to drones
    dr1.cmdPrint('route add default gw 10.0.0.4')
    dr2.cmdPrint('route add default gw 10.0.0.4')
    dr3.cmdPrint('route add default gw 10.0.0.4')

    # Run mosquitto central on h1
    h1.cmdPrint('mosquitto -c ./examples/uav/central_mosquitto.conf -v -d')

    # Run mosquittos bridges on drones
    dr1.cmdPrint('mosquitto -c ./examples/uav/bridge1_central.conf -v -d')
    dr2.cmdPrint('mosquitto -c ./examples/uav/bridge1_central.conf -v -d')
    dr3.cmdPrint('mosquitto -c ./examples/uav/bridge1_central.conf -v -d')

    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    kill_process()
    net.stop()


def kill_process():
    os.system('pkill -9 -f coppeliaSim')
    os.system('pkill -9 -f simpleTest.py')
    os.system('pkill -9 -f setNodePosition.py')
    os.system('rm examples/uav/data/*')


if __name__ == '__main__':
    setLogLevel('info')
    # Killing old processes
    kill_process()
    topology()
