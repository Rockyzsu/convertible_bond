# 转债正股 波动率计算
import datetime
import akshare as ak
import pandas as pd
import requests

sign = '' # 需要的话私信星主


def get_bond_basic_info():
    HOST = ''
    PORT = ''
    host = 'http://{}:{}/{}'
    atction = 'info'
    data = {'sign': sign, 'args': None}
    resp = requests.post(
        url=host.format(HOST,PORT,atction), data=data,
   )

    ret_data = resp.json()['data']
    df = pd.DataFrame(ret_data)
    return df

def last_n_day(date, n, origin_fmt, target_fmt):
    return (datetime.datetime.strptime(date, origin_fmt) - datetime.timedelta(days=n)).strftime(target_fmt)

def main():
    fmt = '%Y%m%d'
    jsl_bond_df=get_bond_basic_info()

    zg_code = jsl_bond_df['zg_code'].tolist()
    today=datetime.date.today().strftime(fmt)
    start_date=last_n_day(today,30,fmt,fmt)
    iv_dict={}

    for code in zg_code:
        print('正在获取代码....{}'.format(code))
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=today, adjust="qfq")
        iv = stock_zh_a_hist_df['涨跌幅'].std()
        iv_dict[code]=iv

    jsl_bond_df['iv']=jsl_bond_df['zg_code'].map(lambda x:iv_dict.get(x))
    jsl_bond_df.to_excel('{}正股波动率.xlsx'.format(today),encoding='utf8')

if __name__ == '__main__':
    main()