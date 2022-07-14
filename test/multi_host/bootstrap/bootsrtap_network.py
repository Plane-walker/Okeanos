import paramiko
import pandas as pd
import io
import time
from concurrent import futures


def bootstrap_nodes(node_ips, private_key, node_list):
    with futures.ThreadPoolExecutor(max_workers=len(node_list)) as pool:
        for node_id in node_list:
            def bootstrap():
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=node_ips[node_id], port=22, username='root', pkey=private_key)
                ftp_client = ssh.open_sftp()
                ftp_client.put('node_ips.csv', 'node_ips.csv')
                stdin, stdout, stderr = ssh.exec_command(f'systemctl start okeanos.service')
                stdout.channel.recv_exit_status()
                stdin, stdout, stderr = ssh.exec_command(f'while [ ! -d /root/lane_2 ]; do continue; done')
                stdout.channel.recv_exit_status()
                ssh.close()
                time.sleep(12)
            pool.submit(bootstrap)
    print(f'{node_list} started')


def main():
    with open('sk.pem', 'r') as file:
        sk = file.read()
    key_file = io.StringIO(sk)
    private_key = paramiko.RSAKey.from_private_key(key_file)
    node_data = pd.read_csv('node_ips.csv', header=None).values
    node_ips = {node_data[index, 0]: node_data[index, 1] for index in range(node_data.shape[0])}
    bootstrap_nodes(node_ips, private_key, ['okeanos000', 'okeanos011', 'okeanos020'])
    bootstrap_nodes(node_ips, private_key, ['okeanos001', 'okeanos002', 'okeanos003', 'okeanos004', 'okeanos012', 'okeanos013', 'okeanos014', 'okeanos015', 'okeanos021', 'okeanos022', 'okeanos023', 'okeanos024'])
    bootstrap_nodes(node_ips, private_key, ['okeanos029'])
    bootstrap_nodes(node_ips, private_key, ['okeanos030', 'okeanos031', 'okeanos032'])
    bootstrap_nodes(node_ips, private_key, ['okeanos005'])
    bootstrap_nodes(node_ips, private_key, ['okeanos006', 'okeanos007', 'okeanos008', 'okeanos009', 'okeanos010'])
    bootstrap_nodes(node_ips, private_key, ['okeanos016'])
    bootstrap_nodes(node_ips, private_key, ['okeanos017', 'okeanos018', 'okeanos019'])
    bootstrap_nodes(node_ips, private_key, ['okeanos025'])
    bootstrap_nodes(node_ips, private_key, ['okeanos026', 'okeanos027', 'okeanos028'])


if __name__ == '__main__':
    main()
