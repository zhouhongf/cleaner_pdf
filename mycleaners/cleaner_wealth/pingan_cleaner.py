from mycleaners.base import Cleaner, ManualTable, ManualTextOnly
import os
from utils.file_util import pdf_to_string


class PinganTable(ManualTable):
    table_labels_config = {}


class PinganText(ManualTextOnly):
    labels_check_config = {}


class PinganCleaner(Cleaner):
    name = 'PinganCleaner'
    bank_name = '平安银行'

    async def divide_tables_text(self, filename):
        content_type = os.path.splitext(filename)[-1]
        tables, text = None, None
        try:
            if content_type == '.pdf':
                text = pdf_to_string(filename)
            else:
                print('============================ 特殊文件类型，无法解析: %s ================================' % filename)
        except Exception as e:
            self.logger.error('提取%s文件内容时出错：%s' % (filename, e))
        return tables, text

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = PinganText.start(self.bank_name, ukey, text, self.collection_outline)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    PinganCleaner.start()
