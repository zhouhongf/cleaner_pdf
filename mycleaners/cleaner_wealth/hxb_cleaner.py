from mycleaners.base import Cleaner, ManualTable, ManualText


class HxbTable(ManualTable):
    table_labels_config = {}


class HxbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class HxbCleaner(Cleaner):
    name = 'HxbCleaner'
    bank_name = '华夏银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = HxbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = HxbText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    HxbCleaner.start()
