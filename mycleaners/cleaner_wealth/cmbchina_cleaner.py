from config import Wealth
from mycleaners.base import Cleaner, ManualTable, ManualText
from utils.nlp_util import parse_regex
import re


class CmbchinaTable(ManualTable):
    table_labels_config = {}


class CmbchinaText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class CmbchinaCleaner(Cleaner):
    name = 'CmbchinaCleaner'
    bank_name = '招商银行'

    async def parse_manual(self, ukey, tables, text):
        # print('解析出来的文字内容是：%s' % text)
        dict_wealth = CmbchinaTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = CmbchinaText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CmbchinaCleaner.start()




