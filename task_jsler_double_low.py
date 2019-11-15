# -*-coding=utf-8-*-
# @Time : 2019/9/2 9:35
# @File : send_bond_info.py

from settings import get_engine
import pandas as pd
import datetime
from settings import jsl_mail_sender, llogger, send_aliyun, QQ_MAIL

logger = llogger('log/task_jsler_double_low.log')

today = datetime.datetime.now().strftime('%Y-%m-%d')


def cb_info():
    con = get_engine('db_stock', 'local')
    df = pd.read_sql('tb_bond_jisilu', con=con)

    df['可转债综合价格'] = df['可转债价格'] + df['溢价率']
    df = df.sort_values(by='可转债综合价格')
    df1 = df[['可转债代码', '可转债名称', '可转债综合价格', '可转债价格', '溢价率']].head(20)
    df1 = df1.reset_index(drop=True)
    send_content = df1.to_html()
    # send_content=send_content+'\n\n默认每周一开盘前发送一次，如果有其他需求请回复。\n'
    # send_content = send_content
    title = '{} 可转债综合价格前10名'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
    conn2 = get_engine('double_low_full')
    df1.to_sql(f'double_low_{today}',con=conn2)

    try:
        send_aliyun(title, send_content, QQ_MAIL,types='html')
        # print(QQ_MAIL)
        # jsl_mail_sender(title,send_content,types='html')
    except Exception as e:
        print('报错了')


if __name__ == '__main__':
    import tushare as ts

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cons = ts.get_apis()
    if ts.is_holiday(today):
        ts.close_apis(cons)
        exit()

    else:
        # TODO
        cb_info()

        ts.close_apis(cons)
