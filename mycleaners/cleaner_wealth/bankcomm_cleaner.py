from mycleaners.base import Cleaner, ManualTable, ManualText


class BankcommTable(ManualTable):
    table_labels_config = {}


class BankcommText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class BankcommCleaner(Cleaner):
    name = 'BankcommCleaner'
    bank_name = '交通银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = BankcommTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = BankcommText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    BankcommCleaner.start()
