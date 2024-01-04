# 根据形态选择转债

import pandas as pd
from dataconfig import csv_path
import sys

sys.path.append('..')
from configure.settings import get_tushare_pro, DBSelector
from configure.util import calendar
import time
from configure.util import fmt_date

start_date, end_date = '2023-12-01', '2024-01-03'
REMAIN_YEAR = 1
SCALE = 7
DROP_DOWN_PCT = -5 * 0.01  # 下跌5%
MAX_PRICE = 130
LAST_DROP_DAY = 5

def Percent(a, b):
    return (a - b) / b


class DataFeed:

    def __init__(self, data):
        data = self.read_csv(csv_path)
        jsl_df = self.get_currrent_bond()
        self.code_name_mapper = self.mapper(jsl_df)
        in_list = self.factor_filter(jsl_df)
        self.data = self.process_data(data, in_list)
        # print(data.head())
        # data = self.filter(data)

    def run(self):
        self.filter(self.data)

    def filter(self, data):
        self.down_direction(data)

    def down_direction(self, data):
        # 下降趋势
        end_data_convert = fmt_date(end_date, '%Y-%m-%d', '%Y%m%d')

        for ts_code, row in data.groupby('ts_code'):
            bond_name = self.code_name_mapper[ts_code]
            target_item = row.sort_values(by='trade_date')
            start_price, end_price = target_item['close'].iloc[0], target_item['close'].iloc[-1]
            last_date = target_item['trade_date'].iloc[-1]

            if end_price > MAX_PRICE:
                continue

            if end_data_convert < str(last_date):
                continue

            percent = Percent(end_price, start_price)
            if start_price < end_price or percent > DROP_DOWN_PCT:
                continue

            total_days = len(target_item)
            # bond_dropdown_day = len(target_item[target_item['pct_chg'] < 0])
            # bond_dropdown_pct = bond_dropdown_day / total_days
            # if bond_dropdown_pct < 0.6:
            #     continue
            last_five_item = target_item.iloc[-20:-1]
            last_drop_day = len(last_five_item[last_five_item['pct_chg'] <= 0])
            if last_drop_day < LAST_DROP_DAY:
                continue


            avg = target_item['close'].mean()
            first_part_day_avg = target_item['close'][:total_days // 3].mean()
            if avg > first_part_day_avg:
                continue

            print(
                '代码:{}\t名称:{}\t最新价格:{}\t跌幅:{}\t最近跌的天数:{}'.format(ts_code, bond_name, end_price, round(percent * 100, 2),last_drop_day))

            # print(bond_dropdown_pct)

    def mapper(self, jsl_df):
        return dict(zip(jsl_df['可转债代码'].tolist(), jsl_df['可转债名称'].tolist()))

    def get_currrent_bond(self):
        conn = DBSelector().get_engine('db_stock', 'qq')
        df = pd.read_sql('tb_bond_jisilu', con=conn)
        df['可转债代码'] = df['可转债代码'].astype(str)
        df['可转债代码'] = df['可转债代码'].map(self.convert_postfix)
        return df

    def factor_filter(self, df):
        df = df[df['剩余规模'] < SCALE]
        df = df[df['剩余时间'] >= REMAIN_YEAR]
        return df['可转债代码'].tolist()

    def convert_postfix(self, x):
        if x.startswith('12'):
            return x + '.SZ'
        else:
            return x + '.SH'

    def read_csv(self, path):
        df = pd.read_csv(path)
        return df

    def process_data(self, data, in_list):
        # 处理数据
        no_vol_bond = list(set(list(data[data['vol'] == 0]['ts_code'].tolist())))
        data = data[~data['ts_code'].isin(no_vol_bond)]
        data = data[data['ts_code'].isin(in_list)]
        return data

    def gen_csv(self):
        # 从mysql读取数据 生成csv
        dates = calendar(start_date, end_date)
        conn = DBSelector().get_engine('db_bond_ochl', 'qq')
        df_total_list = []
        for date in dates:
            date = fmt_date(date, '%Y-%m-%d', '%Y%m%d')
            print(date)
            try:
                df = pd.read_sql('tb_{}'.format(date), con=conn)
            except Exception as e:
                print(e)
            else:
                df_total_list.append(df)

        df_total = pd.concat(df_total_list)
        df_total.to_csv('data.csv', index=False, encoding='utf-8')


if __name__ == '__main__':
    data = DataFeed(csv_path)
    data.run()
    # data.get_currrent_bond()
