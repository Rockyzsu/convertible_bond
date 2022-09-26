# -*-coding=utf-8-*-
import sys

import re
import pandas as pd
sys.path.append('..')

from configure.settings import DBSelector

from configure.util import read_web_headers_cookies,send_message_via_wechat
from common.BaseService import BaseService
from sqlalchemy.types import DATE
import js2py
import numpy as np

'''
可转债综合概览, 各个价格的分段
'''


class CBSpider(BaseService):

    def __init__(self, db=None):
        super(CBSpider, self).__init__('../log/bond_overview.log')

        self.headers_, self.cookies = read_web_headers_cookies('jsl', headers=True, cookies=True)
        self.DB = DBSelector()
        if db and db == 'mongo':
            # 数据库选择
            self.db = self.DB.mongo('qq')
            self.doc = db['db_stock']['']  # 怎么空了
    @property
    def headers(self):
        return self.headers_


    def parse(self, content):
        '''
        页面解析
        '''
        # response = parsel.Selector(text=content)
        date = re.search('var __date = (\[.*?\]);', content, re.S)
        if date:
            date = date.group()

        data = re.search('var __data = ({.*?});', content, re.S)
        if data:
            data = data.group()

        return data, date

    def prepare_data(self, data_dict):
        total_len = len(data_dict['amount'])
        for k, v in data_dict.items():
            if len(v) != total_len:
                delta = total_len - len(v)
                data_dict[k].extend([np.nan] * delta)
        return data_dict

    def process(self, data, history=False):
        '''
        数据存储        
        '''

        data_, date_ = data[0], data[1]

        data = js2py.eval_js(data_).to_dict()
        date = js2py.eval_js(date_).to_list()
        data = self.prepare_data(data)
        df = pd.DataFrame(data)
        origin_columns = list(df.columns)
        df['date'] = date
        origin_columns.insert(0, 'date')

        df = df.reindex(columns=origin_columns)
        # TABLE_NAME = 'tb_{}'.format(self.today)
        if history == True:
            '''
            历史数据
            '''
            engine = self.DB.get_engine('bond_overview', 'qq')

            try:
                df.to_sql(self.TABLE_NAME, con=engine, index_label='id',
                          if_exists='replace', dtype={'date': DATE})
            except Exception as e:
                print(e)

        else:
            '''
            当天数据
            '''
            last_data = df.iloc[-1]
            # self.today = '2022-09-07' # 临时修改
            if last_data['date'] == self.today:
                insert_data = list(last_data.values)
                insert_data = self.convert(insert_data)
                join_str = ','.join(['%s'] * (len(insert_data) - 1))
                self.save_mysql(insert_data, join_str)

    def save_mysql(self, insert_data, join_str):

        conn = self.DB.get_mysql_conn('db_stock', 'qq')
        if conn is None:
            send_message_via_wechat('failed to connect to database {}'.format(self.__class__.__name__))
            return

        cursor = conn.cursor()
        cursor.execute(
            f'SELECT id FROM db_stock.{self.TABLE_NAME} order by id desc limit 1')
        idx = cursor.fetchone()
        idx = idx[0]
        print(join_str)
        # insert_sql = f'''insert into `bond_overview` (`id`,`date`, `price`,`volume`,`amount`,`count`,`avg_price`,`mid_price`,`avg_premium_rt`,  `avg_ytm_rt`,  `increase_val`,  `increase_rt`,  `turnover_rt`,  `price_90`,  `price_90_100`,  `price_100_110`,  `price_110_120`,  `price_120_130`,  `price_130`,  `idx_price`,  `idx_increase_rt`）value ({join_str})'''
        insert_sql = f'''insert into `{self.TABLE_NAME}` values ({join_str})'''
        insert_data.insert(0, idx + 1)
        try:
            cursor.execute(insert_sql, insert_data)
        except Exception as e:
            send_message_via_wechat('{}-{}'.format(self.__class__.__name__,e))
        else:
            conn.commit()

        conn.close()

    def convert(self, data_list):
        import numpy
        for index, value in enumerate(data_list):
            if type(data_list[index]) == numpy.float64:
                data_list[index] = float(data_list[index])
            elif type(data_list[index]) == numpy.int64:
                data_list[index] = int(data_list[index])

        return data_list


class CBProcess(CBSpider):

    def __init__(self):
        super(CBProcess, self).__init__()
        self.url = 'https://www.jisilu.cn/data/cbnew/cb_index/'
        self.TABLE_NAME = 'tb_{}'.format(self.today)

    def run(self):
        content = self.get(url=self.url)
        result = self.parse(content)
        self.process(result,True)


def main():
    processor = CBProcess()
    processor.run()


if __name__ == '__main__':
    main()
