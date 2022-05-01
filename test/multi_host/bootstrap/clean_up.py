import subprocess


clean_up = f'kill -9 $(lsof -t -i:2663 -i:2664 -i:2665 -i:2666 -i:2667  -i:2668 -i:2669 -i:2670 -i:2671 -i:2672 -i:2673 -i:2674);' \
                f'rm -rf /root/island_*;' \
                f'rm -rf /root/logs;' \
                f'rm -rf /root/lane_*;'
subprocess.run(clean_up, shell=True, stdout=subprocess.PIPE)
