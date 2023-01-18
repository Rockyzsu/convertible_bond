import sys
import pandas as pd
import os
import numpy as np
import datetime
sys.path.append('..')
from configure.settings import get_tushare_pro

pro = get_tushare_pro()
cal_df = pro.trade_cal(exchange='SSE', start_date='20220101', end_date='20221001')

def transform_date(x):
    return datetime.datetime.strptime(x,'%Y%m%d').strftime('%Y-%m-%d')

trade_cal = cal_df['trade_date'].astype('str').tolist()
trade_cal = list(map(transform_date,trade_cal))

ninwen_data_folder = '/home/xda/nust/Nutstore/量化/宁稳'




def one_date_df(date):
    file='{}_宁稳.xlsx'.format(date)
    try:
        bond_df = pd.read_excel(os.path.join(ninwen_data_folder,file))
    except Exception as e:
        print(e)
        return pd.DataFrame(data=[],index=[date])

    price_series = bond_df['转债价格']
    area = list(range(90,1500,10))
    mylabel = [str(i) for i in area]

    result = pd.cut(price_series,bins=area,labels=mylabel[:-1])

    result_dict ={}
    for i in result.index:
        t = result[i]
        if t is np.nan:
            print('error',i,t)

        else:
            t=int(t)

        if t>=200:
            result_dict.setdefault('>200',0)
            result_dict['>200']+=1
        else:
            result_dict.setdefault(str(t),0)
            result_dict[str(t)]+=1

    tmp_df = pd.DataFrame(result_dict,index=[date])

    return tmp_df


df_list = []
for date in trade_cal:
    tmp_df = one_date_df(date)
    df_list.append(tmp_df)


all_date_df = pd.concat(df_list)

all_date_df.to_csv('bond_info20220930.csv',encoding='utf8')

import bar_chart_race as bcr
bcr.bar_chart_race(all_date_df, 'bondinfo.gif',
                #    fixed_order=['90', '100', '110', '120', '130', '140',
                #                 '150', '160','170',	'180', '190','>200',],
                   orientation='v',
                   steps_per_period=5,
                   )
