from config import Wealth
from mycleaners.base import Cleaner, ManualTable, ManualText
from utils.nlp_util import find_datetimes, parse_datetime, transfer_to_yuan, percent_to_num
import re



class SpdbTable(ManualTable):

    table_labels_config = {
        'amount_buy_min': {'认购起点', '单笔认购', '起存金额', '认购金额', '申购金额', '申购份额', '认购份额', '最低持有份额'},
    }

    pattern_code_spdb = re.compile(r'([0-9]{6,})[产品代码编号登记为是：:\s]{4,}([A-Za-z0-9][-+A-Za-z0-9]+)?')
    pattern_rate_spdb = re.compile(r'[保底收益利率]{4,}[为：:\s]*([0-9]+(\.[0-9]+)*[%％])[,，;；][浮动收益利率范围]{4,}[为：:\s]*([0-9]+(\.[0-9]+)*[%％])[~或到和\-]([0-9]+(\.[0-9]+)*[%％])')
    pattern_rate_extra_spdb = re.compile(r'([0-9]+(\.[0-9]+)*[%％]?)[~或到和\-]([0-9]+(\.[0-9]+)*[%％])')

    pattern_fee_spdb = re.compile(r'产品管理费|托管费|投资管理费|销售手续费|认购费|固定管理费')

    pattern_date_period_spdb = re.compile(r'([0-9A-Za-z]{6,})([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)-([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)')
    pattern_date_spdb = re.compile(r'([0-9A-Za-z]{6,})([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)')


    def extract_name(self, label: str, value: str, wealth: Wealth):
        ukey = self.ukey
        code = ukey.split('=')[-1]
        wealth.code = code

        name = value.strip()
        wealth.name = name

        wealth = self.extract_product_type(label, value, wealth)
        if not wealth.code_register:
            results = self.pattern_code_spdb.search(name)
            if results:
                wealth.code_register = results.group(2)
                return wealth

            pattern_code_register_in_name = re.compile(r'(登记|注册)[编码代号]+[为是：:\s]*([A-Za-z0-9]{6,})')
            res = pattern_code_register_in_name.search(name)
            if res:
                wealth.code_register = res.group(2)
                return wealth
        return wealth

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

        ukey = self.ukey
        code = ukey.split('=')[-1]
        list_value = value.split(code)
        if len(list_value) == 2:
            value = list_value[1]

        list_data = []
        res = self.pattern_rate_spdb.search(value)
        if res:
            rate_base = res.group(1)
            rate_floor = res.group(3)
            rate_ceil = res.group(5)
            if rate_base:
                num_base = percent_to_num(rate_base)
                if rate_floor and rate_ceil:
                    num_floor = percent_to_num(rate_floor)
                    num_ceil = percent_to_num(rate_ceil)
                    num_floor = round(num_base + num_floor, 6)
                    num_ceil = round(num_base + num_ceil, 6)
                    if num_ceil < 0.15 and num_floor < 0.15:
                        list_data.append(num_floor)
                        list_data.append(num_ceil)
                        list_data.sort(reverse=True)
                        wealth.rate_max = list_data[0]
                        wealth.rate_min = list_data[-1]
                    else:
                        self.log.error('收益率num_ceil: %s或num_floor: %s超过0.15' % (str(num_ceil), str(num_floor)))
                else:
                    wealth.rate_max = num_base
                    wealth.rate_min = num_base
                return wealth

        list_data = []
        res_extra = self.pattern_rate_extra_spdb.search(value)
        if res_extra:
            rate_floor = res_extra.group(1)
            rate_ceil = res_extra.group(3)
            if rate_floor and rate_ceil:
                num_floor = percent_to_num(rate_floor + '%')
                num_ceil = percent_to_num(rate_ceil)
                num_floor = round(num_floor, 6)
                num_ceil = round(num_ceil, 6)
                if num_ceil < 0.15 and num_floor < 0.15:
                    list_data.append(num_floor)
                    list_data.append(num_ceil)
                    list_data.sort(reverse=True)
                    wealth.rate_max = list_data[0]
                    wealth.rate_min = list_data[-1]
                else:
                    self.log.error('收益率num_ceil: %s或num_floor: %s超过0.15' % (str(num_ceil), str(num_floor)))
            return wealth

        list_data = []
        pattern_rate = re.compile(r'[0-9]+\.?[0-9]*[%％]|[0-9]+\.[0-9]+')
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


    def extract_amount_buy_min(self, label: str, value: str, wealth: Wealth):
        ukey = self.ukey
        code = ukey.split('=')[-1]
        list_value = value.split(code)
        if len(list_value) == 2:
            value = list_value[1]

        num = None
        pattern_amount_buy_min = re.compile(r'[不低于起点认购金最余申份额]+[:\s：为]*(人民币|美元|欧元|英镑|日元)*[1-9][0-9]*[\s亿万千百美欧元英镑日]+|[1-9][0-9]*[\s亿万千百美欧元英镑日]+起')
        res = pattern_amount_buy_min.search(value)
        if res:
            one = res.group(0)
            num = transfer_to_yuan(one)
        else:
            pattern_amount = re.compile(r'[1-9][0-9]*(\.[0-9]+)*[亿万千百美欧元英镑日\s]+')
            results = pattern_amount.finditer(value)   # 如果pattern_amount_buy_min正则未匹配到，则使用pattern_amount找出所有的金额数字，取最小值为amount_buy_min的数值
            list_results = []
            for one in results:
                amount = one.group(0)
                if amount:
                    num = transfer_to_yuan(amount)
                    list_results.append(num)
            if len(list_results) > 0:
                list_results.sort(reverse=True)
                num = list_results[-1]                      # 找出value单元格中最小的数字，将其设置为amount_buy_min的数值

        # 起购金额最低设置为1万
        if num and num >= 10000:
            if not wealth.amount_buy_min:
                wealth.amount_buy_min = num
            else:
                if num < wealth.amount_buy_min:
                    wealth.amount_buy_min = num
        return wealth


class SpdbText(ManualText):
    labels_check_config = {}
    labels_check_one_config = {}


class SpdbCleaner(Cleaner):
    name = 'SpdbCleaner'
    bank_name = '浦发银行'

    async def parse_manual(self, ukey, tables, text):
        # print('解析出来的tables内容是：%s' % tables)
        dict_wealth = SpdbTable.start(self.bank_name, ukey, tables, self.collection_outline)
        dict_wealth = SpdbText.start(self.bank_name, dict_wealth, text)
        list_ukey = await self.save_wealth(dict_wealth)
        return list_ukey


def start():
    SpdbCleaner.start()




