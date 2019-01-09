# -*-coding=utf-8-*-

# @Time : 2019/1/2 8:53
# @File : bond_low_down_price.py
# 找出可转债没有调整转股价的
import datetime

import pymongo
import tushare as ts
import pandas as pd
import numpy as np
from setting import get_engine
import re


def get_low_down(x):
    x = x.replace(' ', '')
    try:
        ret = re.findall('连续(.*?)个交易日|任意(.*?)个连续交易', x)
        r = ret[0]
        if r[0]:
            ret = r[0]
        else:
            ret = r[1]
    except Exception as e:
        ret = None
    return ret


def get_low_down_least(x):
    x = x.replace(' ', '')
    x = x.replace('\r\n', '')
    try:
        ret = re.findall('至少有?(.*?)个交易日|有(.*?)个交易日', x)
        r = ret[0]
        if r[0]:
            ret = r[0]
        else:
            ret = r[1]
    except Exception as e:
        ret = None
    return ret


def get_percent(x):
    try:
        ret = re.findall('(\d+)%', x)[0]
    except:
        ret = None
    return ret


# 将中文转为 英文
def convert_ch_eng(x):

    map_dict = {'三十': 30, '二十': 20, '十五': 15, '十': 10, '\r有二十': 20}
    if x:
        x=re.sub('至少','',x)
        t = map_dict.get(x, None)
        if t:
            return t
        else:
            return x
    else:
        return None


def compare_date(x):
    # 转股日期转化
    zgrq = datetime.datetime.strptime(x, '%Y-%m-%d')
    after_one_month = datetime.datetime.now() + datetime.timedelta(days=30)
    if zgrq <= after_one_month:
        return True
    else:
        return False

# 设计一个计数器，如果低于一天就加1
def less_ratio(x):
    pass

def get_bond_low_down_possibility():
    engine = get_engine('db_stock', local='local')

    df = pd.read_sql('tb_bond_jisilu', con=engine)

    # df = df[df['下调次数'] == 0]

    df['需要的天数内'] = df['下修条件'].map(get_low_down)

    df['维持天数'] = df['下修条件'].map(get_low_down_least)

    df['低于比例'] = df['下修条件'].map(get_percent)
    df['当前比例'] = df['正股现价'] / df['最新转股价'] * 100
    df['当前比例'] = df['当前比例'].map(lambda x: round(x, 2))
    df['需要的天数内'] = df['需要的天数内'].map(convert_ch_eng)
    df['维持天数'] = df['维持天数'].map(convert_ch_eng)

    df = df[df['转股起始日'].map(compare_date) == True]
    tb_name = 'tb_bond_low_down_price_{}'.format(datetime.datetime.now().strftime('%Y-%m-%d'))

    del df['正股现价']
    del df['正股涨跌幅']
    del df['可转债涨幅']
    del df['下修条件']
    del df['成交额(万元)']
    del df['强制赎回条款']
    del df['回售']
    del df['下修提示']
    del df['发行规模']
    del df['剩余规模']
    del df['下调次数']

    df['更新日期'] = datetime.datetime.now().strftime('%Y-%m-%d')
    df.to_sql(tb_name, con=engine, if_exists='replace', index=None)


get_bond_low_down_possibility()