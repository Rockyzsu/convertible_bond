# -*- coding: utf-8 -*-
# @Time : 2021/8/28 11:09
# @File : TenHoldingPerson.py
# @Author : Rocky C@www.30daydo.com

# 可转债十大持有人数据获取
import datetime
import random
import sys
import time

import fire
import pandas as pd

sys.path.append('..')

from configure.settings import DBSelector
from common.BaseService import BaseService
from common.DataFetch import DataFetcher


class TopTheHolding(BaseService):

    def __init__(self):
        super(TopTheHolding, self).__init__(f'../log/TopTenHoldingPersion.log')
        self.db = DBSelector()
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')

    def get_jsl_data(self):
        data = self.data_fetcher.jsl_bond
        self.jsl_data = data['可转债代码'].tolist()

    @property
    def headers(self):
        return {
            'origin': 'https://emh5.eastmoney.com',
            'pragma': 'no-cache',
            'referer': 'https://emh5.eastmoney.com/change/index.html?fc=12312102&color=w',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}

    def init_db(self):
        self.mongodb = self.get_mongo_db()
        self.data_fetcher = DataFetcher()
        self.get_jsl_data()

    def crawl(self, code):
        post_fix = {'12': '02', '11': '01'}.get(code[:2])
        url = 'https://emh5.eastmoney.com/api/KeZhuanZhai/JiBenXinXi/GetShiDaChiYouRenList'
        data = {"fc": f"{code}{post_fix}", "color": "w", "pageSize": 1}
        js = self.post(url=url, post_data=data, _json=True)
        # print(js)
        return js

    def get_mongo_db(self):
        return self.db.mongo('qq')['db_stock']
    
    def parse_json(self, js, code):
        result_list = []

        if js is None or js.get('Result') is None:
            return result_list

        for person in js.get('Result', {}).get('ShiDaChiYouRenList', []):
            person_dict = {}

            update_date = person['JieZhiRiQi']
            name = person['ChiYouRenMingCheng']
            amount = person['ChiYouShuLiang']
            holding_ratio = person['ChiYouBiLi']
            holding_ratio = float(holding_ratio.replace('%', ''))

            person_dict['code'] = code
            person_dict['name'] = name
            person_dict['amount'] = amount
            person_dict['update_date'] = update_date
            person_dict['holding_ratio'] = holding_ratio
            person_dict['crawltime'] = datetime.datetime.now()

            if name == '合计':
                continue
            result_list.append(person_dict)

        return result_list

    def dump_mongodb(self, result_list):
        if len(result_list)==0:
            print('empty')
            return
            
        try:
            self.mongodb['bond_top_10_holding_{}'.format(self.today)].insert_many(result_list)
        except Exception as e:
            print(e)
            self.mongodb = self.get_mongo_db()
            self.mongodb['bond_top_10_holding_{}'.format(self.today)].insert_many(result_list)

    def run(self):
        self.init_db()
        for code in self.jsl_data:
            print(f'crawling {code}')
            js = self.crawl(code)
            result_list = self.parse_json(js, code)
            self.dump_mongodb(result_list)
            time.sleep(random.randint(1, 3))
class TopTheHoldingV2(BaseService):

    def __init__(self):
        super(TopTheHoldingV2, self).__init__(f'../log/TopTenHoldingPersion.log')
        self.db = DBSelector()
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')

    def get_jsl_data(self):
        data = self.data_fetcher.jsl_bond
        self.jsl_data = data['可转债代码'].tolist()

    @property
    def headers(self):
        return {
            'origin': 'https://emh5.eastmoney.com',
            'pragma': 'no-cache',
            'referer': 'https://emh5.eastmoney.com',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}

    def init_db(self):
        self.mongodb = self.get_mongo_db()
        self.data_fetcher = DataFetcher()
        self.get_jsl_data()

    def crawl(self, code):
        if code.startswith('12'):
            code=code+'.SZ'
        else:
            code=code+'.SH'

        url = 'https://datacenter.eastmoney.com/securities/api/data/get?client=APP&source=SECURITIES&type=RPT_BOND10_BS_HOLDER&sty=SECUCODE,SECURITY_CODE,BOND_NAME_ABBR,HOLDER_NAME,END_DATE,HOLD_NUM,HOLD_RATIO,HOLDER_RANK&filter=(SECUCODE%3D%22{}%22)&pageNumber=1&pageSize=50'.format(code)
        print(url)
        js = self.get(url=url, _json=True)
        # print(js)
        return js

    def get_mongo_db(self):
        return self.db.mongo('qq')['db_stock']

    def parse_json(self, js, code):
        result_list = []

        if js is None or js.get('result') is None:
            return result_list

        result_list = js.get('result', {}).get('data', [])


        return result_list

    def dump_mongodb(self, result_list):
        if len(result_list)==0:
            print('empty')
            return

        try:
            self.mongodb['bond_top_10_holding_{}'.format(self.today)].insert_many(result_list)
        except Exception as e:
            print(e)
            self.mongodb = self.get_mongo_db()
            self.mongodb['bond_top_10_holding_{}'.format(self.today)].insert_many(result_list)

    def run(self):
        self.init_db()
        for code in self.jsl_data:
            print(f'crawling {code}')
            js = self.crawl(code)
            result_list = self.parse_json(js, code)
            self.dump_mongodb(result_list)
            # time.sleep(random.randint(1, 3))


    def dump_excel(self):
        self.mongodb = self.get_mongo_db()
        doc = self.mongodb['bond_top_10_holding_{}'.format(self.today)]
        result = []
        for item in doc.find({}):
            del item['_id']
            result.append({'转债名称':item['BOND_NAME_ABBR'],
                           '转债代码':item['SECUCODE'],
                           '公布日期':item['END_DATE'],
                           '持有人':item['HOLDER_NAME'],
                           '持有张数':item['HOLD_NUM'],
                           '持有比例':item['HOLD_RATIO'],
                           '排名':item['HOLDER_RANK'],
                           })

        df=pd.DataFrame(result)
        df=df[(df['持有人']=='合计')]
        print(df.head())
        import xlsxwriter
        df.to_excel('十大持有人2022-12-04.xlsx',encoding='utf8',engine='xlsxwriter')




def main(code=None):

    # v1
    # app = TopTheHolding()
    #
    # if code is None:
    #     app.run()
    # else:
    #     app.crawl(code)

    # v2
    app = TopTheHoldingV2()
    app.run()
    # app.dump_excel()

if __name__ == '__main__':
    fire.Fire(main)
