from mycleaners.base import Cleaner, ManualTable, ManualText


class BankofbeijingTable(ManualTable):
    table_labels_config = {}


class BankofbeijingText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class BankofbeijingCleaner(Cleaner):
    name = 'BankofbeijingCleaner'
    bank_name = '北京银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = BankofbeijingTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = BankofbeijingText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    BankofbeijingCleaner.start()
