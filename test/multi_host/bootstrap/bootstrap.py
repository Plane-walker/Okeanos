from importlib.abc import Loader
import pandas as pd
import socket
import sys
import yaml
import subprocess
import os
import csv
import shutil

def write_dock_yaml(islands0, lanes0, lanes1, lanes2, node_id):
    dock_yaml_path = '/root/Okeanos/config/dock.yaml'
    default_yaml_path = '/root/Okeanos/dock/config/default_config.yaml'
    if not os.path.exists('/root/Okeanos/config'):
        os.makedirs('/root/Okeanos/config')
    if not os.path.exists(dock_yaml_path):
        shutil.copy(default_yaml_path, dock_yaml_path)
    with open(dock_yaml_path) as file:
        dock_yaml = yaml.load(file, Loader=yaml.Loader)
    index = 0 
    for island0 in islands0:   
        island0_host = island0.split(":", 1)[0]
        island0_port = island0.split(":", 1)[1]
        length = len(dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'])
        if island0_host == '0.0.0.0':
            dock_yaml['chain_manager']['chain']['island_0']['join'] = False
            dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'][index]['host'] = 'localhost'
            index = index + 1
            break
        else:
            dock_yaml['chain_manager']['chain']['island_0']['join'] = True
            if index < length:
                dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'][index]['host'] = island0_host
                dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'][index]['port'] = island0_port
            else:
                 dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'].append({'host': island0_host, 'port': island0_port})
        index = index + 1
    for x in range(index, len(dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'])):
           dock_yaml['chain_manager']['chain']['island_0']['persistent_peers'].pop(x) 

    index = 0
    for lane0 in lanes0:
        lane0_host = lane0.split(":", 1)[0]
        lane0_port = lane0.split(":", 1)[1]
        length = len(dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'])
        if lane0_host == '0.0.0.0':
            dock_yaml['chain_manager']['chain']['lane_0']['join'] = False
            dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'][0]['host'] = 'localhost'
            index = index + 1
            break
        else:
            dock_yaml['chain_manager']['chain']['lane_0']['join'] = True
            if index < length:
                dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'][0]['host'] = lane0_host
                dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'][0]['port'] = lane0_port
            else:
                dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'].append({'host': lane0_host, 'port': lane0_port})
        index = index + 1
    for x in range(index, len(dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'])):
           dock_yaml['chain_manager']['chain']['lane_0']['persistent_peers'].pop(x) 

    index = 0
    for lane1 in lanes1:
        lane1_host = lane1.split(":", 1)[0]
        lane1_port = lane1.split(":", 1)[1]
        length = len(dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'])
        if lane1_host == '0.0.0.0':
            dock_yaml['chain_manager']['chain']['lane_1']['join'] = False
            dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'][0]['host'] = 'localhost'
            index = index + 1
            break
        else:
            dock_yaml['chain_manager']['chain']['lane_1']['join'] = True
            if index < length:
                dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'][0]['host'] = lane1_host
                dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'][0]['port'] = lane1_port
            else:
                dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'].append({'host': lane1_host, 'port': lane1_port})
        index = index + 1
    for x in range(index, len(dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'])):
           dock_yaml['chain_manager']['chain']['lane_1']['persistent_peers'].pop(x)    

    index = 0
    for lane2 in lanes2:
        lane2_host = lane2.split(":", 1)[0]
        lane2_port = lane2.split(":", 1)[1]
        length = len(dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'])
        if lane2_host == '0.0.0.0':
            dock_yaml['chain_manager']['chain']['lane_2']['join'] = False
            dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'][0]['host'] = 'localhost'
            index = index + 1
            break
        else:
            dock_yaml['chain_manager']['chain']['lane_2']['join'] = True
            if index < length:
                dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'][0]['host'] = lane2_host
                dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'][0]['port'] = lane2_port
            else:
                dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'].append({'host': lane2_host, 'port': lane2_port})
        index = index + 1
    for x in range(index, len(dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'])):
           dock_yaml['chain_manager']['chain']['lane_2']['persistent_peers'].pop(x)
    
    dock_yaml['app']['app_id'] = node_id

    with open(dock_yaml_path, 'w') as file:
            yaml.dump(dock_yaml, file, default_flow_style=False, sort_keys=False)    

def get_bootstrap_ip(node_id):
    node_data = pd.read_csv('/root/node_ips.csv', header=None).values
    node_ips = {node_data[index, 0]: node_data[index, 1] for index in range(node_data.shape[0])}
    if node_id in ['okeanos001', 'okeanos002', 'okeanos003', 'okeanos004']:
        return [f"{node_ips['okeanos000']}:2663"], [f"{node_ips['okeanos000']}:2666"], [f"{node_ips['okeanos000']}:2669"], [f"{node_ips['okeanos000']}:2672"]
    elif node_id in ['okeanos006', 'okeanos007', 'okeanos008', 'okeanos009', 'okeanos010']:
        return [f"{node_ips['okeanos005']}:2663"], [f"{node_ips['okeanos005']}:2666"], [f"{node_ips['okeanos005']}:2669"], [f"{node_ips['okeanos005']}:2672"]
    elif node_id in ['okeanos012', 'okeanos013', 'okeanos014', 'okeanos015']:
        return [f"{node_ips['okeanos011']}:2663"], [f"{node_ips['okeanos011']}:2666"], [f"{node_ips['okeanos011']}:2669"], [f"{node_ips['okeanos011']}:2672"]
    elif node_id in ['okeanos017', 'okeanos018', 'okeanos019']:
        return [f"{node_ips['okeanos016']}:2663"], [f"{node_ips['okeanos016']}:2666"], [f"{node_ips['okeanos016']}:2669"], [f"{node_ips['okeanos016']}:2672"]
    elif node_id in ['okeanos021', 'okeanos022', 'okeanos023', 'okeanos024']:
        return [f"{node_ips['okeanos020']}:2663"], [f"{node_ips['okeanos020']}:2666"], [f"{node_ips['okeanos020']}:2669"], [f"{node_ips['okeanos020']}:2672"]
    elif node_id in ['okeanos026', 'okeanos027', 'okeanos028']:
        return [f"{node_ips['okeanos025']}:2663"], [f"{node_ips['okeanos025']}:2666"], [f"{node_ips['okeanos025']}:2669"], [f"{node_ips['okeanos025']}:2672"]
    elif node_id in ['okeanos030', 'okeanos031', 'okeanos032']:
        return [f"{node_ips['okeanos029']}:2663"], [f"{node_ips['okeanos029']}:2666"], [f"{node_ips['okeanos029']}:2669"], [f"{node_ips['okeanos029']}:2672"]
    elif node_id in ['okeanos000', 'okeanos011', 'okeanos020']:
        return [f"0.0.0.0:0"], [f"0.0.0.0:0"], [f"0.0.0.0:0"], [f"0.0.0.0:0"]
    elif node_id in ['okeanos029']:
        return [f"0.0.0.0:0"], [f"{node_ips['okeanos000']}:2669"], [f"{node_ips['okeanos000']}:2666"], [f"0.0.0.0:0"]
    elif node_id in ['okeanos005']:
        return [f"0.0.0.0:0"], [f"{node_ips['okeanos000']}:2672"], [f"{node_ips['okeanos011']}:2669"], [f"{node_ips['okeanos011']}:2666"]
    elif node_id in ['okeanos016']:
        return [f"0.0.0.0:0"], [f"{node_ips['okeanos011']}:2672"], [f"{node_ips['okeanos011']}:2669"], [f"{node_ips['okeanos020']}:2666"]
    elif node_id in ['okeanos025']:
        return [f"0.0.0.0:0"], [f"{node_ips['okeanos020']}:2672"], [f"{node_ips['okeanos000']}:2669"], [f"{node_ips['okeanos000']}:2666"]

if __name__ == '__main__':
    no_capture_output = '0'
    node_id = socket.gethostname()
    if len(sys.argv) == 1:
        islands, lane0s, lane1s, lane2s = get_bootstrap_ip(node_id)
    else:
        islands = []
        lane0s = []
        lane1s = []
        lane2s = []
        for island in sys.argv[1].split(','):
            islands.append(island)
        for lane0 in sys.argv[2].split(','):
            lane0s.append(lane0)
        for lane1 in sys.argv[3].split(','):
            lane1s.append(lane1)
        for lane2 in sys.argv[4].split(','):
            lane2s.append(lane2)
        node_id = sys.argv[5]
        if len(sys.argv) == 7:
            no_capture_output = sys.argv[6]
    write_dock_yaml(islands, lane0s, lane1s, lane2s, node_id)
    no_capture = ''
    if no_capture_output == '1':
        no_capture = '--no-capture-output'
    start_okeanos = f'cd /root/Okeanos;' \
                    f'conda run -n okeanos {no_capture} python main.py;'
    subprocess.run(start_okeanos, shell=True, stdout=subprocess.PIPE)
