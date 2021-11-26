from mycleaners.base import Cleaner, ManualTable, ManualText



class CcbTable(ManualTable):
    table_labels_config = {}


class CcbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class CcbCleaner(Cleaner):
    name = 'CcbCleaner'
    bank_name = '建设银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = CcbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = CcbText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CcbCleaner.start()
