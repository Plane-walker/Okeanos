import os
import shutil
from dock import Dock
from log import init_log

if __name__ == '__main__':
    if not os.path.exists('config'):
        os.makedirs('config')
    if not os.path.exists('config/dock.yaml'):
        shutil.copy('dock/config/default_config.yaml', 'config/dock.yaml')
    init_log()
    current_path = os.path.dirname(__file__)
    dock_config_path = os.path.join(current_path, 'config/dock.yaml')
    dock = Dock(dock_config_path)
    dock.run()
