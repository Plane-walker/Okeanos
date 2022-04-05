__all__ = [
    'log',
    'init_log',
]


import os
import sys
import yaml
import logging
import logging.handlers
import multiprocessing


def listener_configurer(config_path):
    formatter = logging.Formatter(
        '%(asctime)s %(processName)-11s tid-%(thread)-16d %(levelname)8s: %(message)s (%(funcName)s)'
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    with open(config_path) as file:
        config = yaml.load(file, Loader=yaml.Loader)
    path = config['log']['base_path']
    path = os.path.join(path, 'lane_logs')
    if not os.path.exists(path):
        os.makedirs(path)

    log_path = os.path.join(path, 'error.log')
    error_file_handler = logging.FileHandler(log_path)
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    log_path = os.path.join(path, 'info.log')
    info_file_handler = logging.FileHandler(log_path)
    info_file_handler.setFormatter(formatter)
    info_file_handler.setLevel(logging.INFO)

    log_path = os.path.join(path, 'debug.log')
    debug_file_handler = logging.FileHandler(log_path)
    debug_file_handler.setFormatter(formatter)
    debug_file_handler.setLevel(logging.DEBUG)

    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(stream_handler)
    log.addHandler(error_file_handler)
    log.addHandler(info_file_handler)
    log.addHandler(debug_file_handler)


def listener_process(queue, configurer, config_path):
    configurer(config_path)
    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import traceback
            print('Whoops! Problem:', file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def run_log_lisener_process(queue, config_path):
    listener = multiprocessing.Process(
        target=listener_process,
        args=(queue, listener_configurer, config_path)
    )
    listener.start()


def init_log(config_path):
    queue = multiprocessing.Queue(-1)
    run_log_lisener_process(queue, config_path)
    h = logging.handlers.QueueHandler(queue)
    log = logging.getLogger()
    log.addHandler(h)
    log.setLevel(logging.DEBUG)


log = logging.getLogger()
