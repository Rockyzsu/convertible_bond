# 参考
# https://mp.weixin.qq.com/s?src=11&timestamp=1625502406&ver=3172&signature=A0YcniD9-1jRDsrSsrpzlWqAw2wUFmOLGNyPOvELMYkVMPWa75dDOEpJiC32ydvbxhn8JnKC*QsPYA94X-67NbPrz9x3g7OE*0gl0ydghEuhjReO2LdPtOtT75ypaSC6&new=1

import datetime
updatetime = int(datetime.now().strftime('%Y%m%d'))
inputfile = 'D:/dsod/bond/networkgrasp/'+datetime.now().strftime('%Y-%m-%d')+'/s_daily.csv'
timeToMarket = 20191201
financial_year = 2019
financial_quarter = 3

histdata = pd.read_csv("D:/dsod/basicdata/hist_data.csv", sep=',', header = 0)
histdata = histdata.sort_values(by = ['stockcode', '日期'], ascending = False)
histdata  = histdata.groupby('stockcode').head(60).reset_index(drop=True)
histdata = histdata[['stockcode', '收盘价']]
stock_standard_var = histdata.groupby('stockcode').agg(np.std, ddof=0)
stock_standard_var  = stock_standard_var.reset_index()
stock_standard_var.columns = ['stockcode', '收盘价_stvar']
temp = histdata.groupby('stockcode').agg(np.mean)
temp = temp.reset_index()
temp.columns = ['stockcode', '收盘价_mean']

stock_standard_var = pd.merge(stock_standard_var, temp, how = 'left', on = 'stockcode')

# 结果数据
stock_standard_var['收盘价_cv'] = stock_standard_var.收盘价_stvar/stock_standard_var.收盘价_mean


# read data
bond_daily = pd.read_csv(inputfile, sep=',', header = 0)
bond_daily.create_date = updatetime
temp = ['bond_id', 'bond_nm', 'stock_id', 'convert_dt', 'maturity_dt', 'next_put_dt',
        'redeem_price_ratio', 'orig_iss_amt', 'curr_iss_amt', 'rating_cd', 'put_price','convert_price',
'issuer_rating_cd', 'guarantor', 'qflag', 'margin_flg',
'convert_value', 'premium_rt', 'year_left', 'ytm_rt', 'ytm_rt_tax',
'price', 'volume', 'adj_scnt', 'adj_cnt', 'force_redeem_price', 'convert_amt_ratio', 'create_date', "pb"]
bond_x = bond_daily[temp]

bond_x.convert_dt = pd.to_datetime(bond_x.convert_dt, format='%Y-%m-%d').dt.date
bond_x.maturity_dt = pd.to_datetime(bond_x.maturity_dt, format='%Y-%m-%d').dt.date
bond_x.next_put_dt = pd.to_datetime(bond_x.next_put_dt, format='%Y-%m-%d').dt.date
bond_x.create_date = pd.to_datetime(bond_x.create_date, format='%Y%m%d').dt.date
bond_x['days_to_convert_dt'] = (bond_x['convert_dt'] - bond_x['create_date']).dt.days
del bond_x['convert_dt']
bond_x['days_to_maturity_dt'] = (bond_x['maturity_dt'] - bond_x['create_date']).dt.days
del bond_x['maturity_dt']
bond_x['days_to_next_put_dt'] = (bond_x['next_put_dt'] - bond_x['create_date']).dt.days
del bond_x['next_put_dt']


bond_x.rating_cd = bond_x.rating_cd.replace(" ", "", regex=True)
bond_x.issuer_rating_cd = bond_x.issuer_rating_cd.replace(" ", "", regex=True)
rating = pd.read_csv("D:/dsod/bond/dict/rating.csv", sep=',', header = 0)
bond_x = pd.merge(bond_x, rating, how = 'left', on = 'rating_cd')
del bond_x['rating_cd']
rating.columns = ['issuer_rating_cd', 'issuer_评级']
bond_x = pd.merge(bond_x, rating, how = 'left', on = 'issuer_rating_cd')
del bond_x['issuer_rating_cd']
bond_x.loc[bond_x.issuer_评级.isnull(), 'issuer_评级'] = bond_x.loc[bond_x.issuer_评级.isnull(), '评级']
bond_x.loc[bond_x.评级.isnull(), '评级'] = bond_x.loc[bond_x.评级.isnull(), 'issuer_评级']


