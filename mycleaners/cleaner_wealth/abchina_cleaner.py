from mycleaners.base import Cleaner, ManualTextOnly
import re
import pdfplumber
import os


class AbchinaTextOnly(ManualTextOnly):
    labels_check_config = {}


class AbchinaCleaner(Cleaner):
    name = 'AbchinaCleaner'
    bank_name = '农业银行'

    async def divide_tables_text(self, filename):
        content_type = os.path.splitext(filename)[-1]
        tables, text = None, None
        try:
            if content_type == '.pdf':
                tables, text = self.divide_pdf_tables_text(filename)
            else:
                print('============================ 特殊文件类型，无法解析: %s ================================' % filename)
        except Exception as e:
            self.logger.error('提取%s文件内容时出错：%s' % (filename, e))
        return tables, text

    def divide_pdf_tables_text(self, path):
        with pdfplumber.open(path) as pdf:
            tables_text = ''
            text = ''
            for page in pdf.pages:
                tables = page.find_tables()
                words = page.extract_words()
                words_left = ''
                if tables:
                    words_left_page = ''
                    for table in tables:
                        rows = table.extract()
                        for row in rows:
                            if row:
                                for ceil in row:
                                    if ceil:
                                        ceil = re.sub(r'\s+', '', ceil)
                                        tables_text += ceil

                        x0, top, x1, bottom = table.bbox
                        # 表格top数值应大于表格前面文字的最后一个字的bottom
                        # 表格bottom数值应小于表格后面文字的第一个字的top
                        for word in words:
                            if word:
                                if word['bottom'] < top:
                                    words_left_page += word['text']
                                elif word['top'] > bottom:
                                    words_left_page += word['text']
                    words_left += words_left_page
                else:
                    for word in words:
                        if word:
                            words_left += word['text']
                text += words_left
            return [tables_text], text

    async def parse_manual(self, ukey, tables, text):
        tables_text = tables[0]
        content = tables_text + '\t' + text
        dict_wealth = AbchinaTextOnly.start(self.bank_name, ukey, content, self.collection_outline)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    AbchinaCleaner.start()




