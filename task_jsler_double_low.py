# -*-coding=utf-8-*-
# @Time : 2019/9/2 9:35
# @File : send_bond_info.py
# 发送邮件的,集思录双底

from settings import DBSelector
import pandas as pd
import datetime
from settings import llogger, send_from_aliyun
import tushare as ts

logger = llogger('log/task_jsler_double_low.log')
today = datetime.datetime.now().strftime('%Y-%m-%d')
DB = DBSelector()

def map_rate(x):
    map_dict = {
        'A+': 1,
        'AA-': 1.2,
        'AA': 1.4,
        'AA+': 1.6,
        'AAA': 1.8
    }
    x = x.replace(' ', '')
    return map_dict.get(x, 1)


def cb_info():
    con = DB.get_engine('db_stock', 'qq')
    df = pd.read_sql('tb_bond_jisilu', con=con)
    df['grade']=df['评级'].map(lambda x:map_rate(x))

    df['可转债综合价格'] = df['可转债价格'] + df['溢价率']*df['grade']
    df = df.sort_values(by='可转债综合价格')
    # df = df[df['强赎标志'] != 'Y']
    df1 = df[['可转债代码', '可转债名称', '可转债综合价格', '可转债价格', '溢价率','评级']].head(20)
    df1 = df1.reset_index(drop=True)
    send_content = df1.to_html()
    # send_content=send_content+'\n\n默认每周一开盘前发送一次，如果有其他需求请回复。\n'
    # send_content = send_content
    title = '{} 可转债综合价格前20名'.format(datetime.datetime.now().strftime('%Y-%m-%d'))
    conn2 = DB.get_engine('double_low_full','qq')
    df1.to_sql(f'double_low_{today}', con=conn2, if_exists='replace')

    try:
        send_from_aliyun(title, send_content, types='html')
    except Exception as e:
        logger.error('报错了')
        logger.error(e)
    else:
        logger.info('发送成功！')


if __name__ == '__main__':
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cons = ts.get_apis()

    if ts.is_holiday(today):
        ts.close_apis(cons)
        exit()

    else:
        cb_info()
        ts.close_apis(cons)

