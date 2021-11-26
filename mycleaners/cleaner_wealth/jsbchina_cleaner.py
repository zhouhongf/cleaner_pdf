from mycleaners.base import Cleaner, ManualTable, ManualText


class JsbchinaTable(ManualTable):
    table_labels_config = {}


class JsbchinaText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class JsbchinaCleaner(Cleaner):
    name = 'JsbchinaCleaner'
    bank_name = '江苏银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = JsbchinaTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = JsbchinaText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    JsbchinaCleaner.start()
