# 监控可转债大单
import datetime
import json
import logging
import os
import random
import time
from send_mail import sender_139
import pymongo
import tushare as ts
import pandas as pd
from setting import get_engine
import config

class BigDeal(object):

    def __init__(self):

        # self.df = self.get_tick()
        self.logger = self.llogger('log/'+'big_deal')
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        if ts.is_holiday(today):
            self.logger.info('{}假期 >>>>>'.format(today))
            return

        self.db_stock_engine = get_engine('db_stock', True)
        self.jisilu_df = self.get_code()
        self.code_name_dict=dict(zip(list(self.jisilu_df['可转债代码'].values),list(self.jisilu_df['可转债名称'].values)))
        self.db = pymongo.MongoClient(config.mongodb_host, config.mongodb_port)

    def llogger(self, filename):
        logger = logging.getLogger(filename)  # 不加名称设置root logger
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(asctime)s][%(filename)s][line: %(lineno)d]\[%(levelname)s] ## %(message)s)',
            datefmt='%Y-%m-%d %H:%M:%S')
        # 使用FileHandler输出到文件
        prefix = os.path.splitext(filename)[0]
        fh = logging.FileHandler(prefix + '.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        # 使用StreamHandler输出到屏幕
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        # 添加两个Handler
        logger.addHandler(ch)
        logger.addHandler(fh)
        # logger.info('this is info message')
        # logger.warning('this is warn message')
        return logger

    def get_ticks(self, code, date):
        df = ts.get_tick_data(code, date=date, src='tt')
        # today = datetime.date.today().strftime('%Y-%m-%d')
        df['time'] = df['time'].map(lambda x: date + ' ' + x)
        return df

    # 从mongo获取数据 默认分钟 1000张
    def get_volume_distribition(self,code,date,types='min',big_deal=1000):
        # code='110030'
        # date='2019-04-02'

        # big_deal = 1000 # 1000张 100w

        date_d = datetime.datetime.strptime(date,'%Y-%m-%d')
        next_day = date_d+datetime.timedelta(days=1)

        doc = self.db['cb_deal'][code]
        d=[]
        for item in doc.find({'time':{'$gte':date_d,'$lt':next_day}},{'_id':0}):
            d.append(item)

        if len(d)==0:
            return (code,-1)

        df = pd.DataFrame(d)

        df=df.set_index('time',drop=True)
        min_df = df.resample(types).sum()[['price','volume']]
        count = min_df[min_df['volume']>big_deal]['volume'].count()
        return (code,count)

    def get_tick(self, code, date):
        fs_df = None

        for i in range(10):

            try:
                fs_df = ts.get_tick_data(code, date=date, src='tt')

            except Exception as e:
                self.logger.error('获取tick失败>>>>code={},date'.format(code, date))
                self.logger.error(e)
                time.sleep(random.randint(2, 5))

            else:
                if fs_df is not None and len(fs_df) > 0:
                    break
                else:
                    self.logger.error('>>>>code={},date={} 获取行情重试 {}次'.format(code, date, i))

        return fs_df

    def loop_code(self, date):

        code_list = self.jisilu_df['可转债代码'].values

        for code in code_list:
            fs_df = self.get_tick(code, date)

            if fs_df is None:
                continue

            fs_df['time'] = fs_df['time'].map(lambda x: date + ' ' + x)
            fs_df['time'] = pd.to_datetime(fs_df['time'], format='%Y-%m-%d %H:%M:%S')

            ret = self.store(code, fs_df)

            if ret.get('status') == -1:
                self.logger.error('保存失败 >>>> code={}, date={}'.format(code, date))
            else:
                self.logger.info('保存成功 >>>> code={}, date={}'.format(code, date))

    def store(self, code, df):
        df['code'] = code
        js = json.loads(df.T.to_json()).values()

        for row in js:
            row['time'] = datetime.datetime.utcfromtimestamp(row['time'] / 1000)
        try:
            self.db['cb_deal'][code].insert_many(js)
        except Exception as e:
            self.logger.error(e)
            self.logger.error('插入数据失败')
            return {'status': -1, 'code': code}
        else:
            return {'status': 0, 'code': code}

    def get_code(self):
        df = pd.read_sql('tb_bond_jisilu', con=self.db_stock_engine)
        return df

    def loop_date(self,today=True):

        # 获取当天数据，18点之后
        if today:
            d = datetime.date.today().strftime('%Y-%m-%d')
            if ts.is_holiday(d):
                self.logger.info('holiday,skip>>>>{}'.format(d))
            else:
                self.logger.info('going>>>>{}'.format(d))
                self.loop_code(d)
        # 获取一周的数据看看

        else:
            delta = 7
            for i in range(1, delta + 1):
                d = (datetime.date.today() + datetime.timedelta(days=i * -1)).strftime('%Y-%m-%d')
                if ts.is_holiday(d):
                    print('holiday,skip>>>>{}'.format(d))
                else:
                    print('going>>>>{}'.format(d))
                    self.loop_code(d)

    def analysis(self,date=None,head=300):
        if date is None:
            date=datetime.date.today().strftime('%Y-%m-%d')
        # date='2019-05-08'
        kzz_big_deal_count =[]

        for code in self.jisilu_df['可转债代码'].values:
            kzz_big_deal_count.append(self.get_volume_distribition(code,date))

        kzz_big_deal_order = list(sorted(kzz_big_deal_count,key=lambda x:x[1],reverse=True))
        # print(kzz_big_deal_order)
        send_content=[]

        for item in kzz_big_deal_order[:head]:
            self.logger.info('{} ::: 大单出现次数 {}'.format(self.code_name_dict.get(item[0]),item[1]))
            send_content.append('{} ::: 大单出现次数 {}'.format(self.code_name_dict.get(item[0]),item[1]))
        # 入库的
        big_deal_doc = self.db['db_stock']['big_deal_logger']
        for item in kzz_big_deal_order:
            d={'Date':date,'name':self.code_name_dict.get(item[0]), 'times':int(item[1])}
            try:
                big_deal_doc.insert(d)
            except Exception as e:
                self.logger.error(e)
                self.logger.error(d)
            # send_content.append('{} ::: 大单出现次数 {}'.format(self.code_name_dict.get(item[0]),item[1]))

        content ='\n'.join(send_content)
        title='{}-大单监控'.format(date)

        try:

            sender_139(title,content)

        except Exception as e:
            self.logger.error(e)
        else:
            self.logger.info('发送成功')


def main():
    obj = BigDeal()
    obj.analysis(head=30)

if __name__ == '__main__':

    main()
