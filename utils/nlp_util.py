import jieba
import re
from datetime import datetime
from typing import Pattern


UTIL_CN_NUM = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
    '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4,
    '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
}

UTIL_CN_UNIT = {'十': 10, '百': 100, '千': 1000, '万': 10000, '亿': 100000000}

pattern_year = re.compile(r'([0-9零一二两三四五六七八九十]+)\s*年')

pattern_date = re.compile(r'([0-9一二三四五六七八九零]{2,4})[年/-]?([0-9一二三四五六七八九十]{1,2})[月/-]([0-9一二三四五六七八九十]{1,3})日?')
pattern_date_standard = re.compile(r'20[0-9]{2}[年/-]*[01]?[0-9][月/-]*[0-3]?[0-9]日?')

pattern_date_findall = re.compile(r'[0-9零一二两三四五六七八九十\s]*年?[0-9一二两三四五六七八九十\s]+月[0-9一二两三四五六七八九十\s]+日[上中下午晚早\s]*[0-9零一二两三四五六七八九十]{0,3}[点:.时\s]?[0-9零一二三四五六七八九十]{0,3}[分:.\s]?[0-9零一二三四五六七八九十\s]{0,3}秒?')
pattern_date_search = re.compile(r'([0-9零一二两三四五六七八九十\s]*)年?([0-9一二两三四五六七八九十\s]+)月([0-9一二两三四五六七八九十\s]+)日([上中下午晚早\s]*)([0-9零一二两三四五六七八九十]{0,3})[点:.时\s]([0-9零一二三四五六七八九十]{0,3})[分:.\s]([0-9零一二三四五六七八九十]{0,3})秒?')

pattern_date_yyyymmdd = re.compile(r'[0-9]{2,4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{2,4}/[0-9]{1,2}/[0-9]{1,2}')
pattern_date_yyyymmdd_hhmmss = re.compile(r'[0-9]{2,4}-[0-9]{1,2}-[0-9]{1,2}\s*([0-9]{1,2}:[0-9]{2}:?[0-9]{0,2})?')
pattern_date_yyyymmdd_hhmmss_extra = re.compile(r'[0-9]{2,4}/[0-9]{1,2}/[0-9]{1,2}\s*([0-9]{1,2}:[0-9]{2}:?[0-9]{0,2})?')



def date_to_standard(text: str) -> list:
    list_date = []
    results = pattern_date_standard.finditer(text)
    for one in results:
        date_text = one.group(0)
        if date_text:
            pure_num = re.match(r'[0-9]{6}', date_text)
            if pure_num:
                date = datetime.strptime(date_text, '%Y%m%d')
            elif '/' in date_text:
                date = datetime.strptime(date_text, '%Y/%m/%d')
            elif '年' in date_text and '月' in date_text and '日' in date_text:
                date_text = date_text.replace('年', '-')
                date_text = date_text.replace('月', '-')
                date_text = date_text.replace('日', '')
                date = datetime.strptime(date_text, '%Y-%m-%d')
            else:
                date = datetime.strptime(date_text, '%Y-%m-%d')

            date_text = date.strftime('%Y-%m-%d')
            date_text = date_text + ' 00:00:00'
            list_date.append(date_text)
    return list_date


# 从文字中查找YYYY-mm-dd, 返回YYYY年mm月dd日
def timesimple_to_timechinese(text: str) -> list:
    list_datetime = []
    res = pattern_date_yyyymmdd.findall(text)
    if res:
        for one in res:
            try:
                date = datetime.strptime(one, '%Y-%m-%d')
            except:
                date = datetime.strptime(one, '%Y/%m/%d')

            date = date.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
            list_datetime.append(date)
    return list_datetime


# 注意text当中只允许存在同一种格式的日期，不然将只解析第一个符合条件的日期后，直接返回
def find_datetimes(text: str) -> list:
    list_datetime = []

    # 先查找YYYY-mm-dd HH:mm:ss类型的日期
    results = pattern_date_yyyymmdd_hhmmss.finditer(text)
    for one in results:
        date = one.group(0)
        date_extra = one.group(1)
        if date_extra:
            nums = date_extra.split(':')
            if len(nums) == 2:
                date = date + ':00'
        else:
            date = date + ' 00:00:00'
        list_datetime.append(date)

    # 如果找不到，再查找YYYY/mm/dd HH:mm:ss类型的日期
    if not list_datetime:
        results = pattern_date_yyyymmdd_hhmmss_extra.finditer(text)
        for one in results:
            date = one.group(0)
            date_extra = one.group(1)
            if date_extra:
                nums = date_extra.split(':')
                if len(nums) == 2:
                    date = date + ':00'
            else:
                date = date + ' 00:00:00'
            date = re.sub('/', '-', date)
            list_datetime.append(date)

    # 如果找不到，再查找YYYY年mm月dd日类型的日期
    if not list_datetime:
        results = pattern_date_findall.findall(text)
        if results:
            year = ''
            for one in results:
                res = pattern_year.search(one)
                if res:
                    year = res.group(1)
                    break

            if not year:
                year = str(datetime.today().year)

            for one in results:
                if '年' not in one:
                    one = year + '年' + one
                else:
                    res = pattern_year.search(one)
                    if not res:
                        one = year + one
                date_num = parse_datetime(one)
                if date_num:
                    list_datetime.append(date_num)
    return list_datetime


