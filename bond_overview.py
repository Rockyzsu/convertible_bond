# -*-coding=utf-8-*-

import time
import requests
import json
import pymongo
import pymysql
# from config import get_proxy
import parsel
import re
import datetime
import pandas as pd
from settings import DBSelector
from sqlalchemy.types import DATE
'''
可转债综合概览
'''


class CBSpider(object):

    def __init__(self, db=None):

        self.url = ''
        self.params = {
            # TODO 添加 params query 参数
        }
        self.headers = {
            # TODO 添加headers
        }

        self.cookie = {
            # TODO 添加cookies

        }

        if db and db == 'mongo':
            # 数据库选择
            self.db = pymongo.MongoClient()
            self.doc = db['']['']

    def get(self, _josn=False, binary=False):

        try:
            r = requests.get(
                url=self.url,
                params=self.params,
                headers=self.headers,
                cookies=self.cookie)

        except Exception as e:
            print(e)
            return None
        else:
            if _josn:
                return r.json()
            elif binary:
                return r.content
            else:
                return r.text

    def post(self, post_data):
        try:
            r = requests.post(
                url=self.url,
                headers=self.headers,
                data=post_data
            )
        except:
            return None
        else:
            return text

    def parse(self, content):
        '''
        页面解析
        '''
        # response = parsel.Selector(text=content)
        date = re.search('var __date = (\[.*?\]);', content, re.S)
        if date:
            date = date.group(1)

        data = re.search('var __data = ({.*?});', content, re.S)
        if data:
            data = data.group(1)

        return data, date

    def process(self, data, history=True):
        '''
        数据存储        
        '''
        print(data)
        data_, date_ = data[0], data[1]
        data = eval(data_)
        date = eval(date_)

        # print(data)
        # print(date)
        df = pd.DataFrame(data)
        origin_columns = list(df.columns)
        df['date'] = date
        origin_columns.insert(0, 'date')
        # print(df.head(5))
        # print(origin_columns)
        df = df.reindex(columns=origin_columns)
        # print(df.head(5))
        if history == True:
            '''
            历史数据
            '''
            engine = DBSelector().get_engine('db_stock', 'qq')

            try:
                df.to_sql('bond_overview', con=engine, index_label='id',
                          if_exists='replace', dtype={'date': DATE})
            except Exception as e:
                print(e)

            else:
                print('pass')
        else:
            '''
            当天数据
            '''
            last_data = df.iloc[-1]
            # current_date = datetime.date
            if last_data['date'] == datetime.date.today().strftime('%Y-%m-%d'):
                # pass
                insert_data = list(last_data.values)
                insert_data = self.convert(insert_data)
                join_str = ','.join(['%s']*21)
                conn = DBSelector().get_mysql_conn('db_stock', 'qq')
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT id FROM db_stock.bond_overview order by id desc limit 1')
                idx = cursor.fetchone()
                idx = idx[0]

                # insert_sql = f'''insert into `bond_overview` (`id`,`date`, `price`,`volume`,`amount`,`count`,`avg_price`,`mid_price`,`avg_premium_rt`,  `avg_ytm_rt`,  `increase_val`,  `increase_rt`,  `turnover_rt`,  `price_90`,  `price_90_100`,  `price_100_110`,  `price_110_120`,  `price_120_130`,  `price_130`,  `idx_price`,  `idx_increase_rt`）value ({join_str})'''
                insert_sql = f'''insert into `bond_overview` values ({join_str})'''
                
                print(insert_sql)
                insert_data.insert(0, idx+1)
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
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "www.jisilu.cn",
            "Referer": "https://www.jisilu.cn/data/cbnew/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/69.0.3497.81 Chrome/69.0.3497.81 Safari/537.36",
        }

    def run(self):
        content = self.get()
        result = self.parse(content)
        self.process(result)


if __name__ == '__main__':
    processor = CBProcess()
    processor.run()
