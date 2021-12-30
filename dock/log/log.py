__all__ = [
    'log',
]


import os
import logging


formatter = logging.Formatter(
    '%(asctime)s Thread-%(thread)-16d%(levelname)9s: %(message)s (%(funcName)s)'
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

path = os.path.dirname(__file__)
path = os.path.join(path, 'logs')

log_path = os.path.join(path, 'error.log')
error_file_handler = logging.FileHandler(log_path)
error_file_handler.setFormatter(formatter)
error_file_handler.setLevel(logging.ERROR)

log_path = os.path.join(path, 'info.log')
info_file_handler = logging.FileHandler(log_path)
info_file_handler.setFormatter(formatter)
info_file_handler.setLevel(logging.INFO)

log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(stream_handler)
log.addHandler(error_file_handler)
log.addHandler(info_file_handler)
