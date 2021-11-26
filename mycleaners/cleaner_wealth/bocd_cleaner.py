from mycleaners.base import Cleaner, ManualTable, ManualText


class BocdTable(ManualTable):
    table_labels_config = {}


class BocdText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class BocdCleaner(Cleaner):
    name = 'BocdCleaner'
    bank_name = '成都银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = BocdTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = BocdText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    BocdCleaner.start()
