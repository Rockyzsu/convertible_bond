# -*-coding=utf-8-*-

# @Time : 2019/2/11 14:28
# @File : cb_index.py
# 可转债指数
import re
import sys
sys.path.append('..')
import requests
from configure.settings import DBSelector
from common.BaseService import BaseService

# 获取当天的记录
class CBIndexJSL(BaseService):
    def __init__(self):
        super(CBIndexJSL, self).__init__('../log/cb_index.log')
        self.db = DBSelector()
        self.to_mysql = False


    def get_today_index(self):
        url = 'https://www.jisilu.cn/data/cbnew/cb_index_quote/'
        headers = {'Host': 'www.jisilu.cn',
                   'X-Requested-With': 'XMLHttpRequest',
                   'Referer': 'https://www.jisilu.cn/data/cbnew/',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
        r = requests.get(
            url=url,
            headers=headers
        )

        data_ = r.json()
        price = data_.get('cur_index')
        volume = data_.get('volume')
        amount = data_.get('amount')
        count = data_.get('count')  # 数量
        increase_val = data_.get('cur_increase_val')  # 涨跌额
        increase_rt = data_.get('cur_increase_rt')  # 涨跌幅
        current = self.today
        value_tuple = (current, price, volume, increase_val, increase_rt, count, amount)
        # print(value_tuple)
        self.save_mysql(value_tuple)

    def save_mysql(self, data):
        update_data_sql = '''
        insert into `tb_cb_index` (`日期`,`指数`,`成交额(亿元)`,`涨跌`,`涨跌额`,`转债数目`,`剩余规模`) values (%s,%s,%s,%s,%s,%s,%s);
        '''
        con = self.db.get_mysql_conn('db_stock', 'qq')
        self.execute(update_data_sql, data, con)

    # 获取历史记录
    def history_data(self):
        import demjson

        url = 'https://www.jisilu.cn/data/cbnew/cb_index/'
        headers = {'Host': 'www.jisilu.cn',
                   'Referer': 'https://www.jisilu.cn/data/cbnew/',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}
        r = requests.get(
            url=url,
            headers=headers
        )
        r.encoding = 'utf8'

        content = r.text
        date = re.search('var __date = (.*?);', content, re.S).group(1)
        data = re.search('var __data = (.*?);', content, re.S).group(1)
        data_py = demjson.decode(data)
        date_py = demjson.decode(date)

        print(data_py)
        print(date_py)

        # print(data_py.get('price'))

        # date_ = eval(date)
        # data_ = eval(data)
        # price = data_py.get('price')
        # volume = data_py.get('volume')
        # amount = data_.get('amount')
        # count = data_.get('count')  # 数量
        # increase_val = data_.get('increase_val')  # 涨跌额
        # increase_rt = data_.get('increase_rt')  # 涨跌幅
        # if self.to_mysql:
        #
        #     con = self.db.get_mysql_conn('db_stock', 'qq')
        #
        #     create_sql = '''
        #     create table if not exists tb_cb_index_test (`日期` date ,`指数` float ,`成交额(亿元)` float,`涨跌` float ,`涨跌额` float ,`转债数目` float ,`剩余规模` float )
        #     '''
        #     self.execute(create_sql, (), con)
        #
        #     update_data_sql = '''
        #     insert into `tb_cb_index_test` (`日期`,`指数`,`成交额(亿元)`,`涨跌`,`涨跌额`,`转债数目`,`剩余规模`) values (%s,%s,%s,%s,%s,%s,%s);
        #     '''
        #     for index, item in enumerate(date_):
        #         value_tuple = (
        #             item, price[index], volume[index], increase_val[index], increase_rt[index], count[index], amount[index])
        #
        #         self.execute(update_data_sql, value_tuple, con)
        #
        # else:
        #     # 存excel
        #     import pandas as pd
        #
        #     df = pd.DataFrame({'date':date_py,'index':data_py.get('price')})
        #     df.to_excel('../data/jsl_index.xlsx',encoding='utf8')
        #

def main():
    app = CBIndexJSL()
    app.get_today_index()

    # 获取历史数据 用于分析
    # app.history_data()

if __name__ == '__main__':
    main()
