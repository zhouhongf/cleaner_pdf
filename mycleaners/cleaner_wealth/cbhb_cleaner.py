from mycleaners.base import Cleaner, ManualTable, ManualText
from config import Wealth
import re


class CbhbTable(ManualTable):
    table_labels_config = {}


class CbhbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}

    def parse_text_manual(self, wealth: Wealth):
        if not wealth.code_register:
            result = re.compile(r'[A-Z][0-9]{13}|[A-Z0-9]{14}').search(self.text)
            if result:
                wealth.code_register = result.group(0)
        return wealth


class CbhbCleaner(Cleaner):
    name = 'CbhbCleaner'
    bank_name = '渤海银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = CbhbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = CbhbText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CbhbCleaner.start()
