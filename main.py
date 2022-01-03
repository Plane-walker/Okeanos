import os
import shutil
from dock import Dock

if __name__ == '__main__':
    if not os.path.exists('config'):
        os.makedirs('config')
    if not os.path.exists('config/dock.yaml'):
        shutil.copy('dock/config/default_config.yaml', 'config/dock.yaml')
    current_path = os.path.dirname(__file__)
    dock_config_path = os.path.join(current_path, 'config/dock.yaml')
    dock = Dock(dock_config_path)
    dock.run()
