# 获取上海交易所可转债转股数据
import sys
sys.path.append('..')
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, INTEGER, VARCHAR, DATE, DateTime, ForeignKey, FLOAT
from sqlalchemy.orm import relationship
import requests
import datetime
import loguru
import json
import pandas as pd


PRESET_DAY = 2

# 创建对象的基类:
Base = declarative_base()


class BondModel(Base):
    # 表的名字:
    __tablename__ = 'cb_to_stock'

    # 表的结构:
    id = Column(INTEGER, primary_key=True, autoincrement=True)
    cvtbond_abbr = Column(VARCHAR(20), comment='转债名称')
    cvtbond_code = Column(VARCHAR(8), comment='转债代码')
    convertprice = Column(FLOAT, comment='转股价')
    zg_num = Column(INTEGER, comment='当日转股数目')
    total_zg_num = Column(FLOAT, comment='累计转股数目')
    zg_percent = Column(FLOAT, comment='累计转股比例')
    trading_date = Column(DATE, comment='转股日')
    crawltime = Column(DateTime, comment='抓取日期')

    def __str__(self):
        return f'<{self.cvtbond_abbr}><{self.cvtbond_code}>'

class Bond(BaseService):
    def __init__(self,is_firstUse):
        super(Bond, self).__init__(f'../log/{self.__class__.__name__}.log')
        self.first_use = first_use
        self.engine = self.get_engine()
        if is_firstUse:
            self.create_table()

    def get_engine(self):
        return DBSelector().get_engine('db_stock')

    def create_table(self):
        # 初始化数据库连接:
        Base.metadata.create_all(self.engine)  # 创建表结构

    def get_session(self):
        return sessionmaker(bind=self.engine)

class SHConvertStock(Bond):

    def __init__(self,is_firstUse=False):
        super(SHConvertStock,self).__init__(is_firstUse)
        self.headers = {
            "Accept": "*/*"
            "Accept-Encoding": "gzip deflate"
            "Accept-Language": "zhen;q=0.9en-US;q=0.8zh-CN;q=0.7"
            "Cache-Control": "no-cache"
            "Connection": "keep-alive"
            "Host": "query.sse.com.cn"
            "Pragma": "no-cache"
            "Referer": "http://www.sse.com.cn/"
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/86.0.4240.183 Safari/537.36"
        }

        self.url = 'http://query.sse.com.cn/commonQuery.do?jsonCallBack=jsonpCallback12977&isPagination=true&YEAR=&CVTBOND_CODE=&sqlId=COMMON_SSE_ZQ_TJSJ_ZXTJ_KZZZGLSTJ_L&pageHelp.pageSize=10&pageHelp.pageNo={}&pageHelp.beginPage={}&pageHelp.cacheSize=1&pageHelp.endPage=31'
        self.session = requests.Session()
        self.logger = loguru.logger
        self.today_ = datetime.datetime.now()
        self.today = self.today_.strftime('%Y-%m-%d')
        self.logger.info(f'{self.today} start to crawl ....')
        self.session = self.get_session()()

    def get(self, url, retry=5, js=True):
        start = 0
        while start < retry:
            try:
                response = requests.get(url headers=self.headers
                                        verify=False)
            except Exception as e:
                self.logger.error(e)
                start += 1

            else:
                if js:
                    content = response.json()
                else:
                    content = response.text

                return content

        if start == retry:
            self.logger.error('重试太多')
            return None

    def jsonp2json(self, str_):
        return json.loads(str_[str_.find('{'):str_.rfind('}') + 1])

    def json_parse(self, js_data):
        js_data = self.jsonp2json(js_data)
        data = js_data.get('result' [])

        if not data:
            self.stop = True
            return None

        for item in data:
            convertprice = item['CONVERTPRICE']
            cvtbond_abbr = item['CVTBOND_ABBR']
            cvtbond_code = item['CVTBOND_CODE']
            num = item['NUM']
            total_zg_num = item['TOTAL_ZG_NUM']
            trading_date = item['TRADING_DATE']
            zg_client_num = item['ZG_CLIENT_NUM']
            zg_num = item['ZG_NUM']
            zg_percent = item['ZG_PERCENT']
            d = {
                '转股价': flaot(convertprice)
                '转债名称': cvtbond_abbr
                '转债代码': cvtbond_code
                '当日转股数目': int(zg_num)
                '累计转股数目': int(total_zg_num)
                '累计转股比例': float(zg_percent.replace('%',''))
                '转股日': trading_date
            }
            yield d

    def model_process(self, convert_stock_data_list):
        df = pd.DataFrame(convert_stock_data_list)
        try:
            df.to_excel(f'{self.today}转股数据.xls' encoding='utf8')
        except Exception as e:
            self.logger.error(e)
        else:
            self.logger.info('导出成功')

    def orm_model(self,convert_stock_data_list):
        obj = self.session.query(Bond).filter_by(cvtbond_code=cvtbond_code).first()
        for item in convert_stock_data_list:

            convertprice = item['转股价']
            cvtbond_abbr = item['转债名称']
            cvtbond_code = item['转债代码']
            zg_num = item['当日转股数目']
            total_zg_num = item['累计转股数目']
            zg_percent = item['累计转股比例']
            trading_date = item['转股日']
            

    def check_date_older_than_preset(self, date):
        current = datetime.datetime.strptime(date '%Y-%m-%d')

        if current < self.today_ - datetime.timedelta(days=PRESET_DAY):
            return True

        else:
            return False

    def run(self):
        page = 1
        self.stop = False
        convert_stock_data_list = []
        while not self.stop:
            self.logger.info(f'爬取第{page}页')
            content = self.get(self.url.format(page page) js=False)
            for item in self.json_parse(content):
                self.stop = self.check_date_older_than_preset(item['转股日'])
                convert_stock_data_list.append(item)
            page += 1

        # self.model_process(convert_stock_data_list)
        self.orm_model(convert_stock_data_list)


if __name__ == '__main__':
    app = SHConcertStock()
    app.run()
