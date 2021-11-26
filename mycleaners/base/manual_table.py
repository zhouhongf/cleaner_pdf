import re
from config import Config, BankDict, Wealth, Logger
import os
from pymongo.collection import Collection
from utils.nlp_util import transfer_to_yuan, percent_to_num
from utils.nlp_util import UTIL_CN_NUM


class ManualTable(object):
    log_file = os.path.join(Config.LOG_DIR, 'ManualTable.log')
    log = Logger(log_file, level='warning').logger

    # 理财产品说明书布局 的思考：
    # 1、一般来说，表格为母表的，含有基础内容，表格为其子表，含有补充内容
    # 2、子理财产品的名称为母理财产品的名称或名称简称，再加上 第XX期  XX天型
    table_labels = {
        'product_type': {'产品类型', '收益类型', '存款类型'},

        'name': {'名称'},
        'code': {'产品编码', '产品代码', '认购编号', '单元代码', '销售编号'},
        'code_register': {'登记编码'},
        'risk': {'风险等级', '风险分级', '风险分类', '风险评级', '产品评级', '风险评定', '风险级别'},
        'currency': {'币种'},

        'term': {'计算天数', '理财期限', '计划期限', '周期天数', '存款期限', '产品期限', '投资周期', '投资期限', '持有期'},
        'term_looped': {'投资周期顺延', '自动再投资'},

        'amount_buy_min': {'认购起点', '认购份额', '认购金额', '申购起点', '申购份额', '申购金额', '单笔认购', '起存金额', '起点金额', '起购金额'},

        'redeem_type': {'赎回'},
        'fixed_type': {'固定收益', '浮动收益'},
        'promise_type': {'保本', '非保本'},
        'rate_type': {'业绩基准', '比较基准', '理财收益率', '理财收益', '利息', '预期收益率', '年化收益率', '净值', '预期收益', '年化净收益率', '结构性存款', '参考收益率', '参考净收益率', '参照收益率'},
        'rate_max': {},
        'rate_min': {'固定收益率'},
        'rate_netvalue': {},
    }

    list_risk = BankDict.list_risk
    list_currency = BankDict.list_currency
    list_ignore = ['ukey', 'bank_level', 'bank_name', 'name', 'code', 'do_dump', 'do_load']

    # 如果实例化时，传入了自定义的table_labels字典，则将其更新至类属性table_labels当中，
    # table_labels字典中key对应的value将发生变化
    def __init__(self, bank_name: str, ukey: str, tables: list, collection: Collection):
        self.bank_name = bank_name
        self.ukey = ukey
        self.tables = tables
        self.collection = collection
        config = getattr(self, 'table_labels_config', None)
        if config:
            if not isinstance(config, dict):
                raise ValueError("table_labels_config must be type of dict")
            self.table_labels.update(config)

    @classmethod
    def start(cls, bank_name: str, ukey: str, tables: list, collection: Collection):
        print('开始解析:', ukey)
        manual_table_in = cls(bank_name, ukey, tables, collection)
        dict_wealth = manual_table_in._start()
        return dict_wealth

    def init_wealth_outline(self):
        result = self.collection.find_one({'_id': self.ukey})
        if result:
            wealth = Wealth.do_load(result)
        else:
            wealth = Wealth(ukey=self.ukey)
        return wealth

    def _start(self):
        dict_wealth = {}                                          # dict_wealth的key为code, value为wealth实例
        last_wealth = Wealth(ukey=self.bank_name + '=last')       # 生成一个last_wealth实例，用于保存上一张表格的信息
        for table in self.tables:
            wealth = self.init_wealth_outline()

            # 1、解析每一张table
            for row in table:
                label = re.sub(r'[【】()（）《》\s]+', '', row[0])
                value = re.sub(r'[【】()（）《》\s]+', '', row[1])          # 【去掉value中的一些特殊字符，以减少后期正则匹配的难度】
                wealth = self.parse_row(label, value, wealth)
            # 2、自定义解析方法
            wealth = self.parse_table_manual(wealth, table)
            # 3、比较last_wealth和wealth,
            # （1）如果last_wealth当中没有wealth的内容，则用wealth更新last_wealth，
            # （2）如果wealth中缺少内容，则从last_wealth中补全
            wealth = self.compare_last_wealth(last_wealth, wealth)
            # 4、codeless的wealth设置
            # 防止该文件中只有一张table，并且该table只存在一个不含有code的wealth情况的出现，使用codeless来表示没有code的wealth
            # 如果一个文件中存在2张具有相同code的表格，则以后一个wealth内容为准
            if wealth.code:
                dict_wealth[wealth.code] = wealth
            else:
                dict_wealth['codeless'] = wealth
        return dict_wealth

    def parse_row(self, label: str, value: str, wealth: Wealth):
        for k, v in self.table_labels.items():
            # 遍历对应key的所有的value值，如果有value值存在于label中，则应用解析方法，去取值
            for one in v:
                if one in label:
                    extract_method = getattr(self, 'extract_' + k, None)
                    if extract_method is not None and callable(extract_method):
                        wealth = extract_method(label, value, wealth)
                    else:
                        self.log.error('没有找到相应的方法：extract_%s方法' % k)

        if '封闭' in label:
            wealth.redeem_type = '封闭式'
        return wealth

    # 【此方法开放给用户，ManualTable的子类继承后，自定义使用】
    def parse_table_manual(self, wealth: Wealth, table: list):
        return wealth

    # 比较last_wealth和当前的wealth
    # (1) 挑选出wealth中需要更新的实例元素，去除内置元素和内置方法，去除不需要比较的元素，放入wealth_instance_elements集合中，进行遍历
    # (2) 如果wealth的元素current_element的值存在，则将last_wealth中的element的值设置为current_element的值
    # (3) 如果wealth的元素current_element的值不存在，相反，如果last_wealth的元素last_element存在值，则将wealth的current_element设置为last_element的值
    def compare_last_wealth(self, last_wealth: Wealth, wealth: Wealth):
        wealth_instance_elements = [one for one in dir(wealth) if not (one.startswith('__') or one.startswith('_') or (one in self.list_ignore))]
        for element in wealth_instance_elements:
            last_element = getattr(last_wealth, element, None)
            current_element = getattr(wealth, element, None)
            if current_element:
                setattr(last_wealth, element, current_element)
            else:
                if last_element:
                    setattr(wealth, element, last_element)
        return wealth

    # ================================================================================================================
    # 以下为具体的解析每一个label的方法
    # ================================================================================================================
    def extract_product_type(self, label: str, value: str, wealth: Wealth):
        # print('直接搜索关键字, product_type【标签】：%s, 【解析内容】：%s' % (label, value))
        if not wealth.promise_type:
            if '非保本' in value:
                wealth.promise_type = '非保本'
            elif '保本' in value:
                wealth.promise_type = '保本'
            elif '保证收益' in value:
                wealth.promise_type = '保本'

        if not wealth.fixed_type:
            if '浮动' in value:
                wealth.fixed_type = '浮动收益'
            elif '固定' in value:
                wealth.fixed_type = '固定收益'

        if not wealth.redeem_type:
            if '封闭' in value:
                wealth.redeem_type = '封闭式'
            elif '开放' in value:
                wealth.redeem_type = '开放式'

        if not wealth.rate_type:
            if '净值' in value:
                wealth.rate_type = '净值型'
                wealth.fixed_type = '浮动收益'
                return wealth

            for one in ['比较业绩基准', '业绩比较基准', '业绩基准']:
                if one in value:
                    wealth.rate_type = '净值型'
                    break
            for one in ['预期理财收益率', '预期年化收益率', '预期到期利率', '年化收益率', '预期收益率', '结构性存款']:
                if one in value:
                    wealth.rate_type = '预期收益型'
                    break
        return wealth

    def extract_redeem_type(self, label: str, value: str, wealth: Wealth):
        if not wealth.redeem_type:
            pattern_redeem_type_sub = re.compile(r'(如果|若|假设)[封闭期内投资理财计划成立后]*(投资者|投资人|客户)[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前]*赎回')
            pattern_redeem_type = re.compile(r'(投资者|投资人|客户)[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前]*赎回|本[理财产品计划投资]{2,}[在产品到期日之前封闭内]*[不没]?(对|得|享有|开放|可以|可|能|能够|无|有|接受)[\u4e00-\u9fa5]*赎回')
            pattern_redeem_type_extra = re.compile(r'[存续封闭期内投资理财计划成立后]*[不没]?(得|享有|开放|可以|可|能|能够|无|有|接受)[提前申购和与或]*赎回')
            # pattern_redeem_type = re.compile(r'[投资者人客户产品理财计划]*不?[提供得享没有开放可以能够无]*[申购和与提前]*赎回')
            value = pattern_redeem_type_sub.sub('', value)              # 去除内容中关于赎回权利的如果，假设等语句
            value = re.sub(r'[投资者人客户申购买认]+', '', value)         # 去除内容中类似投资人，购买者，认购者，申购者等名词

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

    def extract_fixed_type(self, label: str, value: str, wealth: Wealth):
        return wealth

    def extract_promise_type(self, label: str, value: str, wealth: Wealth):
        if not wealth.promise_type:
            pattern_promise_type = re.compile(r'([不无]?)[提供]*本金[完全]*保障|([不无]?)[保证障]{2}[理财购买资金]*[金额本]{2}')
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

    def extract_rate_type(self, label: str, value: str, wealth: Wealth):
        if not wealth.rate_type:
            if '业绩' in label:
                wealth.rate_type = '净值型'
                wealth.promise_type = '非保本'
                wealth.fixed_type = '浮动收益'

            # wealth = self.extract_promise_type(label, value, wealth)
            # wealth = self.extract_product_type(label, value, wealth)
            wealth = self.extract_rate_min(label, value, wealth)
        return wealth


    def extract_name(self, label: str, value: str, wealth: Wealth):
        if not wealth.name:
            wealth.name = value

        if not wealth.code:
            pattern_code_in_name = re.compile(r'[代码编号]{2,}[为是：:\s]*([A-Za-z0-9][-+A-Za-z0-9]+)')
            result = pattern_code_in_name.search(value)
            if result:
                wealth.code = result.group(1)

        if not wealth.code_register:
            pattern_code_register_in_name = re.compile(r'(登记|注册)[编码代号]+[为是：:\s]*([A-Za-z0-9]{6,})')
            res = pattern_code_register_in_name.search(value)
            if res:
                wealth.code_register = res.group(2)

        if wealth.promise_type and wealth.fixed_type and wealth.redeem_type and wealth.rate_type:
            return wealth
        else:
            return self.extract_product_type(label, value, wealth)

    def extract_code(self, label: str, value: str, wealth: Wealth):
        if not wealth.code:
            pattern_code = re.compile(r'[内部产品代码编号为是：:\s]*([A-Za-z0-9][-+A-Za-z0-9]+)')
            result = pattern_code.search(value)
            if result:
                wealth.code = result.group(1)
        return wealth

    def extract_code_register(self, label: str, value: str, wealth: Wealth):
        if not wealth.code_register:
            pattern_code_register = re.compile(r'[A-Z0-9]{6,}')
            result = pattern_code_register.search(value)
            if result:
                wealth.code_register = result.group(0)
        return wealth

    def extract_currency(self, label: str, value: str, wealth: Wealth):
        if not wealth.currency:
            for one in self.list_currency:
                if one in value:
                    wealth.currency = one
                    break
        return wealth

    # 返回风险等级的数字表示
    def extract_risk(self, label: str, value: str, wealth: Wealth):
        # print('【risk标签：%s, 解析：%s】' % (label, value))
        if not wealth.risk:
            pattern_risk_dig = re.compile(r'([0-9A-Za-z零一二三四五]+)级?')
            pattern_risk_cn = re.compile(r'[无低极较中等高]+风险')
            risk = None
            result = pattern_risk_cn.search(value)
            if result:
                risk_raw = result.group(0)
                # print('risk_raw1是：', risk_raw)
                for key in self.list_risk.keys():
                    if key == risk_raw:
                        risk = self.list_risk[key]
                        break
            if not risk:
                res = pattern_risk_dig.search(value)
                if res:
                    risk_raw = res.group(1)
                    # print('risk_raw2是：', risk_raw)
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
            wealth.risk = risk
        return wealth

    def extract_term(self, label: str, value: str, wealth: Wealth):
        result = re.compile(r'\d+').fullmatch(value)
        if not result:
            # 检查value单元格是否为纯数字，若是，则再检查label标签中是否有单位，如有单位，则转换为天数后返回
            pattern_num = re.compile(r'[0-9，,]+')
            res_value = pattern_num.fullmatch(value)
            if res_value:
                num = res_value.group(0)
                num = num.replace(',', '')
                num = num.replace('，', '')
                num = int(num)

                pattern_unit = re.compile(r'[天日月年]')
                res_label = pattern_unit.search(label)
                if res_label:
                    unit = res_label.group(0)
                    if unit == '月':
                        num = num * 30
                    elif unit == '年':
                        num = num * 365
                    if num < 7301:
                        wealth.term = num
                    return wealth

            pattern_term = re.compile(r'([0-9，,]+)个?([天日月年])')
            pattern_term_sub = re.compile(r'([0-9]{2,4}年)?[0-9]{1,2}月[0-9]{1,2}日')
            # 去除value单元格中XX年XX月XX日格式的文字
            res = pattern_term_sub.finditer(value)
            for one in res:
                date = one.group(0)
                value = value.replace(date, '')

            # 查找数量的年、月、日
            result = pattern_term.search(value)
            if result:
                num = result.group(1)
                num = num.replace(',', '')
                num = num.replace('，', '')
                num = int(num)
                unit = result.group(2)
                if unit == '月':
                    num = num * 30
                elif unit == '年':
                    num = num * 365
                if num < 7301:              # 设定期限的最大值不能超过20年
                    wealth.term = num
        # 检查是否是循环理财
        if not wealth.term_looped:
            if '投资周期顺延' in value or '自动再投资' in value or '无固定期限' in value:
                wealth.term_looped = 'YES'
        return wealth

    def extract_term_looped(self, label: str, value: str, wealth: Wealth):
        if not wealth.term_looped:
            if '投资周期顺延' in label or '自动再投资' in label:
                wealth.term_looped = 'YES'
        return wealth


    def extract_amount_buy_min(self, label: str, value: str, wealth: Wealth):
        value = re.sub('[,，]+', '', value)
        # 用match匹配一下，是否是纯数字
        if not wealth.amount_buy_min:
            num = None
            res_value = re.fullmatch(r'[0-9]+(\.[0-9]+)*', value)
            if res_value:
                num = res_value.group(0)
                # 如果是，再检查一下label中是否存在单位，如有单位，则换算成数字
                res_label = re.search(r'[亿万]', label)
                if res_label:
                    unit = res_label.group(0)
                    num = transfer_to_yuan(num + unit)
                else:
                    num = int(num)
            else:
                # pattern_amount_buy_min = re.compile(r'(不低于|起点|起点份额|认购金额|最低余额|申购金额)[:\s：为]*(人民币|美元|欧元|英镑|日元)*[1-9][0-9]*[\s亿万千美欧元英镑日]+|[1-9][0-9]*[\s亿万千美欧元英镑日]+起')   # 仅能用于search()方法
                pattern_amount_buy_min = re.compile(r'[不低于起点认购金最余申份额]+[:\s：为]*(人民币|美元|欧元|英镑|日元)*[1-9][0-9]*[\s亿万千百美欧元英镑日]+|[1-9][0-9]*[\s亿万千百美欧元英镑日]+起')
                # 如果不是纯数字，则使用带文字的pattern_amount_buy_min正则表达式去匹配
                res = pattern_amount_buy_min.search(value)
                if res:
                    one = res.group(0)
                    num = transfer_to_yuan(one)
                else:
                    # 如果未匹配到，则使用pattern_amount找出所有的金额数字，取最小值为amount_buy_min的数值
                    pattern_amount = re.compile(r'[1-9][0-9]*(\.[0-9]+)*[亿万千百美欧元英镑日\s]+')
                    results = pattern_amount.finditer(value)
                    list_results = []
                    for one in results:
                        amount = one.group(0)
                        if amount:
                            num = transfer_to_yuan(amount)
                            list_results.append(num)
                    if len(list_results) > 0:
                        list_results.sort(reverse=True)
                        num = list_results[-1]                      # 找出value单元格中最小的数字，将其设置为amount_buy_min的数值
            if num and num > 0:
                wealth.amount_buy_min = num
        return wealth

    def extract_rate_netvalue(self, value: str, wealth: Wealth):
        return wealth

    def extract_rate_max(self, label: str, value: str, wealth: Wealth):
        return wealth

    def extract_rate_min(self, label: str, value: str, wealth: Wealth):
        if not wealth.rate_min:
            pattern_rate = re.compile(r'[0-9]+\.?[0-9]*[%％]|[0-9]+\.[0-9]+')  # 带%号的，可以为整数或小数，不带%号的，则必须为小数格式
            pattern_rate_extra = re.compile(r'([0-9]+\.?[0-9]*)[%％]?\+([0-9]+\.?[0-9]*)[%％]')  # 带+号的，最高最低利率区间需要自己再计算一下

            res = pattern_rate_extra.search(value)
            if res:
                rate_base = res.group(1)
                rate_add = res.group(2)

                num_base = float(rate_base) / 100
                num_add = float(rate_add) / 100
                num_ceil = round(num_base + num_add, 6)

                wealth.rate_min = num_base
                wealth.rate_max = num_ceil
                return wealth

            list_data = []
            results = pattern_rate.finditer(value)
            for one in results:
                word = one.group(0)
                if word:
                    num = percent_to_num(word)
                    if num < 0.1:
                        list_data.append(num)
                    else:
                        self.log.error('收益率超过0.15，解析出来的num为：%s' % str(num))
            if len(list_data) > 0:
                list_data.sort(reverse=True)
                wealth.rate_max = list_data[0]
                wealth.rate_min = list_data[-1]
        return wealth
