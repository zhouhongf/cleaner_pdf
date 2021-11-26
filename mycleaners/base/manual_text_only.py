# 适用于一个文件内就含一个Wealth的情况
import re
import os
from utils.nlp_util import transfer_to_yuan, percent_to_num
from config import BankDict, Logger, Config, Wealth
from utils.nlp_util import UTIL_CN_NUM
from pymongo.collection import Collection


class ManualTextOnly(object):
    log_path = os.path.join(Config.LOG_DIR, 'ManualTextOnly.log')
    log = Logger(log_path, level='warning').logger

    labels_check = {
        'product_type',         # pass
        'name',                 # pass
        'code',
        'code_register',
        'currency',             # pass
        'risk',                 # pass
        'term',                 # pass
        'amount_buy_min',       # pass
        'redeem_type',
        'fixed_type',
        'promise_type',         # pass
        'rate_type',
        'rate_max',
        'rate_min',
    }

    list_risk = BankDict.list_risk
    list_currency = BankDict.list_currency

    def __init__(self, bank_name: str, ukey: str, text: str, collection: Collection):
        self.bank_name = bank_name
        self.ukey = ukey
        self.collection = collection
        self.text = re.sub(r'[【】\s]+', '', text)
        config = getattr(self, 'labels_check_config', None)
        if config:
            if not isinstance(config, set):
                raise ValueError("labels_check_config must be type of set")
            self.labels_check.update(config)

    @classmethod
    def start(cls, bank_name: str, ukey: str, text: str, collection: Collection):
        manual_text_in = cls(bank_name, ukey, text, collection)
        list_need = manual_text_in._start()
        return list_need

    def init_wealth_outline(self):
        result = self.collection.find_one({'_id': self.ukey})
        if result:
            wealth = Wealth.do_load(result)
        else:
            wealth = Wealth(ukey=self.ukey)
        return wealth

    def _start(self):
        wealth = self.init_wealth_outline()
        wealth = self.makeup_wealth(wealth)
        wealth = self.final_makeup_wealth(wealth)
        return wealth

    def makeup_wealth(self, wealth: Wealth):
        for one in self.labels_check:
            extract_method = getattr(self, 'extract_' + one, None)
            if extract_method is not None and callable(extract_method):
                wealth = extract_method(self.text, wealth)
            else:
                self.log.error('没有找到相应的方法：extract_%s方法' % one)
        return wealth

    # 此方法开放给用户，ManualText的子类继承后，自定义使用
    def parse_text_manual(self, wealth: Wealth):
        return wealth

    def final_makeup_wealth(self, wealth: Wealth):
        if not wealth.code:
            wealth.code = self.ukey.split('=')[-1]

        pattern_term_final = re.compile(r'[理财产品计划]*期限[为是：:\s]*[无没有]{1,2}固定期限')
        if not wealth.term:
            result = pattern_term_final.search(self.text)
            if result:
                wealth.term = '无固定期限'

        wealth = self.parse_text_manual(wealth)

        dict_need = {}
        dict_need[wealth.code] = wealth
        return dict_need

    def extract_product_type(self, value: str, wealth: Wealth):
        pattern_product_type = re.compile(r'[理财计划产品]*产品类型[属于为是：:\s]*[非保本证固定浮动收益开放式封闭净值型类公私募,，、]{5,}|本[期理财]*产品[属于为是：:\s]*[非保本证固定浮动收益开放式封闭净值型类公私募,，、\s]{5,}[理财]*产品')
        result = pattern_product_type.search(value)
        if result:
            text = result.group(0)
            if not wealth.promise_type:
                if '非保本' in text:
                    wealth.promise_type = '非保本'
                elif '保本' in text:
                    wealth.promise_type = '保本'

            if not wealth.fixed_type:
                if '浮动' in text:
                    wealth.fixed_type = '浮动收益'
                elif '固定' in text:
                    wealth.fixed_type = '固定收益'

        if not wealth.redeem_type:
            if '封闭式' in value:
                wealth.redeem_type = '封闭式'
            elif '开放式' in value:
                wealth.redeem_type = '开放式'

        if not wealth.rate_type:
            if '净值型' in value:
                wealth.rate_type = '净值型'
                wealth.fixed_type = '浮动收益'
            elif '预期收益型' in value:
                wealth.rate_type = '预期收益型'
            elif '结构性存款' in value:
                wealth.rate_type = '预期收益型'
        return wealth

    def extract_name(self, value: str, wealth: Wealth):
        if not wealth.name:
            pattern_name = re.compile(r'产品名称([\u4e00-\u9fa5、，,:：·“”"+\[\]\s（）()A-Za-z0-9\-]+?[理财结构性存款]{2,}产品([0-9]+年)?([0-9]+期)?([0-9]+款)?)')
            results = pattern_name.search(value)
            if results:
                name = results.group(1)
                wealth.name = name

                if not wealth.redeem_type:
                    if '封闭' in name:
                        wealth.redeem_type = '封闭式'
                    elif '开放' in name:
                        wealth.redeem_type = '开放式'

                if not wealth.rate_type:
                    if '净值' in name:
                        wealth.rate_type = '净值型'
                        wealth.fixed_type = '浮动收益'
                    elif '预期收益' in name:
                        wealth.rate_type = '预期收益型'
                    elif '结构性存款' in name:
                        wealth.rate_type = '预期收益型'

                if not wealth.promise_type:
                    if '非保本' in name:
                        wealth.promise_type = '非保本'
                    elif '保本' in name:
                        wealth.promise_type = '保本'
        return wealth

    def extract_rate_type(self, value: str, wealth: Wealth):
        if not wealth.rate_type:
            pattern_rate_type = re.compile(r'净值型|业绩比较基准|比较业绩基准|预期收益率|年化收益率|预期理财收益率|预期年化收益率|预期到期利率|结构性存款')
            result = pattern_rate_type.search(value)
            if result:
                rate_type = result.group(0)
                if rate_type in ['净值型', '比较业绩基准', '业绩比较基准']:
                    wealth.rate_type = '净值型'
                    wealth.fixed_type = '浮动收益'
                elif rate_type in ['预期收益率', '年化收益率', '预期理财收益率', '预期年化收益率', '预期到期利率', '结构性存款']:
                    wealth.rate_type = '预期收益型'
        return wealth

    def extract_redeem_type(self, value: str, wealth: Wealth):
        if not wealth.redeem_type:
            pattern_redeem_type_sub = re.compile(r'(如果|若|假设)[封闭期内投资理财计划成立后]*(投资者|投资人|客户)[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前]*赎回')
            pattern_redeem_type = re.compile(r'(投资者|投资人|客户)[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前]*赎回|本[理财产品计划投资]{2,}[在产品到期日之前封闭内]*[不没]?(对|得|享有|开放|可以|可|能|能够|无|有|接受)[\u4e00-\u9fa5]*赎回')
            pattern_redeem_type_extra = re.compile(r'[存续封闭期内投资理财计划成立后]*[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前申购和与或]*赎回')
            # 去除内容中关于赎回权利的如果，假设等语句
            value = pattern_redeem_type_sub.sub('', value)

            redeem_text = None
            result = pattern_redeem_type.search(value)
            if result:
                redeem_text = result.group(0)
            else:
                result = pattern_redeem_type_extra.search(value)
                if result:
                    redeem_text = result.group(0)
            if redeem_text:
                if '不' in redeem_text or '无' in redeem_text or '没' in redeem_text:
                    wealth.redeem_type = '封闭式'
                else:
                    wealth.redeem_type = '开放式'
        return wealth

    def extract_fixed_type(self, value: str, wealth: Wealth):
        return wealth

    def extract_promise_type(self, value: str, wealth: Wealth):
        if not wealth.promise_type:
            pattern_promise_type = re.compile(r'本[投资产品理财计划的]+([不无]?)[提供]*本金[完全]*[保障担证]{2}|([不无]?)[保障担证]{2}[理财购买资金]*[金额本]{2}')
            result = pattern_promise_type.search(value)
            if result:
                word = result.group(0)
                if word:
                    one_no = result.group(1)
                    two_no = result.group(2)
                    if one_no or two_no:
                        wealth.promise_type = '非保本'
                    else:
                        wealth.promise_type = '保本'
        return wealth


    def extract_code(self, value: str, wealth: Wealth):
        if not wealth.code:
            pattern_code = re.compile(r'[产品单元理财计划]{2,}[的认购]*[代码编号]{2}[为是：:\s]*([A-Za-z0-9][-+A-Za-z0-9]+)')
            result = pattern_code.search(value)
            if result:
                wealth.code = result.group(1)
        return wealth

    def extract_code_register(self, value: str, wealth: Wealth):
        if not wealth.code_register:
            pattern_code_register = re.compile(r'(登记|注册)[编码代号]+[为是：:\s]*([A-Za-z0-9]{6,})')
            result = pattern_code_register.search(value)
            if result:
                wealth.code_register = result.group(2)
        return wealth

    def extract_currency(self, value: str, wealth: Wealth):
        if not wealth.currency:
            pattern_currency = re.compile(r'[销售投资及收益本币]{2,}币种(人民币|美元|欧元|日元|英镑)')
            result = pattern_currency.search(value)
            if result:
                wealth.currency = result.group(1)
        return wealth

    # 返回风险等级的数字表示
    def extract_risk(self, value: str, wealth: Wealth):
        if not wealth.risk:
            pattern_risk_dig = re.compile(r'风险[评等分][级类][属于为是：:\s]*([0-9A-Za-z零一二三四五]+)级?')
            pattern_risk_cn = re.compile(r'风险[评等分][级类][属于为是：:\s]*[基本]*([无低较中等高极]+风险)')
            pattern_risk_cn_extra = re.compile(r'风险[评等分][级类][属于为是：:\s]*[基本]*(无|低|极低|较低|中低|中等|高|较高|中高)[风险]*')
            risk = None
            result = pattern_risk_cn.search(value)
            if result:
                risk_raw = result.group(1)
                for key in self.list_risk.keys():
                    if key == risk_raw:
                        risk = self.list_risk[key]
                        break
            if not risk:
                res = pattern_risk_dig.search(value)
                if res:
                    risk_raw = res.group(1)
                    res_num = re.search(r'[0-9]', risk_raw)
                    if res_num:
                        risk = res_num.group(0)
                        risk = int(risk)
                        if risk > 5:
                            self.log.error('风险评级数字超出范围，内容为：%s' % value)
                    else:
                        res_cn_num = re.search(r'[零一二三四五]', risk_raw)
                        if res_cn_num:
                            cn_num = res_cn_num.group(0)
                            risk = UTIL_CN_NUM[cn_num]
            if not risk:
                result = pattern_risk_cn_extra.search(value)
                if result:
                    risk_raw = result.group(1) + '风险'
                    for key in self.list_risk.keys():
                        if key == risk_raw:
                            risk = self.list_risk[key]
                            break

            wealth.risk = risk
        return wealth

    # 理财期限应该在所有的包含年月日等date查找完，并从value中去除后，再查找
    def extract_term(self, value: str, wealth: Wealth):
        if not wealth.term:
            pattern_term = re.compile(r'[理财产品计划]{2,}期限[为是：:\s]*([0-9]+)\s*([天日月年])')
            results = pattern_term.finditer(value)
            list_num = []
            for one in results:
                num = int(one.group(1))
                unit = one.group(2)
                if unit == '月':
                    num = num * 30
                elif unit == '年':
                    num = num * 365
                if num < 7301:              # 设定期限的最大值不能超过20年
                    list_num.append(num)
            if list_num:
                list_num.sort()
                wealth.term = list_num[0]       # 取list中期限日期最短的一个数字
        return wealth

    def extract_amount_buy_min(self, value: str, wealth: Wealth):
        if not wealth.amount_buy_min:
            pattern_amount_buy_min = re.compile(r'[起点份额认购买金最低余申产品销售]{4,}[个人对公机构:：为不低于\s]*(人民币|美元|欧元|英镑|日元)*\s*([1-9][0-9]*)\s*([亿万千百元]+)起?')
            results = pattern_amount_buy_min.finditer(value)
            list_num = []
            for one in results:
                num_text = one.group(2)
                unit = one.group(3)
                # print('找到的起购金额为：', (one.group(0)))
                if num_text and unit:
                    num = transfer_to_yuan(num_text + unit)
                    list_num.append(num)
            if list_num:
                list_num.sort()
                wealth.amount_buy_min = list_num[-1]
        return wealth

    def extract_rate_max(self, value: str, wealth: Wealth):
        return wealth

    def extract_rate_min(self, value: str, wealth: Wealth):
        if wealth.rate_min and wealth.rate_max:
            return wealth
        else:
            pattern_rate = re.compile(r'(业绩比较基准|业绩基准|预期收益率|实现年化收益|预期理财收益率|预期年化收益率|预期到期利率|净值型|结构性存款)[\u4e00-\u9fa5（()）]*([0-9]+(\.)?[0-9]*)[%％]')
            results = pattern_rate.finditer(value)
            list_num = []
            for one in results:
                rate_type = one.group(1)
                if rate_type and not wealth.rate_type:
                    self.extract_rate_type(rate_type, wealth)

                rate_num = one.group(2)
                if rate_num:
                    rate_num = percent_to_num(rate_num + '%')
                    if rate_num < 0.15:
                        list_num.append(rate_num)
            if list_num:
                list_num.sort()
                wealth.rate_min = list_num[0]
                wealth.rate_max = list_num[-1]
        return wealth
