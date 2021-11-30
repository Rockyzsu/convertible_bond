# -*-coding=utf-8-*-
import sys

sys.path.append('..')
import requests
import re
import pandas as pd
from configure.settings import DBSelector
from configure.util import read_web_headers_cookies
from common.BaseService import BaseService
from sqlalchemy.types import DATE
import js2py
import numpy as np
'''
可转债综合概览
'''
DB = DBSelector()

TABLE_NAME = 'bond_overview'


class CBSpider(BaseService):

    def __init__(self, db=None):
        super(CBSpider, self).__init__('../log/bond_overview.log')

        self.url = ''
        self.params = {
            # TODO 添加 params query 参数
        }

        self.headers_, self.cookies = read_web_headers_cookies('jsl',headers=True, cookies=True)

        if db and db == 'mongo':
            # 数据库选择
            self.db = DB.mongo('qq')
            self.doc = db['db_stock']['']  # 怎么空了

    def get(self, url=None, _json=False, binary=False, retry=5):

        try:
            r = requests.get(
                url=self.url,
                params=self.params,
                headers=self.headers_,
                cookies=self.cookies)

        except Exception as e:
            self.logger.error(e)
            return None
        else:
            if _json:
                return r.json()
            elif binary:
                return r.content
            else:
                return r.text

    def post(self, url, post_data, _json=False, binary=False, retry=5):
        try:
            r = requests.post(
                url=self.url,
                headers=self.headers,
                data=post_data
            )
        except:
            return None
        else:
            return r.text

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
    def prepare_data(self,data_dict):
        total_len = len(data_dict['amount'])
        for k,v in data_dict.items():
            if len(v)!=total_len:
                delta = total_len-len(v)
                data_dict[k].extend([np.nan]*delta)
        return data_dict

    def process(self, data, history=False):
        '''
        数据存储        
        '''

        data_, date_ = data[0], data[1]

        data = js2py.eval_js(data_).to_dict()
        date = js2py.eval_js(date_).to_list()
        data=self.prepare_data(data)
        df = pd.DataFrame(data)
        origin_columns = list(df.columns)
        df['date'] = date
        origin_columns.insert(0, 'date')

        df = df.reindex(columns=origin_columns)

        if history == True:
            '''
            历史数据
            '''
            engine = DB.get_engine('db_stock', 'qq')

            try:
                df.to_sql(TABLE_NAME, con=engine, index_label='id',
                          if_exists='replace', dtype={'date': DATE})
            except Exception as e:
                print(e)

        else:
            '''
            当天数据
            '''
            last_data = df.iloc[-1]
            # self.today = '2021-05-14'
            if last_data['date'] == self.today:
                insert_data = list(last_data.values)
                insert_data = self.convert(insert_data)
                join_str = ','.join(['%s'] * 28)
                # print(insert_data)
                self.save_mysql(insert_data, join_str)

    def save_mysql(self, insert_data, join_str):
        conn = DBSelector().get_mysql_conn('db_stock', 'qq')
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT id FROM db_stock.{TABLE_NAME} order by id desc limit 1')
        idx = cursor.fetchone()
        idx = idx[0]

        # insert_sql = f'''insert into `bond_overview` (`id`,`date`, `price`,`volume`,`amount`,`count`,`avg_price`,`mid_price`,`avg_premium_rt`,  `avg_ytm_rt`,  `increase_val`,  `increase_rt`,  `turnover_rt`,  `price_90`,  `price_90_100`,  `price_100_110`,  `price_110_120`,  `price_120_130`,  `price_130`,  `idx_price`,  `idx_increase_rt`）value ({join_str})'''
        insert_sql = f'''insert into `{TABLE_NAME}` values ({join_str})'''

        insert_data.insert(0, idx + 1)
        cursor.execute(insert_sql, insert_data)
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


    def run(self):
        content = self.get()
        result = self.parse(content)
        self.process(result)


def main():
    processor = CBProcess()
    processor.run()


if __name__ == '__main__':
    main()
