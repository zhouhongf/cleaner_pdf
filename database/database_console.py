from importlib import import_module
from config import Logger
import time


def database_console():
    start = time.time()

    mongodb_module = import_module("database.backends.mongo_database")
    mongodb_module.send_database()

    logger = Logger(level='warning').logger
    logger.info("Time costs: {0}".format(time.time() - start))


if __name__ == '__main__':
    database_console()
