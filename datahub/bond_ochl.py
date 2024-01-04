# -*- coding: utf-8 -*-
# @Time : 2022/12/29 16:29
# @File : A_stock_daily_info.py
# @Author : Rocky C@www.30daydo.com

# A 股日线行情导入数据库
# 获取开高低收量
import sys
sys.path.append('..')
from configure.settings import get_tushare_pro,DBSelector
from configure.util import calendar
import time

start_date = '2023-12-31'
end_date = '2024-01-03'

class BondDailyInfo():
    '''
    可转债每天的高开低收
    '''
    def __init__(self):
        self.pro = get_tushare_pro()
        self.conn = DBSelector().get_engine('db_bond_ochl','qq')


    def run(self):
        date = calendar(start_date,end_date)
        from configure.util import fmt_date
        for d in date:
            print('写入数据{} '.format(d))
            d=fmt_date(d,'%Y-%m-%d','%Y%m%d')
            df = self.pro.cb_daily(trade_date=d)
            df=df.reset_index()
            try:
                df.to_sql('tb_{}'.format(d),con=self.conn,if_exists='fail')
            except Exception as e:
                print(e)

            time.sleep(1)

def main():
    app=BondDailyInfo()
    app.run()


if __name__ == '__main__':
    main()
