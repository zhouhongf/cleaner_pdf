from mycleaners.base import Cleaner, ManualTable, ManualText


class HfbankTable(ManualTable):
    table_labels_config = {}


class HfbankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class HfbankCleaner(Cleaner):
    name = 'HfbankCleaner'
    bank_name = '恒丰银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = HfbankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = HfbankText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    HfbankCleaner.start()
