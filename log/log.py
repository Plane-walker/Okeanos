__all__ = [
    'log',
    'init_log',
]


import os
import sys
import logging
import logging.handlers
import multiprocessing


def listener_configurer():
    formatter = logging.Formatter(
        '%(asctime)s %(processName)-11s tid-%(thread)-16d %(levelname)8s: %(message)s (%(funcName)s)'
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


def listener_process(queue, configurer):
    configurer()
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


def run_log_lisener_process(queue):
    listener = multiprocessing.Process(
        target=listener_process,
        args=(queue, listener_configurer)
    )
    listener.start()


def init_log():
    queue = multiprocessing.Queue(-1)
    run_log_lisener_process(queue)
    h = logging.handlers.QueueHandler(queue)
    log = logging.getLogger()
    log.addHandler(h)
    log.setLevel(logging.DEBUG)


log = logging.getLogger()
