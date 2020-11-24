# -*-coding=utf-8-*-

# @Time : 2019/5/12 16:52
# @File : filter_bond.py
# 根据条件选择债券

import tushare as ts
import pandas as pd
import datetime
import numpy as np

# pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows', None)

# 条件
OUTSTANDING_MAX = 70  # 流通 x亿
TOTAL_MAX = 500  # 总市值

YIJIALU = 10  # 溢价率
ZZ_PRICE = 120  # 转债价格

REMAIN_SHARE = 5  # 转股剩余比例


# 市值选择
def market_share(zg_df, price_df):
    if len(zg_df) == 0:
        return zg_df

    for index in zg_df.index:
        price = price_df[price_df['code'] == zg_df.loc[index]['code']]['trade'].values[0]
        ltgb = zg_df.loc[index]['outstanding']
        total_gb = zg_df.loc[index]['totals']
        lt = round(price * ltgb, 1)  # 流通市值
        zg_df.loc[index, 'outstanding_shizhi'] = lt
        zsz = round(price * total_gb, 1)  # 总市值
        zg_df.loc[index, 'totals_shizhi'] = zsz

    zg_df = zg_df[(zg_df['outstanding_shizhi'] <= OUTSTANDING_MAX) & (zg_df['totals_shizhi'] <= TOTAL_MAX)]
    zg_df = zg_df.sort_values(by='outstanding_shizhi')
    zg_df.reset_index(inplace=True, drop=True)
    # print(zg_df[['code','name','outstanding_shizhi','totals_shizhi']])

    return zg_df


# 双低
def double_low(jsl_df):
    jsl_df = jsl_df[(jsl_df['溢价率'] <= YIJIALU) & (jsl_df['可转债价格'] <= ZZ_PRICE)]
    # print(jsl_df)
    return jsl_df


# 剩余未转股
def remain_share(jsl_df):
    jsl_df['剩余比例'] = jsl_df['剩余规模'].astype(np.float) / jsl_df['发行规模'].astype(np.float) * 100
    return jsl_df[jsl_df['剩余比例'] > REMAIN_SHARE]


def get_low_price(code, start, end=datetime.date.today().strftime('%Y-%m-%d')):
    # 获取某个股票在一个阶段的最低价
    retry_max = 5
    try_time = 0
    while try_time < retry_max:
        try:
            df = ts.get_k_data(code=code, start=start, end=end)
        except Exception as e:
            try_time += 1
        else:
            break

    if retry_max == try_time:
        return None, None, None

    pre_closed = df.iloc[0]['close']
    last_closed = df.iloc[-1]['close']
    m_percent = round((last_closed - pre_closed) / pre_closed * 100, 2)

    try:
        w_pre_closed = df.iloc[-6]['close']
    except Exception as e:
        w_percent = 0
        # logger.info(f'新债{code}')
    else:
        w_percent = round((last_closed - w_pre_closed) / w_pre_closed * 100, 2)

    return m_percent, w_percent, last_closed


# 所有功能放在一起
def main():
    global jsl_df

    jsl_df_ = remain_share(jsl_df)
    jsl_df_ = double_low(jsl_df_)
    zg_list = list(jsl_df_['正股代码'].values)
    zg_df = basic_df[basic_df['code'].isin(zg_list)]
    zg_df = market_share(zg_df, price_df)
    con = DB.get_engine('double_low_bond', 'qq')
    zg_df.to_sql('double_low_{}'.format(today), con=con, if_exists='replace')
