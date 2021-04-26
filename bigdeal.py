# 监控可转债大单
import datetime
import json
import random
import time
import tushare as ts
import pandas as pd
from common.BaseService import BaseService
from configure.settings import DBSelector, send_from_aliyun
from common.TushareUtil import TushareBaseUtil

# 大单定义 手数, 需要在大单数据获取完成后
BIG_DEAL = 1000

# 获取的历史天数的数据
DELTA_DAY = 365*4


class BigDeal(BaseService):

    def __init__(self):
        super(BigDeal, self).__init__('log/BigDeal.log')

        self.DB = DBSelector()
        self.db_stock_engine = self.DB.get_engine('db_stock', 'qq')
        self.jisilu_df = self.get_bond()
        self.code_name_dict = dict(zip(list(self.jisilu_df['可转债代码'].values), list(self.jisilu_df['可转债名称'].values)))
        self.mongodb = self.DB.mongo(type='qq')

    def get_trade_date(self):
        start_date=datetime.datetime.now() +datetime.timedelta(days=-1*DELTA_DAY)
        return TushareBaseUtil().get_trade_date(start_date=start_date.strftime('%Y%m%d'))

    def get_ticks(self, code, date):
        df = ts.get_tick_data(code, date=date, src='tt')
        df['time'] = df['time'].map(lambda x: date + ' ' + x)
        return df

    def get_volume_distribition(self, code, date, types='min', big_deal=BIG_DEAL):
        '''
        # 从mongo获取数据 默认分钟 1000张
        :param code:
        :param date:
        :param types:
        :param big_deal:
        :return:
        '''
        # code='110030'
        # date='2019-04-02'

        # big_deal = 1000 # 1000张 100w

        date_d = datetime.datetime.strptime(date, '%Y-%m-%d')
        next_day = date_d + datetime.timedelta(days=1)

        doc = self.mongodb['cb_deal'][code]
        d = []
        for item in doc.find({'time': {'$gte': date_d, '$lt': next_day}}, {'_id': 0}):
            d.append(item)

        if len(d) == 0:
            return (code, -1)

        df = pd.DataFrame(d)
        df = df.set_index('time', drop=True)
        min_df = df.resample(types).sum()[['price', 'volume']]
        count = min_df[min_df['volume'] > big_deal]['volume'].count()
        return (code, count)

    def get_tick(self, code, date, retry=5):
        fs_df = None

        for i in range(retry):

            try:
                fs_df = ts.get_tick_data(code, date=date, src='tt')

            except Exception as e:
                self.logger.error('获取tick失败>>>>code={},date'.format(code, date))
                self.logger.error(e)
                time.sleep(random.randint(5, 25))

            else:
                if fs_df is not None and len(fs_df) > 0:
                    break
                else:
                    self.logger.error('>>>>code={},date={} 获取行情重试 {}次'.format(code, date, i))

        return fs_df

    def total_bonds(self, date):

        code_list = self.jisilu_df['可转债代码'].values
        for code in code_list:
            self.individual_bond(code,date)

    def individual_bond(self,code,date):
        # 储存一个可转债
        fs_df = self.get_tick(code, date)

        if fs_df is None:
            return None

        fs_df['time'] = fs_df['time'].map(lambda x: date + ' ' + x)
        fs_df['time'] = pd.to_datetime(fs_df['time'], format='%Y-%m-%d %H:%M:%S')

        ret = self.save_mongo(code, fs_df)

        if ret.get('status') == -1:
            self.notify('bigdeal', 'bigdeal保存mongo出错')
            self.logger.error('保存失败 >>>> code={}, date={}'.format(code, date))
        else:
            self.logger.info('保存成功 >>>> code={}, date={}'.format(code, date))

    def save_mongo(self, code, df):
        df['code'] = code
        js = json.loads(df.T.to_json()).values()

        for row in js:
            row['time'] = datetime.datetime.utcfromtimestamp(row['time'] / 1000)

        try:
            self.mongodb['cb_deal_backup'][code].insert_many(js)

        except TypeError:
            pass
            return {'status': 0, 'code': code}

        except Exception as e:
            self.logger.error(e)
            self.logger.error('插入数据失败')
            return {'status': -1, 'code': code}

        else:
            return {'status': 0, 'code': code}

    def get_bond(self):
        df = pd.read_sql('tb_bond_jisilu', con=self.db_stock_engine)
        return df

    def fetch_bigdeal(self, today=True):
        '''
        # 获取大单数据
        # 获取当天数据，18点之后
        :param today:
        :return:
        '''
        if today:
            self.total_bonds(self.today)

        # 获取历史数据的数据看看
        else:
            valid_date = self.get_trade_date()
            for i in valid_date[::-1]:
                print('going>>>>{}'.format(i))
                self.total_bonds(i)

    # 发送大单数据到手机
    def analysis(self, date=None, head=300):

        date = datetime.date.today().strftime('%Y-%m-%d') if date is None else None

        kzz_big_deal_count = []
        for code in self.jisilu_df['可转债代码'].values:
            kzz_big_deal_count.append(self.get_volume_distribition(code, date))

        kzz_big_deal_order = list(sorted(kzz_big_deal_count, key=lambda x: x[1], reverse=True))
        send_content = []
        for item in kzz_big_deal_order[:head]:
            self.logger.info('{} |大单{}'.format(self.code_name_dict.get(item[0]), item[1]))
            send_content.append('{}|大单 {}'.format(self.code_name_dict.get(item[0]), item[1]))

        # 入库的
        big_deal_doc = self.mongodb['db_stock']['big_deal_logger']
        batch_size = []
        for item in kzz_big_deal_order:
            d = {'Date': date, 'name': self.code_name_dict.get(item[0]), 'times': int(item[1])}
            batch_size.append(d)

        try:
            big_deal_doc.insert_many(batch_size)  # 写入mongo
        except Exception as e:
            self.logger.error(e)

        content = '\n'.join(send_content)
        title = '{}-大单监控'.format(date)

        try:
            send_from_aliyun(title, content)
        except Exception as e:
            self.notify('bigdeal msg', 'bigdeal send failed')
            self.logger.error(e)
        else:
            self.logger.info('发送成功')
