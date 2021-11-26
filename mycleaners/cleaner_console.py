import os
import time
from config import Config
from config import Logger
from importlib import import_module

work_list = {
    '工商银行': 'icbc',
    '农业银行': 'abchina',
    '中国银行': 'boc',
    '建设银行': 'ccb',
    '交通银行': 'bankcomm',
    '邮储银行': 'psbc',

    '招商银行': 'cmbchina',
    '中信银行': 'citicbank',
    '浦发银行': 'spdb',
    '兴业银行': 'cib',
    '广发银行': 'cgbchina',
    '民生银行': 'cmbc',
    '光大银行': 'cebbank',
    '浙商银行': 'czbank',
    '平安银行': 'pingan',
    '华夏银行': 'hxb',
    '渤海银行': 'cbhb',
    '恒丰银行': 'hfbank'
}


def file_name(file_dir=os.path.join(Config.BASE_DIR, 'mycleaners/cleaner_wealth')):
    bank_alias = work_list.values()
    all_files = []
    for file in os.listdir(file_dir):
        if file.endswith('_cleaner.py') and file.replace('_cleaner.py', '') in bank_alias:
            all_files.append(file.replace('.py', ''))
    return all_files


def cleaner_console():
    start = time.time()
    all_files = file_name()

    for cleaner in all_files:
        cleaner_module = import_module("mycleaners.cleaner_wealth.{}".format(cleaner))
        cleaner_module.start()

    logger = Logger(level='warning').logger
    logger.info("Time costs: {0}".format(time.time() - start))


if __name__ == '__main__':
    cleaner_console()
