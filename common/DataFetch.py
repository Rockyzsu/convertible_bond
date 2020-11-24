# -*- coding: utf-8 -*-
# @Time : 2020/11/23 23:43
# @File : DataFetch.py
# @Author : Rocky C@www.30daydo.com

import pandas as pd
import sys
import datetime
sys.path.append('..')
from configure.settings import DBSelector
class DataFetcher():

    def __init__(self):
        # today='2020-03-27'
        self.DB = DBSelector()

    @property
    def jsl_bond(self):
        engine = self.DB.get_engine('db_stock', 'qq')
        jsl_df = pd.read_sql('tb_bond_jisilu', con=engine)
        return jsl_df

    @property
    def basic_info(self):
        engine = self.DB.get_engine('db_stock', 'qq')
        basic_df = pd.read_sql('tb_basic_info', con=engine, index_col='index')
        return basic_df

    @property
    def daily(self):
        engine_daily = self.DB.get_engine('db_daily', 'qq')
        daily_df = pd.read_sql(datetime.date.today().strftime('%Y-%m-%d'), con=engine_daily)
        return daily_df

