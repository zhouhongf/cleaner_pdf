from mycleaners.base import Cleaner, ManualTable, ManualText


class CsrcbankTable(ManualTable):
    table_labels_config = {}


class CsrcbankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class CsrcbankCleaner(Cleaner):
    name = 'CsrcbankCleaner'
    bank_name = '常熟银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = CsrcbankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = CsrcbankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CsrcbankCleaner.start()
