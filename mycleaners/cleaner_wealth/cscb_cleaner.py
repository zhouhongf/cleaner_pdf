from mycleaners.base import Cleaner, ManualTable, ManualText


class CscbTable(ManualTable):
    table_labels_config = {}


class CscbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class CscbCleaner(Cleaner):
    name = 'CscbCleaner'
    bank_name = '长沙银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = CscbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = CscbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CscbCleaner.start()