# 9999亿以内，转换是准确的
def num_to_dig(text: str):
    if text == '':
        return 0

    num_yi = 0
    num_wan = 0
    if '亿' in text:
        list_text = text.split('亿')
        text_yi = list_text[0]
        num_yi = _num_to_dig(text_yi) * 100000000
        list_text.pop(0)
        text = list_text[0]
    if '万' in text:
        list_text = text.split('万')
        text_wan = list_text[0]
        num_wan = _num_to_dig(text_wan) * 10000
        list_text.pop(0)
        text = list_text[0]
    num_left = _num_to_dig(text)
    num_total = num_yi + num_wan + num_left
    return num_total


# 以下方法，十万以内是准确的，以上解析错误
def _num_to_dig(text: str):
    if text == '':
        return 0
    m = re.match(r"\d+", text)
    if m:
        return int(m.group(0))
    text = re.sub('[元整]+', '', text)

    rsl = 0
    unit = 1
    for item in text[::-1]:
        if item in UTIL_CN_UNIT.keys():
            unit = UTIL_CN_UNIT[item]
        elif item in UTIL_CN_NUM.keys():
            num = UTIL_CN_NUM[item]
            rsl += num * unit
        else:
            print('【解析中文数字出错，内容为：%s】' % text)
            return 0
    if rsl and rsl < unit:
        rsl += unit
    return rsl



def year_to_dig(year: str):
    res = ''
    for item in year:
        if item in UTIL_CN_NUM.keys():
            res = res + str(UTIL_CN_NUM[item])
        else:
            res = res + item
    m = re.match(r"\d+", res)
    if m:
        if len(m.group(0)) == 2:
            return int(datetime.today().year / 100) * 100 + int(m.group(0))
        else:
            return int(m.group(0))
    else:
        print('【解析中文年数字出错，内容为：%s】' % year)
        return None


def parse_datetime(text: str):
    # print('进来的日期是：', text)
    if text is None or len(text) == 0:
        return None

    m = pattern_date_search.search(text)
    if m is not None:
        res = {
            "year": m.group(1).strip() or str(datetime.today().year),
            "month": m.group(2).strip(),
            "day": m.group(3).strip(),
            "hour": m.group(5).strip() or '0',
            "minute": m.group(6).strip() or '0',
            "second": m.group(7).strip() or '0',
        }
        if int(res['hour']) > 23:
            res['hour'] = '0'
            res['minute'] = '0'
            res['second'] = '0'

        params = {}
        for name in res:
            if res[name] and (len(res[name]) > 0):
                if name == 'year':
                    tmp = year_to_dig(res[name])
                else:
                    tmp = num_to_dig(res[name])

                params[name] = int(tmp)

        target_date = datetime.today().replace(**params)
        is_pm = m.group(4).strip()
        if is_pm:
            if is_pm == u'下午' or is_pm == u'晚上' or is_pm == '中午':
                hour = target_date.time().hour
                if hour < 12:
                    target_date = target_date.replace(hour=hour + 12)
        return target_date.strftime('%Y-%m-%d %H:%M:%S')
    else:
        m = pattern_date.search(text)
        if m is not None:
            res = {
                "year": m.group(1).strip() or str(datetime.today().year),
                "month": m.group(2).strip(),
                "day": m.group(3).strip(),
            }

            params = {}
            for name in res:
                if res[name] and (len(res[name]) > 0):
                    if name == 'year':
                        tmp = year_to_dig(res[name])
                    else:
                        tmp = num_to_dig(res[name])

                    params[name] = int(tmp)

            target_date = datetime.today().replace(**params)
            return target_date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return None


def transfer_to_yuan(value: str):
    pattern = re.compile(r'[0-9]+(\.[0-9]+)*')  # 整数或小数
    res = pattern.search(value)
    num = res.group(0)
    num = float(num)
    if '亿' in value:
        num = num * 10000 * 10000
        return int(num)
    if '千万' in value:
        num = num * 10000 * 1000
        return int(num)
    if '百万' in value:
        num = num * 10000 * 100
        return int(num)
    if '万' in value:
        num = num * 10000
        return int(num)
    if '千' in value:
        num = num * 1000
        return int(num)
    if '百' in value:
        num = num * 100
        return int(num)
    return int(num)


def percent_to_num(value: str):
    result = re.compile(r'[0-9]+\.?[0-9]*').search(value)
    if not result:
        return 0
    number = float(result.group(0))
    if '%' in value or '％' in value:
        number = round(number / 100, 6)
    return number


def parse_regex(re_pattern: Pattern, value: str, many=False):
    if many:
        matches = re_pattern.finditer(value)
        return [regex_match(match, re_pattern) for match in matches]
    else:
        match = re_pattern.search(value)
        return regex_match(match, re_pattern)


def regex_match(match, re_pattern):
    if not match:
        print('【正则：%s, 匹配不成功！！！】' % re_pattern)
        return None
    else:
        string = match.group()
        groups = match.groups()
        group_dict = match.groupdict()
        if group_dict:
            return group_dict
        if groups:
            return groups[0] if len(groups) == 1 else groups
        return string


def get_content(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = ''
        for l in f:
            content += l.strip()
        return content


def stop_words(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        return [l.strip() for l in f]


# 定义高频词统计的函数，其输入是一个词的数组
def get_TF(words, topK=10):
    tf_dic = {}
    for w in words:
        tf_dic[w] = tf_dic.get(w, 0) + 1  # get() 函数返回指定键的值，如果值不在字典中返回默认值。
    return sorted(tf_dic.items(), key=lambda x: x[1], reverse=True)[:topK]


def jieba_cut(text, userdict_path=None, stopword_path=None):
    if userdict_path:
        jieba.load_userdict(userdict_path)
    if stopword_path:
        split_word = [x for x in jieba.cut(text) if x not in stop_words(stopword_path)]
    else:
        split_word = [x for x in jieba.cut(text)]
    return split_word
