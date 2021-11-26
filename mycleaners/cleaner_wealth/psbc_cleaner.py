from mycleaners.base import Cleaner, ManualTable, ManualTextOnly
import os
from utils.file_util import pdf_to_string
from config import Wealth
import re


class PsbcTextOnly(ManualTextOnly):
    labels_check_config = {}

    def parse_text_manual(self, wealth: Wealth):
        name = wealth.name
        bank_name = '中国邮政储蓄银行'
        name_right = bank_name + name.split(bank_name)[-1]
        wealth.name = name_right

        if not wealth.code_register:
            result = re.compile(r'[A-Z][0-9]{13}|[A-Z0-9]{14}').search(self.text)
            if result:
                wealth.code_register = result.group(0)
        return wealth


class PsbcCleaner(Cleaner):
    name = 'PsbcCleaner'
    bank_name = '邮储银行'

    async def divide_tables_text(self, filename):
        content_type = os.path.splitext(filename)[-1]
        tables, text = None, None
        try:
            if content_type == '.pdf':
                text = pdf_to_string(filename)
            else:
                print('============================ 特殊文件类型，无法解析: %s ================================' % filename)
        except Exception as e:
            self.logger.error('提取%s文件内容时出错：%s' % (filename, e))
        return tables, text

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = PsbcTextOnly.start(self.bank_name, ukey, text, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    PsbcCleaner.start()
