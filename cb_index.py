# -*-coding=utf-8-*-

# @Time : 2019/2/11 14:28
# @File : cb_index.py
# 可转债指数
import datetime
import re
import pandas as pd
import requests
from settings import get_mysql_conn,llogger
import tushare as ts
logger = llogger('log/'+'cb_index.log')

# 获取当天的记录
def get_today_index():
    url='https://www.jisilu.cn/data/cbnew/cb_index_quote/'
    headers = {'Host': 'www.jisilu.cn',
               'X-Requested-With': 'XMLHttpRequest',
               'Referer': 'https://www.jisilu.cn/data/cbnew/',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    r = requests.get(
        url=url,
        headers=headers
    )

    # print(r.text)
    data_ = r.json()
    price = data_.get('cur_index')
    volume = data_.get('volume')
    amount = data_.get('amount')
    count = data_.get('count')  # 数量
    increase_val = data_.get('cur_increase_val')  # 涨跌额
    increase_rt = data_.get('cur_increase_rt')  # 涨跌幅

    con = get_mysql_conn('db_stock', 'local')
    cursor = con.cursor()
    current=datetime.datetime.now().strftime('%Y-%m-%d')
    update_data_sql = '''
    insert into `tb_cb_index` (`日期`,`指数`,`成交额(亿元)`,`涨跌`,`涨跌额`,`转债数目`,`剩余规模`) values (%s,%s,%s,%s,%s,%s,%s);
    '''
    value_tuple = (
        current, price, volume, increase_val, increase_rt, count,amount)

    print(value_tuple)
    try:
        cursor.execute(update_data_sql, value_tuple)
    except Exception as e:
        print(value_tuple)
        print(e)
        con.rollback()
    else:
        con.commit()
        logger.info('爬取成功并入库')

# 获取历史记录
def history_data():
    url = 'https://www.jisilu.cn/data/cbnew/cb_index/'
    headers = {'Host': 'www.jisilu.cn',
               'Referer': 'https://www.jisilu.cn/data/cbnew/',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
    r = requests.get(
        url=url,
        headers=headers
    )
    r.encoding = 'utf8'

    # print(r.text)

    content = r.text
    date = re.search('var __date = (.*?);', content, re.S).group(1)
    data = re.search('var __data = (.*?);', content, re.S).group(1)
    date_ = eval(date)
    data_ = eval(data)
    price = data_.get('price')
    volume = data_.get('volume')
    amount = data_.get('amount')
    count = data_.get('count')  # 数量
    increase_val = data_.get('increase_val')  # 涨跌额
    increase_rt = data_.get('increase_rt')  # 涨跌幅

    # df = pd.DataFrame({'日期':date_,'指数':price,'成交额': amount,'涨跌':increase_val,'涨跌额':increase_rt,'转债数目':increase_rt})
    con = get_mysql_conn('db_stock', 'local')
    cursor = con.cursor()

    create_sql = '''
    create table if not exists tb_cb_index (`日期` date ,`指数` float ,`成交额(亿元)` float,`涨跌` float ,`涨跌额` float ,`转债数目` float ,`剩余规模` float )
    '''

    try:
        cursor.execute(create_sql)
    except Exception as e:
        print(e)
        con.rollback()
    else:
        con.commit()

    update_data_sql = '''
    insert into `tb_cb_index` (`日期`,`指数`,`成交额(亿元)`,`涨跌`,`涨跌额`,`转债数目`,`剩余规模`) values (%s,%s,%s,%s,%s,%s,%s);
    '''
    for index, item in enumerate(date_):
        value_tuple = (
        item, price[index], volume[index], increase_val[index], increase_rt[index], count[index],amount[index])

        try:
            cursor.execute(update_data_sql, value_tuple)
        except Exception as e:
            print(value_tuple)
            print(e)
            con.rollback()
        else:
            con.commit()


if __name__ == '__main__':
    current = datetime.datetime.now().strftime('%Y-%m-%d')
    logger.info('Start')
    con=ts.get_apis()
    if ts.is_holiday(current):
        logger.info('Holiday')
        ts.close_apis(con)
        exit()
    else:
        # history_data()  # 第一次获取历史数据， 后面获取每一天的数据
        get_today_index()
        ts.close_apis(con)
