# 强赎天数计算
import datetime
import sys

import requests

sys.path.append('..')
from configure.settings import DBSelector
class RedeemDayCoundDown:


    def __init__(self):
        self.url='https://www.jisilu.cn/data/cbnew/redeem_list/?___jsl=LST___'


    def get_data(self):
        for _ in range(5):
            try:
                r = requests.get(self.url,headers={'User-Agent':'Microsoft Chrome Firefox'})
            except:
                pass
            else:
                break

        resp = r.json()
        return resp

    def parse(self,js):
        rows = js.get('rows')
        lines=[]
        for row in rows:
            line = row.get('cell')
            lines.append(line)
        return lines


    def dump_db(self,ret_data):
        today = datetime.datetime.now().strftime("%Y%m%d")
        client = DBSelector().mongo('qq')
        ret = client['db_redeem_count'][today].insert_many(ret_data)
        print(ret)

    def run(self):
        js=self.get_data()
        ret_data= self.parse(js)
        self.dump_db(ret_data)

if __name__ == '__main__':
    app = RedeemDayCoundDown()
    app.run()

