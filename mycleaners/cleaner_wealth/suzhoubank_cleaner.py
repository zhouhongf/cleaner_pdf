from mycleaners.base import Cleaner, ManualTable, ManualText


class SuzhoubankTable(ManualTable):
    table_labels_config = {}


class SuzhoubankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class SuzhoubankCleaner(Cleaner):
    name = 'QrcbCleaner'
    bank_name = '苏州银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = SuzhoubankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = SuzhoubankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    SuzhoubankCleaner.start()
