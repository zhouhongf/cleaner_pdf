from mycleaners.base import Cleaner, ManualTable, ManualText
import aiofiles


class IcbcTable(ManualTable):
    table_labels_config = {}


class IcbcText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class IcbcCleaner(Cleaner):
    name = 'IcbcCleaner'
    bank_name = '工商银行'      # 如果没有定义bank_name，则从start_bank_name方法启动

    async def start_bank_name(self):
        ukey = '工商银行=20GS1815'
        content_type = '.pdf'
        async with aiofiles.open(ukey + content_type, 'rb') as f:
            content = await f.read()
        manual_in = self.Manual(ukey=ukey, content=content, content_type=content_type)
        yield manual_in

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = IcbcTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('一解析的内容是：%s' % dict_wealth)
        dict_wealth = IcbcText.start(self.bank_name, dict_wealth, text)
        # print('二解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    IcbcCleaner.start()



