from mycleaners.base import Cleaner, ManualTextOnly
import os
from utils.file_util import divide_html_text


class CmbcText(ManualTextOnly):
    labels_check_config = {}


class CmbcCleaner(Cleaner):
    name = 'CmbcCleaner'
    bank_name = '民生银行'

    async def divide_tables_text(self, filename):
        content_type = os.path.splitext(filename)[-1]
        tables, text = None, None
        try:
            if content_type == '.html' or content_type == '.htm' or content_type == '.shtml' or content_type == '.shtm':
                text = divide_html_text(filename)
            else:
                print('============================ 特殊文件类型，无法解析: %s ================================' % filename)
        except Exception as e:
            self.logger.error('提取%s文件内容时出错：%s' % (filename, e))
        return tables, text

    async def parse_manual(self, ukey, tables, text):
        dict_wealth = CmbcText.start(self.bank_name, ukey, text, self.collection_outline)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CmbcCleaner.start()
