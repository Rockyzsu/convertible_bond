# 监控可转债大单
import datetime

import tushare as ts
import pandas as pd


class BigDeal(object):

    def __init__(self):
        # self.df = self.get_tick()
        pass

    def get_tick(self,code,date):
        df=ts.get_tick_data(code,date=date,src='tt')
        # today = datetime.date.today().strftime('%Y-%m-%d')
        df['time']=df['time'].map(lambda x:date+' '+x)
        return df

    def analysis(self):
        df = self.get_tick()
        df['time']=pd.to_datetime(df['time'],format='%Y-%m-%d %H:%M:%S')
        df = df.set_index('time',drop=True)

    def loop_date(self):
        