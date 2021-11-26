from config import Wealth
from mycleaners.base import Cleaner, ManualTable, ManualText
import os
import re


class CibTable(ManualTable):

    table_labels_config = {
        'year_term_number': {'期次款数'},
        'name': {'产品名称'},
        'term': {'计算天数', '理财期限', '计划期限', '周期天数', '存款期限', '产品期限', '投资周期', '期限'},
    }

    pattern_year_term_number = re.compile(r'[0-9]{4}年第[0-9]+期.*')
    pattern_sale_ways = re.compile(r'(网点柜面|网银|网上银行|网上个人银行|手机银行|电话银行|营业网点|微信银行|自助渠道|柜面|直销银行|金融自助通)+')
    pattern_fee_types = re.compile(r'([销售托管其他手续固定认购投资]+费)[\s:：年化费率为]*([0-9]+(\.[0-9]+)*)[%％][\s/每年]*')

    pattern_risk_dig = re.compile(r'■([0-9A-Za-z]+)级?')
    pattern_risk_cn = re.compile(r'■[基本]*([无低极较中等高]+风险)')

    name_extra = None

    def parse_table_manual(self, wealth: Wealth, table: list):
        name = wealth.name
        if name:
            if self.name_extra and ('年第期' in name):
                name = name.replace('年第期', self.name_extra)
                wealth.name = name
        return wealth

    def extract_year_term_number(self, label: str, value: str, wealth: Wealth):
        result = self.pattern_year_term_number.search(value)
        if result:
            self.name_extra = result.group(0)
        return wealth

    def extract_risk(self, label: str, value: str, wealth: Wealth):
        # print('【risk标签：%s, 解析：%s】' % (label, value))
        risk = None
        result = self.pattern_risk_cn.search(value)
        if result:
            risk_raw = result.group(1)
            # print('risk_raw1是：', risk_raw)
            for key in self.list_risk.keys():
                if key == risk_raw:
                    risk = self.list_risk[key]
                    break
        if not risk:
            res = self.pattern_risk_dig.search(value)
            if res:
                risk_raw = res.group(1)
                # print('risk_raw2是：', risk_raw)
                res_num = re.search(r'[0-9]', risk_raw)
                if res_num:
                    risk = res_num.group(0)
                    risk = int(risk)
                    if risk > 5:
                        self.log.error('风险评级数字超出范围，内容为：%s' % value)
        wealth.risk = risk
        return wealth


class CibText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}

    def extract_name(self, value: str, wealth: Wealth):
        pattern_name_extra = re.compile(r'兴业银行.+?要素表.+年第?[0-9]+期([A-Za-z0-9]+款)?')
        pattern_name = re.compile(r'《([\u4e00-\u9fa5、，,:：“”"+\[\]\s（）()A-Za-z0-9\-]+)(风险揭示及说明书|产品说明书|协议书)》')
        if not wealth.name:
            res = pattern_name_extra.search(value)
            if res:
                word = res.group(0)
                name = word.split('要素表')[-1]
                wealth.name = name
                return wealth

            results = pattern_name.findall(value)         # 全文搜索带书名号的文字，选择最长的作为name, 需要考虑是否合适？
            if results:
                word_longest = ''
                for one in results:
                    name_raw = one[0]
                    name_net = name_raw.replace('结构性存款', '')
                    if len(name_net) > 0:
                        if len(name_raw) > len(word_longest):
                            word_longest = name_raw
                wealth.name = word_longest
                # print('extract_name中的wealth.name是：%s' % wealth.name)
        return wealth


class CibCleaner(Cleaner):
    name = 'CibchinaCleaner'
    bank_name = '兴业银行'
    other_file_type = '.html'

    async def parse_manual(self, ukey, tables, text):
        # print('解析出来的文字内容是：%s' % text)
        dict_wealth = CibTable.start(self.bank_name, ukey, tables, self.collection_outline)
        # print('解析的内容是：%s' % dict_wealth)
        dict_wealth = CibText.start(self.bank_name, dict_wealth, text)
        # print('解析的内容是：%s' % dict_wealth)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    CibCleaner.start()




