from mycleaners.base import Cleaner, ManualTable, ManualText


class ZzbankTable(ManualTable):
    table_labels_config = {}


class ZzbankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class ZzbankCleaner(Cleaner):
    name = 'ZzbankCleaner'
    bank_name = '郑州银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = ZzbankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = ZzbankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    ZzbankCleaner.start()
