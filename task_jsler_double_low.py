# -*-coding=utf-8-*-
# @Time : 2019/9/2 9:35
# @File : send_bond_info.py
# 发送邮件的,集思录双底

from settings import DBSelector
import pandas as pd
import datetime
from settings import  llogger,send_from_aliyun, check_path
import tushare as ts

logger = llogger('log/task_jsler_double_low.log')
if not check_path('log'):
    logger.error('log创建路径出现问题！')

today = datetime.datetime.now().strftime('%Y-%m-%d')
DB = DBSelector()
con = DB.get_engine('db_stock', 'qq')


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


def get_df_data():
    df = pd.read_sql('tb_bond_jisilu', con=con)
    return df


def convert(df):
    df['grade'] = df['评级'].map(lambda x: map_rate(x))
    df['可转债综合价格'] = df['可转债价格'] + df['溢价率'] * df['grade']
    df = df.sort_values(by='可转债综合价格')
    df['剩余规模'] = df['剩余规模'].map(lambda x: round(float(x), 2))
    df = df[df['强赎日期'].isnull()]  # 去除强赎
    df = df[['可转债代码', '可转债名称', '可转债综合价格', '可转债价格', '溢价率', '评级', '剩余规模']].head(20)
    df = df.reset_index(drop=True)
    df['可转债名称'] = df['可转债名称'].map(lambda x: x.replace('转债', ''))
    return df


def save_mysql(df):
    conn2 = DB.get_engine('double_low_full', 'qq')
    df.to_sql(f'double_low_{today}', con=conn2, if_exists='replace')


def send_mail(df):
    send_content = df.to_html(index=False, border=1, justify='center')
    send_content = send_content.replace('class', 'cellspacing=\"0\" class')

    title = '{} 可转债综合价格前20名'.format(datetime.datetime.now().strftime('%Y-%m-%d'))

    try:
        send_from_aliyun(title, send_content, types='html')
    except Exception as e:
        logger.error('发送邮件出错')
        logger.error(e)
    else:
        logger.info('发送成功！')


def jsl_cb_double_low_monitor():
    '''
    JSL双底可转债
    :return:
    '''
    df = get_df_data()
    df = convert(df)
    save_mysql(df)
    send_mail(df)


if __name__ == '__main__':
    jsl_cb_double_low_monitor()

