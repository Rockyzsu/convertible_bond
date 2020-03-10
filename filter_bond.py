# -*-coding=utf-8-*-

# @Time : 2019/5/12 16:52
# @File : filter_bond.py
# 根据条件选择债券

import pymongo
import config
import tushare as ts
from settings import get_engine,llogger
import pandas as pd
import datetime
import numpy as np

# pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', None)

# 条件
OUTSTANDING_MAX = 70  # 流通 x亿
TOTAL_MAX = 500  # 总市值

YIJIALU = 10  # 溢价率
ZZ_PRICE = 110  # 转债价格

REMAIN_SHARE = 5  # 转股剩余比例

today = datetime.datetime.now().strftime('%Y-%m-%d')
# today='2019-11-15'

engine = get_engine('db_stock', 'local')

jsl_df = pd.read_sql('tb_bond_jisilu', con=engine)
basic_df = pd.read_sql('tb_basic_info', con=engine, index_col='index')
engine_daily = get_engine('db_daily','local')
db=pymongo.MongoClient(config.mongodb_host,config.mongodb_port)

price_df = pd.read_sql(today, con=engine_daily)

logger = llogger('log/filter_bond.log')
# 市值选择
def market_share(zg_df):
    if len(zg_df)==0:
        return zg_df

    for i in zg_df.index:
        p = price_df[price_df['code'] == zg_df.loc[i]['code']]['trade'].values[0]
        ltgb = zg_df.loc[i]['outstanding']
        total_gb = zg_df.loc[i]['totals']
        lt = round(p * ltgb, 1)  # 流通市值
        zg_df.loc[i, 'outstanding_shizhi'] = lt
        zsz = round(p * total_gb, 1)  # 总市值
        zg_df.loc[i, 'totals_shizhi'] = zsz

    zg_df = zg_df[(zg_df['outstanding_shizhi'] < OUTSTANDING_MAX) & (zg_df['totals_shizhi'] < TOTAL_MAX)]
    zg_df = zg_df.sort_values(by='outstanding_shizhi')
    zg_df.reset_index(inplace=True, drop=True)
    # print(zg_df[['code','name','outstanding_shizhi','totals_shizhi']])

    return zg_df


# 双低
def double_low(jsl_df):
    jsl_df = jsl_df[(jsl_df['溢价率'] < YIJIALU) & (jsl_df['可转债价格'] < ZZ_PRICE)]
    # print(jsl_df)
    return jsl_df


# 剩余未转股
def remain_share(jsl_df):
    jsl_df['剩余比例'] = jsl_df['剩余规模'].astype(np.float) / jsl_df['发行规模'].astype(np.float) * 100
    return jsl_df[jsl_df['剩余比例'] > REMAIN_SHARE]


# 计算一周，一个月，一个季度跌幅最多的债
# work
def weekly_drop_rank(current=True):

    if current:
        today = datetime.datetime.today()
    else:
        # 修复问题使用
        today = datetime.datetime.strptime('2019-11-15','%Y-%m-%d')

    code_list = jsl_df['可转债代码'].values
    name_list = jsl_df['可转债名称'].values
    yjl = jsl_df['溢价率'].values


    week = today + datetime.timedelta(days=-7)
    month = today+ datetime.timedelta(days=-31)
    today_str = today.strftime('%Y-%m-%d')
    week_str = week.strftime('%Y-%m-%d')
    month_str = month.strftime('%Y-%m-%d')
    m_result={}
    w_result={}
    price_dict ={}
    code_dict=dict(zip(code_list,name_list))
    yjl_dict=dict(zip(code_list,yjl))
    for code in code_dict:

        # 周线,获取下跌的幅度
        m_percent,w_percent,last_close = get_low_price(code=code,start=month_str)
        price_dict[code]=last_close
        w_result[code]=w_percent
        m_result[code]=m_percent

    m_result_list = list(sorted(m_result.items(),key=lambda x:x[1]))
    w_result_list = list(sorted(w_result.items(),key=lambda x:x[1]))

    # TODO 把溢价率也写入
    # 按月
    logger.info('月度数据')
    for i in m_result_list:
        logger.info(f'{i[0]} {code_dict.get(i[0])} : {i[1]}%')

        d={}
        d['代码']=i[0]
        d['名称']=code_dict.get(i[0])
        d['当前价格']=price_dict.get(i[0])
        d['溢价率']=yjl_dict.get(i[0])
        d['跌幅']=i[1]
        d['更新日期']=today_str
        db['db_price_drop'][f'{today_str}_month_drop'].insert_one(d)

    logger.info('\n周度数据')
    for i in w_result_list:
        logger.info(f'{i[0]} {code_dict.get(i[0])} : {i[1]}%')
        d={}
        d['代码']=i[0]
        d['名称']=code_dict.get(i[0])
        d['当前价格']=price_dict.get(i[0])

        d['溢价率']=yjl_dict.get(i[0])
        d['跌幅']=i[1]
        d['更新']=today_str
        db['db_price_drop'][f'{today_str}_week_drop'].insert_one(d)


def get_low_price(code,start):
    df = ts.get_k_data(code=code,start=start)
    # print(df)
    pre_closed = df.iloc[0]['close']
    last_closed = df.iloc[-1]['close']
    m_percent = round((last_closed-pre_closed)/pre_closed*100,2)

    try:
        w_pre_closed = df.iloc[-6]['close']
    except Exception as e:
        w_percent=0
        logger.info(f'新债{code}')
    else:
        w_percent =  round((last_closed-w_pre_closed)/w_pre_closed*100,2)

    return m_percent,w_percent,last_closed



# 所有功能放在一起
def main():
    global jsl_df
    jsl_df = remain_share(jsl_df)
    jsl_df = double_low(jsl_df)
    zg_list = list(jsl_df['正股代码'].values)
    zg_df = basic_df[basic_df['code'].isin(zg_list)]
    zg_df = market_share(zg_df)
    con = get_engine('double_low_bond', 'local')
    zg_df.to_sql('double_low_{}'.format(today), con=con, if_exists='replace')


if __name__ == '__main__':
    if ts.is_holiday(today):
        exit(0)
    main()
