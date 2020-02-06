# -*- coding=utf-8 -*-
from log.jdlogger import logger

'''
找一条第一个版本的url
'''
url = 'https://c0.3.cn/stock?skuId=1336984&area=19_1607_4773_0&venderId=1000078145&buyNum=1&choseSuitSkuIds=&cat=9192,12190,1517&extraParam={%22originid%22:%221%22}&fqsp=0&pdpin=jd_7c3992aa27d1a&pduid=1580535906442142991701&ch=1&callback=jQuery6715489'
skuId = url.split('skuId=')[1].split('&')[0]
area = url.split('area=')[1].split('&')[0]
logger.info('你的area是[ %s ]，链接的商品id是[ %s ]', area, skuId)
