# 计算转债与正股的涨幅 以周为单位
import datetime

import pandas as pd
import tushare as ts
from setting import get_engine

engine=get_engine('db_stock')

def get_code():
    df = pd.read_sql('tb_bond_jisilu',engine)
    kzz_code,zg_code = df['可转债代码'].values,df['正股代码'].values
    return kzz_code,zg_code

def main():
    today = datetime.date.today()
    today_str = today.strftime('%Y-%m-%d')
    start = today+ datetime.timedelta(days=-14)
    start_str= start.strftime('%Y-%m-%d')
    kzz_code,zg_code = get_code()
    code_dict = dict(zip(kzz_code,zg_code))

    for code in code_dict:
        ret = ts.get_k_data(code,start=start_str,end=today_str,ktype='W')
        


if __name__=='__main__':
    main()