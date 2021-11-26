from mycleaners.base import Cleaner, ManualTable, ManualText


class QdccbTable(ManualTable):
    table_labels_config = {}


class QdccbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class QdccbCleaner(Cleaner):
    name = 'QdccbCleaner'
    bank_name = '青岛银行'

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = QdccbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = QdccbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    QdccbCleaner.start()
