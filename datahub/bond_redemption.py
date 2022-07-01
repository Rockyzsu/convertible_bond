
from datetime import datetime
import fire
import sys
import pandas as pd

sys.path.append('..')
from common.BaseService import BaseService
from common.DataFetch import DataFetcher
from parsel import Selector
from configure.settings import DBSelector


class RedemptionInfo(BaseService):

    def __init__(self, logfile='../log/redemptioninfo.log'):
        super().__init__(logfile)


    @property
    def headers(self):
        h = {
            'Host': 'www.jisilu.cn',
            'Referer': 'https://www.jisilu.cn/web/data/cb/delisted',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
        
        return h

    def get_current_bond_info(self):
        bond_info = DataFetcher()
        return bond_info.jsl_bond


    def get_delisted_code(self):
        delisted_bond = self.get_delisted_bond()
        code_list =[i.get('bond_id') for i in delisted_bond]
        return code_list

    def run(self):
        code_list = self.get_delisted_code()
        code_= self.get_current_bond_info()['可转债代码'].tolist() # 数据库获取集思录数据
        
        code_list.extend(code_)
        result_list=[]
        for code in code_list:
            result = self.get_bond_redeem_price(code)
            result_list.append(result)
            print('update code ',code)
        
        self.dump_mongo(result_list)

    def dump_mongo(self,data):
        client = DBSelector().mongo('qq')
        doc=client['db_stock']['bond_redeem_price']
        doc.insert_many(data)


    def get_delisted_bond(self):
        # 获取退市转债
        url='https://www.jisilu.cn/webapi/cb/delisted/'
        js = self.get(url=url,_json=True)
        return js['data']

    def get_bond_redeem_price(self,code):
        # code = '113550'
        redemp_url = 'https://www.jisilu.cn/data/convert_bond_detail/{}'
        content = self.get(url=redemp_url.format(code))
        result_dict = self.parse(content)
        result_dict['code']=code
        result_dict['updated']=datetime.now()
        return result_dict

    def parse(self,content):
        resp = Selector(text=content)        
        price = resp.xpath('//div[@id="tc_data"]//td[@class="jisilu_title" and contains(text(),"到期赎回价")]/following-sibling::*[1]/text()').extract_first()
        result_dict = {}  

        try:
            red_price = float(price.strip())
        except:
            red_price_price =0

        result_dict['redeem_price']=red_price
        result_dict['html']=content # html也保存一份
        return result_dict

    def create_mapper(self):
        delist_ = self.get_delisted_bond()
        print(delist_)
        result = {item['bond_id']:item['bond_nm'] for item in delist_}


        bond_info = DataFetcher()
        df= bond_info.jsl_bond
        existed_bond_list = dict(zip(df['可转债代码'].tolist(),df['可转债名称'].tolist()))
        result.update(existed_bond_list)
        return result

    def update(self):
        # 更新名字
        bond_dict = self.create_mapper()
        client = DBSelector().mongo('qq')
        doc=client['db_stock']['bond_redeem_price']
        for k,v in bond_dict.items():
            doc.update_one({'code':k},{'$set':{'name':v}})

    def output_excel(self):
        
        client = DBSelector().mongo('qq')
        doc=client['db_stock']['bond_redeem_price']

        result =[]
        
        for item in doc.find({},{'html':0}):
            tmp_dict = {}
            try:
                tmp_dict['code']=item['code']
                tmp_dict['name']=item['name']
                tmp_dict['redeem_price']=item['redeem_price']
            except Exception as e:
                print(item['code'])

            result.append(tmp_dict)

        df = pd.DataFrame(result)
        df.to_excel('bond_redeem_price.xlsx',encoding='utf8')

    def clear(self):

        client = DBSelector().mongo('qq')
        doc=client['db_stock']['bond_redeem_price']
        count=doc.remove({'name':{'$exists':False}})
        print(count)

    def count(self):
        client = DBSelector().mongo('qq')
        doc=client['db_stock']['bond_redeem_price']
        count=doc.find({},{'_id':1,'html':0}).count()
        print(count)

def main():
    app = RedemptionInfo()
    df = app.get_current_bond_info()
    print(df['可转债代码'].tolist())
    # app.run()
    # print(app.create_mapper())
    # app.update()
    # app.output_excel()
    # app.clear()
    # app.count()


    


if __name__ == '__main__':
    fire.Fire(main)
