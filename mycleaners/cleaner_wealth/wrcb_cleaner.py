from mycleaners.base import Cleaner, ManualTable, ManualText


class WrcbTable(ManualTable):
    table_labels_config = {}


class WrcbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class WrcbCleaner(Cleaner):
    name = 'WrcbCleaner'
    bank_name = '无锡银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = WrcbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = WrcbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    WrcbCleaner.start()
