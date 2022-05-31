# 溢价率计算 数据和集思录的吻合
def cb_premium_rt(bond_price,convert_price,sprice):
    convert_value = 100.00/convert_price*sprice
    premium_rt = (bond_price - convert_value)/convert_value*100
    return premium_rt

if __name__=='__main__':
    bond_price,convert_price,sprice = 499.820,9.04,7.31
    result = cb_premium_rt(bond_price,convert_price,sprice)
    print(result) # 518.1084541723666

