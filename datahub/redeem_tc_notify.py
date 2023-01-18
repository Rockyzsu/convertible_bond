# 强赎通知
import datetime
import re

import pandas as pd
from parsel import Selector
import sys

sys.path.append('..')
from common.BaseService import BaseService

LESS_DAY = 4  # 提前跑路时间 例如，4  ， 30天满足15天转股价值大于130，那么 满足 15-4 =12 天的时候就会告警

STATUS = {'暂不强赎', '公告要强赎', '已满足强赎条件', '已公告强赎'}


class Redemption(BaseService):

    def __init__(self):
        BaseService.__init__(self, '../log/redemption_log.txt')
        self.source = 'realtime'  # 'jsl'
        self._funcs_ = {
            'db': self.get_bond_codes,
            'realtime': self.get_bond_codes_rt
        }


    def get_bond_codes(self):
        from common.DataFetch import DataFetcher

        bonds = DataFetcher().jsl_bond
        name_dict = dict(zip(bonds['可转债代码'].tolist(), bonds['可转债名称'].tolist()))
        return name_dict

    def get_bond_codes_rt(self):
        # 实时获取
        from jsl_login import realtime_data
        df = realtime_data()
        return dict(zip(df['bond_id'].tolist(), df['bond_nm'].tolist()))

    @property
    def headers(self):
        return {'User-Agent': 'Apple Safari'}

    def analysis(self, info):
        # print(info)
        if info not in STATUS:
            try:
                meet, require = info.split('|')
                require = int(require.strip())
                first, second = meet.split('/')
                first = int(first.strip())
                second = int(second.strip())
            except Exception as e:
                print(e)
                print(info)
                return True, None, None, None, info
            else:
                return False, first, second, require, None
        else:
            return True, None, None, None, info

    def dump_local(self, result_list):
        df = pd.DataFrame(result_list)
        try:
            df.to_excel('../data/{}-redeem-info.xlsx'.format(self.today), encoding='utf8')
        except Exception as e:
            print(e)

    def redemption_count(self, code):
        url = 'https://www.jisilu.cn/data/convert_bond_detail/{}'.format(code)
        content = self.get(url, _json=False)
        redeem_info = self.parse(content)
        deathline_info = self.parse_deathline(content)
        print('{} - {}'.format(code,redeem_info))
        status, first, second, require, word = self.analysis(redeem_info)
        return status, first, second, require, word,deathline_info

    def parse(self, content):
        resp = Selector(text=content)
        redeem_icon = resp.xpath('//td[contains(text(),"强赎天计数")]/following-sibling::*[1]/span/text()').extract_first()
        chinese_str = resp.xpath('//td[contains(text(),"强赎天计数")]/following-sibling::*[1]/text()').extract_first()

        if redeem_icon:
            redeem_icon = redeem_icon.strip()

        if redeem_icon=='!':
            redeem_icon=chinese_str.strip()

        return redeem_icon

    def parse_deathline(self,content):
        # 加入可转债到期数据
        resp = Selector(text=content)
        nodes = resp.xpath('//span[@class="glyphicon glyphicon-info-sign"]/following-sibling::*[1]/text()').extract()
        if len(nodes)==0:
            return None
        else:
            if nodes[0]=='最后交易日':
                txt = resp.xpath('//span[@class="glyphicon glyphicon-info-sign"]/following-sibling::*[2]/text()').extract_first()

                print('最后一交易日',txt)
                s = re.search('(\d+)年(\d+)月(\d+)日',txt)
                if s:
                    year = s.group(1)
                    month = s.group(2)
                    day = s.group(3)
                    print(year)
                    print(month)
                    print(day)
                    return '{}-{}-{}'.format(year,month,day)

            return None






    def dump_db(self, data):
        # 存入mongo
        from configure.settings import DBSelector

        client = DBSelector().mongo('qq')
        doc = client['db_parker']['{}-redeem-info'.format(self.today)]
        try:
            doc.insert_many(data)
        except Exception as e:
            print(e)

    def filters(self, result):
        for item in result:
            if not item['status']:
                if item['target_day'] - item['current_day'] <= LESS_DAY:
                    msg = "{} 当前已经达到{}天，目标天数{} ".format(item['name'], item['current_day'], item['target_day'])
                    print(msg)
                    self.notify(msg)
            if item['word']=='已满足强赎条件':
                msg = "{} 已满足强赎条件".format(item['name'])
                print(msg)
                self.notify(msg)


    def run(self):
        result = self.redemption_info()
        self.dump_local(result)
        self.dump_db(result)
        self.filters(result)

    def redemption_info(self):
        # print(self._funcs_)

        name_dict = self._funcs_.get(self.source)()
        result = []
        for k, v in name_dict.items():
            item_dict = dict()
            status, first, second, require, word,deathline_info = self.redemption_count(k)
            item_dict['code'] = k
            item_dict['name'] = v

            item_dict['status'] = status
            item_dict['current_day'] = first
            item_dict['target_day'] = second
            item_dict['period'] = require
            item_dict['word'] = word
            item_dict['last_trading_date'] = deathline_info
            item_dict['updated_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result.append(item_dict)
        return result


def main():
    app = Redemption()
    print('正在获取数据，请稍等')
    app.run()


if __name__ == '__main__':
    main()
