# -*- coding: utf-8 -*-
# @Time : 2021/4/2 18:08
# @File : TushareUtil.py
# @Author : Rocky C@www.30daydo.com
import tushare as ts
import sys
sys.path.append('..')
from configure.settings import config
import datetime
from common.Base import pro

class TushareBaseUtil:
    '''
    tushare 常用调用
    '''
    def __init__(self):
        # ts_token = config.get('ts_token')
        # ts.set_token(ts_token)
        # self.pro = ts.pro_api()
        self.pro=pro


    def get_trade_date(self,start_date=None, end_date=None):
        '''
        返回交易日历
        :param start_date:
        :param end_date:
        :return:
        '''
        if end_date is None:
            end_date=datetime.datetime.now().strftime('%Y%m%d')
        df = self.pro.trade_cal(exchange='', is_open='1',start_date=start_date, end_date=end_date)
        return df['cal_date'].tolist()

    def get_cb_code(self):
        df = self.pro.cb_basic()
        # print(len(df))
        # print(df.tail(10))
        for index,row in df[['ts_code','list_date','bond_short_name']].iterrows():
            print(row['ts_code'],row['bond_short_name'],row['list_date'])

    def tick(self):
        import tushare as ts
        # df = ts.get_tick_data('123094','20210401',src='tt') work
        df = ts.get_tick_data('113520','2019-05-17',src='sn')
        # print(df.head())
        print(df)

    def bar_tick(self):
        import tushare as ts
        cons = ts.get_apis()
        df = ts.bar('113520', conn=cons, freq='D', start_date='2019-05-01', end_date='2019-05-20')
        print(df.head())

    def common_tick(self):
        import tushare as ts
        cons = ts.get_apis()
        df = ts.tick('113520', conn=cons, date='2020-03-02')
        print(df.head())

def main():
    app = TushareBaseUtil()
    # df =app.get_trade_date(start_date='20190101')
    # print(df)
    # app.get_cb_code()
    # app.tick()

    # app.bar_tick()
    app.common_tick()

if __name__ == '__main__':
    main()
