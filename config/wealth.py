# ukey
# ukeyhash

# name:                     产品名称
# code:                     产品代码
# code_register:            登记编码
# bank_name                 银行名称
# bank_level                银行层级（国有银行、股份银行、城商银行、农商银行）

# currency:                 币种
# risk:                     风险等级
# term:                     期限                          单位（天）
# term_looped:              YES, NO        投资周期顺延 自动再投资
# amount_buy_min:           起购金额        单位(元)

# redeem_type:              封闭式、开放式，         即赎回规则
# fixed_type:               固定收益、浮动收益       如rate_type为净值型，则默认 浮动收益
# promise_type:             保本、非保本            如rate_type为净值型，则默认 非保本

# rate_type:                净值型、预期收益型       “保本的”为预期收益型，“非保本的”为净值型； 建设银行 用 七日年化收益率譬如3.6%，来表示 净值型产品的收益水平， 工商银行 直接用 净值譬如1.2256，来表示 净值型产品的收益水平
# 【利率的参考，以官方网站公布为准, 如果网站上没有，则尝试从PDF中搜寻】
# rate_min:                 最低利率     %转换为小数表述， 【只有一个利率时，默认首先保存rate_min】
# rate_max:                 最高利率     %转换为小数表述
# rate_netvalue:            如果是净值型，且大于0.2，则将rate_min的值记录在这里， rate_min和rate_max都设置为None， 将dict格式的rate_netvalue进行str化后，再保存


import time
import farmhash
from config.bank_dict import BankDict


version = "0.1"
version_info = (0, 1, 0, 0)


class Wealth(object):
    list_bank_level = BankDict.list_bank_level

    def __init__(
            self,
            ukey: str,
            name: str = None,
            code_register: str = None,
            currency: str = None,
            risk: int = None,
            term: int = None,
            term_looped: str = None,
            amount_buy_min: int = None,
            redeem_type: str = None,
            fixed_type: str = None,
            promise_type: str = None,
            rate_type: str = None,
            rate_max: float = None,
            rate_min: float = None,
            rate_netvalue: str = None,
            file_type: str = None,
            status: str = 'undo',
    ):
        self._ukey = ukey
        words = ukey.split('=')
        self._bank_name = words[0]
        self._code = words[-1]
        self._bank_level = self.list_bank_level[self._bank_name]
        self._name = name
        self._code_register = code_register
        self._currency = currency
        self._risk = risk
        self._term = term
        self._term_looped = term_looped
        self._amount_buy_min = amount_buy_min
        self._redeem_type = redeem_type
        self._fixed_type = fixed_type
        self._promise_type = promise_type
        self._rate_type = rate_type
        self._rate_max = rate_max
        self._rate_min = rate_min
        self._rate_netvalue = rate_netvalue
        self._file_type = file_type
        self._status = status

    def __repr__(self):
        return f"【Wealth ukey: {self._ukey}, name: {self._name}】 " \
               f"code: {self._code}, code_register: {self._code_register}, currency: {self._currency}, risk: {self._risk}, " \
               f"rate_type: {self._rate_type}, rate_max: {self._rate_max}, rate_min: {self._rate_min}, " \
               f"fixed_type: {self._fixed_type}, promise_type: {self._promise_type}, redeem_type: {self._redeem_type}, " \
               f"term: {self._term}, term_looped: {self._term_looped}, amount_buy_min: {self._amount_buy_min}, file_type: {self._file_type}"

    def do_dump(self):
        elements = [one for one in dir(self) if not (one.startswith('__') or one.startswith('_') or one.startswith('do_') or one.startswith('list_'))]
        data = {}
        for name in elements:
            value = getattr(self, name, None)
            data[name] = value
        # 为了保存进mongodb，增加_id，并设置其值为ukey, 并添加保存时间
        data['_id'] = str(farmhash.hash64(self.ukey))
        data['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        return data

    @classmethod
    def do_load(cls, data: dict):
        outline = cls(ukey=data['ukey'])
        elements = [one for one in dir(cls) if not (one.startswith('__') or one.startswith('_') or one.startswith('do_') or one.startswith('list_'))]
        for one in elements:
            if one in data.keys():
                setattr(outline, one, data[one])
        return outline

    @property
    def ukey(self):
        return self._ukey

    @ukey.setter
    def ukey(self, value):
        self._ukey = value

    @property
    def bank_level(self):
        return self._bank_level

    @bank_level.setter
    def bank_level(self, value):
        self._bank_level = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def bank_name(self):
        return self._bank_name

    @bank_name.setter
    def bank_name(self, value):
        self._bank_name = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def code_register(self):
        return self._code_register

    @code_register.setter
    def code_register(self, value):
        self._code_register = value

    @property
    def redeem_type(self):
        return self._redeem_type

    @redeem_type.setter
    def redeem_type(self, value):
        self._redeem_type = value

    @property
    def fixed_type(self):
        return self._fixed_type

    @fixed_type.setter
    def fixed_type(self, value):
        self._fixed_type = value

    @property
    def promise_type(self):
        return self._promise_type

    @promise_type.setter
    def promise_type(self, value):
        self._promise_type = value

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, value):
        self._currency = value

    @property
    def risk(self):
        return self._risk

    @risk.setter
    def risk(self, value):
        self._risk = value

    @property
    def term(self):
        return self._term

    @term.setter
    def term(self, value):
        self._term = value

    @property
    def term_looped(self):
        return self._term_looped

    @term_looped.setter
    def term_looped(self, value):
        self._term_looped = value

    @property
    def rate_type(self):
        return self._rate_type

    @rate_type.setter
    def rate_type(self, value):
        self._rate_type = value

    @property
    def rate_max(self):
        return self._rate_max

    @rate_max.setter
    def rate_max(self, value):
        self._rate_max = value

    @property
    def rate_min(self):
        return self._rate_min

    @rate_min.setter
    def rate_min(self, value):
        self._rate_min = value

    @property
    def rate_netvalue(self):
        return self._rate_netvalue

    @rate_netvalue.setter
    def rate_netvalue(self, value):
        self._rate_netvalue = value

    @property
    def amount_buy_min(self):
        return self._amount_buy_min

    @amount_buy_min.setter
    def amount_buy_min(self, value):
        self._amount_buy_min = value

    @property
    def file_type(self):
        return self._file_type

    @file_type.setter
    def file_type(self, value):
        self._file_type = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
