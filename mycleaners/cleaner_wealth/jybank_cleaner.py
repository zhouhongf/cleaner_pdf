from mycleaners.base import Cleaner, ManualTable, ManualText


class JybankTable(ManualTable):
    table_labels_config = {}


class JybankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class JybankCleaner(Cleaner):
    name = 'JybankCleaner'
    bank_name = '江阴银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = JybankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = JybankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    JybankCleaner.start()
