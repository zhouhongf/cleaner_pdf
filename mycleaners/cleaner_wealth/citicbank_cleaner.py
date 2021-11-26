from config import Wealth
from mycleaners.base import Cleaner, ManualTable, ManualText
from utils.nlp_util import percent_to_num
import re
from config import BankDict


class CiticbankTable(ManualTable):
    base_rate = BankDict.wealth_base['base_rate_save']
    table_labels_config = {}
    pattern_rate_citicbank = re.compile(r'一年期人民币存款基准利率\+([0-9]+(\.[0-9]+)*[%％])')

    def extract_rate_type(self, label: str, value: str, wealth: Wealth):
        if '业绩' in label:
            wealth.rate_type = '净值型'
            wealth.promise_type = '非保本'
            wealth.fixed_type = '浮动收益'
        elif '收益率' in label:
            wealth.rate_type = '预期收益型'

        # 使用正则表达式，匹配是否为保本或非保本
        wealth = self.extract_promise_type(label, value, wealth)
        # 重要，使用extract_product_type()再次匹配关键字，或正则表达式搜索匹配 业绩比较基准 或 预期收益率
        wealth = self.extract_product_type(label, value, wealth)

        list_data = []
        res = self.pattern_rate_citicbank.finditer(value)
        for one in res:
            word = one.group(1)
            if word:
                num = percent_to_num(word)
                if num < 0.15:
                    list_data.append(num)
                else:
                    self.log.error('收益率超过0.15，解析出来的num为：%s' % str(num))
        if len(list_data) > 0:
            list_data.sort(reverse=True)
            rate_max = round(list_data[0] + self.base_rate, 6)
            rate_min = round(list_data[-1] + self.base_rate, 6)
            wealth.rate_max = rate_max
            wealth.rate_min = rate_min
            return wealth

        pattern_rate = re.compile(r'[0-9]+\.?[0-9]*[%％]|[0-9]+\.[0-9]+')
        list_data = []
        results = pattern_rate.finditer(value)
        for one in results:
            word = one.group(0)
            if word:
                num = percent_to_num(word)
                if num < 0.15:
                    list_data.append(num)
                else:
                    self.log.error('收益率超过0.15，解析出来的num为：%s' % str(num))
        if len(list_data) > 0:
            list_data.sort(reverse=True)
            wealth.rate_max = list_data[0]
            wealth.rate_min = list_data[-1]
        return wealth


class CiticbankText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


    def extract_invest_on(self, value: str, wealth: Wealth):
        pattern_invest_on = re.compile(r'本[期]?理财[理财募集的资计划产品本金最终可存续期间,，管人主要]*投资于[以下投资工具：:\s]*([\u4e00-\u9fa5、，；;,:：%％+\[\]（）()A-Za-z0-9\-]+)。')
        pattern_invest_on_citicbank = re.compile(r'[1-9]([\u4e00-\u9fa5]+)[:：][\u4e00-\u9fa5、，,（）\\(\\)A-Za-z0-9]+[；;。]')
        result = pattern_invest_on.search(value)
        if result:
            text = result.group(1)
            if text:
                res = pattern_invest_on_citicbank.findall(text)
                if res:
                    wealth.invest_on = ','.join(res)
        return wealth


class CiticbankCleaner(Cleaner):
    name = 'CiticbankCleaner'
    bank_name = '中信银行'

    async def parse_manual(self, ukey, tables, text):
        # print('解析出来的tables内容是：%s' % tables)
        dict_wealth = CiticbankTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = CiticbankText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CiticbankCleaner.start()



