# -*-coding=utf-8-*-

# @Time : 2019/5/12 16:52
# @File : filter_bond.py
# 根据条件选择债券
import tushare as ts
from setting import get_engine
import pandas as pd
import datetime
import numpy as np
# pd.set_option('expand_frame_repr', False)
pd.set_option('display.max_rows',None)

# 条件
OUTSTANDING_MAX=70 # 流通 x亿
TOTAL_MAX=500 # 总市值

YIJIALU = 10 # 溢价率
ZZ_PRICE = 110 # 转债价格

REMAIN_SHARE = 5 # 转股剩余比例

today = datetime.datetime.now().strftime('%Y-%m-%d')
# today='2019-07-01'

engine = get_engine('db_stock',True)
jsl_df = pd.read_sql('tb_bond_jisilu',con=engine)
basic_df = pd.read_sql('tb_basic_info',con=engine,index_col='index')
engine_daily = get_engine('db_daily')
price_df = pd.read_sql(today,con=engine_daily)


# 市值选择
def market_share(zg_df):

    for i in zg_df.index:

        p=price_df[price_df['code']==zg_df.loc[i]['code']]['trade'].values[0]
        ltgb=zg_df.loc[i]['outstanding']
        total_gb=zg_df.loc[i]['totals']
        lt=round(p*ltgb,1) # 流通市值
        zg_df.loc[i,'outstanding_shizhi']=lt
        zsz=round(p*total_gb,1) # 总市值
        zg_df.loc[i,'totals_shizhi']=zsz



    zg_df=zg_df[(zg_df['outstanding_shizhi']<OUTSTANDING_MAX) & (zg_df['totals_shizhi']<TOTAL_MAX)]
    zg_df=zg_df.sort_values(by='outstanding_shizhi')
    zg_df.reset_index(inplace=True,drop=True)
    # print(zg_df[['code','name','outstanding_shizhi','totals_shizhi']])

    return zg_df

# 双低
def double_low(jsl_df):
    jsl_df=jsl_df[(jsl_df['溢价率']<YIJIALU) & (jsl_df['可转债价格']<ZZ_PRICE)]
    # print(jsl_df)
    return jsl_df

# 剩余未转股
def remain_share(jsl_df):
    jsl_df['剩余比例']=jsl_df['剩余规模'].astype(np.float)/jsl_df['发行规模'].astype(np.float)*100
    return jsl_df[jsl_df['剩余比例']>REMAIN_SHARE]

def main(jsl_df):
    jsl_df=remain_share(jsl_df)
    jsl_df=double_low(jsl_df)
    zg_list = list(jsl_df['正股代码'].values)
    zg_df = basic_df[basic_df['code'].isin(zg_list)]
    zg_df = market_share(zg_df)
    # print(zg_df)
    con=get_engine('db_bond',local=True)
    zg_df.to_sql('double_low_{}'.format(today),con=con)

if __name__=='__main__':
    if ts.is_holiday(today):
        exit(0)

    main(jsl_df)