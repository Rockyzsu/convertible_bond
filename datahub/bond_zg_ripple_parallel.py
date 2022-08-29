# 转债正股 波动率计算 并行版本
import datetime
import time

import akshare as ak
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor,as_completed


sign = ''  # 需要的话私信知识星球 星主


def get_bond_basic_info():
    HOST = ''
    PORT = ''
    host = 'http://{}:{}/{}'
    atction = 'info'
    data = {'sign': sign, 'args': None}
    resp = requests.post(
        url=host.format(HOST, PORT, atction), data=data,
    )

    ret_data = resp.json()['data']
    df = pd.DataFrame(ret_data)
    return df


def last_n_day(date, n, origin_fmt, target_fmt):
    return (datetime.datetime.strptime(date, origin_fmt) - datetime.timedelta(days=n)).strftime(target_fmt)


def get_iv(code, start_date, end_date):
    print('正在获取代码....{}'.format(code))
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date,
                                            adjust="qfq")
    iv = stock_zh_a_hist_df['涨跌幅'].std()
    return (code,iv)


def main():
    start_time = time.time()
    fmt = '%Y%m%d'
    jsl_bond_df = get_bond_basic_info()

    zg_code = jsl_bond_df['zg_code'].tolist()
    today = datetime.date.today().strftime(fmt)
    start_date = last_n_day(today, 30, fmt, fmt) # 默认30个自然日的日线波动率
    iv_dict = {}

    executor = ThreadPoolExecutor(max_workers=10)
    all_task =[]
    for code in zg_code:
        args=[code,start_date,today]
        task=executor.submit(lambda p: get_iv(*p),args)
        all_task.append(task)


    for future in as_completed(all_task):
        iv_tuple = future.result()
        iv_dict[iv_tuple[0]]=iv_tuple[1]
    print('all task done')
    print('time used {}'.format(time.time()-start_time))
    jsl_bond_df['iv'] = jsl_bond_df['zg_code'].map(lambda x: iv_dict.get(x))
    jsl_bond_df.to_excel('{}正股波动率.xlsx'.format(today), encoding='utf8')


if __name__ == '__main__':
    main()
