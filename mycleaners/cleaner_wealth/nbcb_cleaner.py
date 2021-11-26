from mycleaners.base import Cleaner, ManualTable, ManualText


class NbcbTable(ManualTable):
    table_labels_config = {}


class NbcbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class NbcbCleaner(Cleaner):
    name = 'NbcbCleaner'
    bank_name = '宁波银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = NbcbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = NbcbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    NbcbCleaner.start()
