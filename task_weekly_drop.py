# -*-coding=utf-8-*-

# @Time : 2019/10/19 13:47
# @File : weekly_drop.py

# 每周跌幅最多的
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
        if not current:
            self.today = datetime.datetime.strptime('2019-11-15', '%Y-%m-%d')
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
        code_dict = dict(zip(code_list, name_list))
        yjl_dict = dict(zip(code_list, yjl))
        for code in code_dict:
            # 周线,获取下跌的幅度
            m_percent, w_percent, last_close = get_low_price(code=code, start=month_str)
            price_dict[code] = last_close
            w_result[code] = w_percent
            m_result[code] = m_percent

        m_result_list = list(sorted(m_result.items(), key=lambda x: x[1]))
        w_result_list = list(sorted(w_result.items(), key=lambda x: x[1]))
        return m_result_list[:10] + m_result_list[-10:], w_result_list[:10] + w_result_list[
                                                                              -10:], code_dict, price_dict, yjl_dict

    def mail_content(self, input_raw):
        title = f'{self.today} {self.__type}涨跌榜'
        df = pd.DataFrame(input_raw)
        body = df.to_html(index=False)
        return title, body

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
        month_data, week_data, code_dict, price_dict, yjl_dict = self.get_rank(current)
        if type_ == 'week':
            rank_data = week_data
        else:
            rank_data = month_data

        result = []
        for i in rank_data:
            self.logger.info(f'{i[0]} {code_dict.get(i[0])} : {i[1]}%')
            d = {}
            d['代码'] = i[0]
            d['名称'] = code_dict.get(i[0])
            d['当前价格'] = price_dict.get(i[0])
            d['溢价率'] = yjl_dict.get(i[0])
            d['跌幅'] = i[1]
            d['更新日期'] = self.today
            result.append(d)

        # self.save_mongodb(result)

        title, body = self.mail_content(result)
        send_from_aliyun(title=title, content=body, types='html')


def main():
    WeeklyDrop().weekly_drop_rank(current=True, type_='week')  # 正常运行时current = True


if __name__ == '__main__':
    main()
