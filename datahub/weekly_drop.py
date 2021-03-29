# -*-coding=utf-8-*-

# @Time : 2019/10/19 13:47
# @File : weekly_drop.py

# 每周跌幅最多的, 默认是周，可以改为月
import sys

sys.path.append('..')
import datetime
import pandas as pd
from filterbond import get_low_price
from common.BaseService import BaseService
from common.DataFetch import DataFetcher
from configure.settings import DBSelector, send_from_aliyun


class WeeklyDrop(BaseService):

    # 计算一周，一个月，一个季度跌幅最多的债
    def __init__(self):
        super(WeeklyDrop, self).__init__('log/weeklydrop.log')
        self.datafetch = DataFetcher()
        self.mongo = DBSelector().mongo('qq')

    def get_rank(self, current):
        '''
        :param current: True or False
        :return:
        '''
        if not current:
            date = '2019-11-15'
            self.today = datetime.datetime.strptime(date, '%Y-%m-%d')
        else:
            self.today = datetime.datetime.strptime(self.today, '%Y-%m-%d')

        jsl_df = self.datafetch.jsl_bond
        code_list = jsl_df['可转债代码'].values
        name_list = jsl_df['可转债名称'].values

        yjl = jsl_df['溢价率'].values

        week = self.today + datetime.timedelta(days=-7)
        month = self.today + datetime.timedelta(days=-31)
        week_str = week.strftime('%Y-%m-%d')
        month_str = month.strftime('%Y-%m-%d')
        m_result = {}
        w_result = {}
        price_dict = {}
        volatility_dict = {}
        code_dict = dict(zip(code_list, name_list))
        yjl_dict = dict(zip(code_list, yjl))
        for code in code_dict:
            # 周线,获取下跌的幅度
            m_percent, w_percent, last_close, volatility = get_low_price(code=code, start=month_str)
            price_dict[code] = last_close
            w_result[code] = w_percent
            m_result[code] = m_percent
            volatility_dict[code] = volatility

        m_result_list = list(sorted(m_result.items(), key=lambda x: x[1]))
        w_result_list = list(sorted(w_result.items(), key=lambda x: x[1]))
        volatility_list = list(sorted(volatility_dict.items(), key=lambda x: x[1],reverse=True))

        return (m_result_list[:10] + m_result_list[-10:],
                w_result_list[:10] + w_result_list[-10:],
                volatility_list[:10],
                code_dict,
                price_dict,
                yjl_dict)



    def save_mongodb(self, data):
        self.mongo['db_price_drop'][f'{self.today}_{self.__type}_drop'].insert_many(data)

    def weekly_drop_rank(self, current=True, type_='week'):
        '''
        :type_  week或者month
        :param current:
        :param type_:
        :return:
        '''
        self.__type = type_
        month_data, week_data, volatility, code_dict, price_dict, yjl_dict = self.get_rank(current)
        if type_ == 'week':
            rank_data = week_data
        else:
            rank_data = month_data

        result = []
        for code,value in rank_data:
            self.logger.info(f'{code} {code_dict.get(code)} : {value}%')
            d = {}
            d['代码'] = code
            d['名称'] = code_dict.get(code)
            d['当前价格'] = price_dict.get(code)
            d['溢价率'] = yjl_dict.get(code)
            d['跌幅'] = value
            d['更新日期'] = self.today
            result.append(d)
        
        result_volatility=[]
        
        for code,value in volatility:
            d={}
            d['代码']=code
            d['名称']=code_dict.get(code)
            d['当前价格'] = price_dict.get(code)
            d['波动']=value
            d['更新日期'] = self.today

            result_volatility.append(d)
        title = f'{self.today.strftime("%Y-%m-%d")} {self.__type}涨跌榜'
        df_rank = pd.DataFrame(result)
        df_rank['当前价格'] = df_rank['当前价格'].map(lambda x: round(x, 1))
        body_part_one = df_rank.to_html(index=False)

        df_volatility = pd.DataFrame(result_volatility)
        body_part_two =df_volatility.to_html(index=False)

        content = body_part_one+'<br><br>'+body_part_two


        send_from_aliyun(title=title, content=content, types='html')
