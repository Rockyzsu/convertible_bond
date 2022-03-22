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
        print(js)
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


def main(code=None):
    app = TopTheHolding()

    if code is None:
        app.run()
    else:
        app.crawl(code)


if __name__ == '__main__':
    fire.Fire(main)
