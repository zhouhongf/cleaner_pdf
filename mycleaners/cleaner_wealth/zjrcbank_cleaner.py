from mycleaners.base import Cleaner, ManualTable, ManualText


class ZjrcbankTable(ManualTable):
    table_labels_config = {}


class ZjrcbankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class ZjrcbankCleaner(Cleaner):
    name = 'ZjrcbankCleaner'
    bank_name = '紫金银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = ZjrcbankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = ZjrcbankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    ZjrcbankCleaner.start()
