# -*- coding: utf-8 -*-
# @Time : 2021/4/2 18:08
# @File : TushareUtil.py
# @Author : Rocky C@www.30daydo.com
import tushare as ts
import sys
sys.path.append('..')
from configure.settings import config
import datetime

class TushareBaseUtil:
    '''
    tushare 常用调用
    '''
    def __init__(self):
        ts_token = config.get('ts_token')
        ts.set_token(ts_token)
        self.pro = ts.pro_api()


    def get_trade_date(self,start_date=None, end_date=datetime.datetime.now().strftime('%Y%m%d')):
        '''
        返回交易日历
        :param start_date:
        :param end_date:
        :return:
        '''
        df = self.pro.trade_cal(exchange='', is_open='1',start_date=start_date, end_date=end_date)
        return df['cal_date'].tolist()


def main():
    app = TushareBaseUtil()
    df =app.get_trade_date(start_date='20190101')
    print(df)

if __name__ == '__main__':
    main()
