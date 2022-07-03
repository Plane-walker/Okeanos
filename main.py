import os
import shutil
from dock import Dock
from log import init_log

if __name__ == '__main__':
    current_path = os.path.dirname(__file__)
    config_path = os.path.join(current_path, '..', 'config')
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    dock_config_path = os.path.join(config_path, 'dock.yaml')
    if not os.path.exists(dock_config_path):
        shutil.copy('dock/config/default_config.yaml', dock_config_path)
    init_log(dock_config_path)
    dock = Dock(dock_config_path)
    dock.run()
