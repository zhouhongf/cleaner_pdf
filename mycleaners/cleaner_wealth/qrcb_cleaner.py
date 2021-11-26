from mycleaners.base import Cleaner, ManualTable, ManualText


class QrcbTable(ManualTable):
    table_labels_config = {}


class QrcbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class QrcbCleaner(Cleaner):
    name = 'QrcbCleaner'
    bank_name = '青农银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = QrcbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = QrcbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    QrcbCleaner.start()