del bond_x['put_price']
bond_x.loc[bond_x.redeem_price_ratio.isnull(), 'redeem_price_ratio'] = 120

# 处理担保字段
bond_x.guarantor = bond_x.guarantor.replace(" ", "", regex=True)
bond_x['guarantor'] = np.where(bond_x.guarantor == '无担保', 0, 1)


# 处理是否是可交换债
bond_x['qflag'] = np.where(bond_x.qflag == 'Q', 1, 0)

# 处理是否是融资融券标的
bond_x['margin_flg'] = np.where(bond_x.margin_flg == 'R', 1, 0)

# 注意在预测价格时一定要除去与溢价率相关的字段 Why ????????????
del bond_x['margin_flg']
del bond_x['ytm_rt']
del bond_x['ytm_rt_tax']
del bond_x['force_redeem_price']
del bond_x['premium_rt']

# 无回售的全部填最大值,无回售威胁下调转股价动力比较小
bond_x.loc[bond_x.days_to_next_put_dt.isnull(), 'days_to_next_put_dt'] = np.nanmax(bond_x.days_to_next_put_dt)

# 回售条款就是对转债持有者最厉害的保护，你觉得买的不满意，你可以以一定价格回售给公司，但有些公司自持禀赋优秀，就没设置回售条款，所以要处理下回售日期，回售日距今天数缺失的转债总是付给它最大值。


# 转债的剩余规模会逐渐变小
bond_x['convert_amt_ratio'] = bond_x['convert_amt_ratio'].str.rstrip('%').astype('float') / 100.0
bond_x.bond_id = bond_x.bond_id.astype(str)

# 关联变异系数
stock_standard_var = stock_standard_var[['stockcode', '收盘价_cv']]
stock_standard_var.columns = ['stock_id', '收盘价_cv']
bond_x = pd.merge(bond_x, stock_standard_var, how = 'left', on = 'stock_id')

# 关联正股排名数据
inputfile = 'D:/dsod/bond/result/stock_rank'+datetime.now().strftime('%Y%m%d')+'.csv'
stock_rank = pd.read_csv(inputfile, sep=',', header = 0)
stock_rank = stock_rank.drop(['name', 'industry', 'area', 'rev_scale', 'ep_scale', 'nmc_per_holder_scale', 'roe_scale', 'cashratio_scale', 'ranks'], axis=1)
stock_rank = stock_rank.rename(columns = {"code":"stock_id"})
stock_rank = stock_rank.drop_duplicates()
bond_x = pd.merge(bond_x, stock_rank, how = 'left', on = 'stock_id')
bond_x = bond_x[~bond_x.rank_score.isnull()]

# 加载建模相关的模块
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split


bond_x =  bond_x.reset_index(drop = True)
idcolumns = ['bond_id','bond_nm','create_date','stock_id', 'price']
X = bond_x.drop(idcolumns, axis = 1).values
y = bond_x['price'].values
sc =  MinMaxScaler()
X_train = sc.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05)
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)


'''
1句声明一个随机森林模型，并设定参数，这里主要设定下树数和最小分裂节点样本数；
2句使用训练集训练模型，即模型通过这些学习到什么样的x应该对应什么样的y值；
3句声明xgb模型及其参数，我们设置了学习率为0.1，迭代次数为600，每次使用80%的数据；
4句训练xgb模型。
'''
regressor1 = RandomForestRegressor(n_estimators=30,
                                  min_samples_split=2, oob_score=True)
regressor1.fit(X_train, y_train)
regressor2 = XGBRegressor(learning_rate=0.1, n_estimators = 600, subsample=0.8)
regressor2.fit(X_train, y_train)

y_pred = (regressor1.predict(X_test) + regressor2.predict(X_test))/2

from sklearn import metrics
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))


# 输出变量重要性
importances = list(regressor1.feature_importances_)
columnsname = list(bond_x.drop(idcolumns, axis = 1).columns)
importances = pd.DataFrame(importances)
importances.columns = ['importances']
importances['columnsname'] = columnsname
outfile = 'D:/dsod/bond/result/importances.csv'
importances.to_csv(outfile,index =None, encoding = 'gbk')
