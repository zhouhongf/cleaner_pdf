from mycleaners.base import Cleaner, ManualTable, ManualText


class SzrcbTable(ManualTable):
    table_labels_config = {}


class SzrcbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class SzrcbCleaner(Cleaner):
    name = 'SzrcbCleaner'
    bank_name = '苏农银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = SzrcbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = SzrcbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    SzrcbCleaner.start()
