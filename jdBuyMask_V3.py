# -*- coding=utf-8 -*-
'''
2020/2/13
(避免滥用，代码已经废弃，现已不更新，有需要请适量使用exe版本)
京东抢购口罩程序V3版本
'''
import sys
import traceback

from bs4 import BeautifulSoup

from config import Config
from jdProgram import *
from jdlogger import logger
from message import message
from util import *
from util import _setDNSCache

'''
需要修改
'''
global cookies_String, mail, sc_key, messageType, area, skuidsString, skuids, captchaUrl, eid, fp, payment_pwd


def getconfig():
    global_config = Config()
    global cookies_String, mail, sc_key, messageType, area, skuidsString, skuids, captchaUrl, eid, fp, payment_pwd
    # cookie 网页获取
    cookies_String = global_config.getRaw('config', 'cookies_String')
    # 有货通知 收件邮箱
    mail = global_config.getRaw('config', 'mail')
    # 方糖微信推送的key  不知道的请看http://sc.ftqq.com/3.version
    sc_key = global_config.getRaw('config', 'sc_key')
    # 推送方式 1（mail）或 2（wechat）
    messageType = global_config.getRaw('config', 'messageType')
    # 地区id
    area = global_config.getRaw('config', 'area')
    # 商品id
    skuidsString = global_config.getRaw('V3', 'skuid')
    skuids = str(skuidsString).split(',')
    # 验证码服务地址
    captchaUrl = global_config.getRaw('Temporary', 'captchaUrl')
    if len(skuids[0]) == 0:
        logger.error('请在configDemo.ini文件中输入你的商品id')
        sys.exit(1)
    '''
    备用
    '''
    # eid
    eid = global_config.getRaw('Temporary', 'eid')
    fp = global_config.getRaw('Temporary', 'fp')
    # 支付密码
    payment_pwd = global_config.getRaw('config', 'payment_pwd')


# 初次
configTime = int(time.time())
getconfig()
configMd5 = getconfigMd5()
message = message(messageType=messageType, sc_key=sc_key, mail=mail)

is_Submit_captcha = False
submit_captcha_rid = ''
submit_captcha_text = ''
encryptClientInfo = ''
submit_Time = 0
session = requests.session()
checksession = requests.session()
session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Connection": "keep-alive"
}
checksession.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Connection": "keep-alive"
}
manual_cookies = {}


def get_tag_value(tag, key='', index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')


def response_status(resp):
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


for item in cookies_String.split(';'):
    name, value = item.strip().split('=', 1)
    # 用=号分割，分割1次
    manual_cookies[name] = value
    # 为字典cookies添加内容

cookiesJar = requests.utils.cookiejar_from_dict(manual_cookies, cookiejar=None, overwrite=True)
session.cookies = cookiesJar


def validate_cookies():
    for flag in range(1, 3):
        try:
            targetURL = 'https://order.jd.com/center/list.action'
            payload = {
                'rid': str(int(time.time() * 1000)),
            }
            resp = session.get(url=targetURL, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                logger.info('登录成功')
                return True
            else:
                logger.info('第【%s】次请重新获取cookie', flag)
                time.sleep(5)
                continue
        except Exception as e:
            logger.info('第【%s】次请重新获取cookie', flag)
            time.sleep(5)
            continue
    message.sendAny('脚本登录cookie失效了，请重新登录')
    sys.exit(1)


def getUsername():
    userName_Url = 'https://passport.jd.com/new/helloService.ashx?callback=jQuery339448&_=' + str(
        int(time.time() * 1000))
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Connection": "keep-alive"
    }
    resp = session.get(url=userName_Url, allow_redirects=True)
    resultText = resp.text
    resultText = resultText.replace('jQuery339448(', '')
    resultText = resultText.replace(')', '')
    usernameJson = json.loads(resultText)
    logger.info('登录账号名称' + usernameJson['nick'])


'''
检查是否有货
'''


def check_item_stock(itemUrl):
    response = session.get(itemUrl)
    if (response.text.find('无货') > 0):
        return True
    else:
        return False


'''
取消勾选购物车中的所有商品
'''


def cancel_select_all_cart_item():
    url = "https://cart.jd.com/cancelAllItem.action"
    data = {
        't': 0,
        'outSkus': '',
        'random': random.random()
    }
    resp = session.post(url, data=data)
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


'''
勾选购物车中的所有商品
'''


def select_all_cart_item():
    url = "https://cart.jd.com/selectAllItem.action"
    data = {
        't': 0,
        'outSkus': '',
        'random': random.random()
    }
    resp = session.post(url, data=data)
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


'''
删除购物车选中商品
'''


def remove_item():
    url = "https://cart.jd.com/batchRemoveSkusFromCart.action"
    data = {
        't': 0,
        'null': '',
        'outSkus': '',
        'random': random.random(),
        'locationId': '19-1607-4773-0'
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.37",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://cart.jd.com/cart.action",
        "Host": "cart.jd.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Encoding": "zh-CN,zh;q=0.9,ja;q=0.8",
        "Origin": "https://cart.jd.com",
        "Connection": "keep-alive"
    }
    resp = session.post(url, data=data, headers=headers)
    logger.info('清空购物车')
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


'''
购物车详情
'''


def cart_detail():
    url = 'https://cart.jd.com/cart.action'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Host": "cart.jd.com",
        "Connection": "keep-alive"
    }
    resp = session.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    cart_detail = dict()
    for item in soup.find_all(class_='item-item'):
        try:
            sku_id = item['skuid']  # 商品id
        except Exception as e:
            logger.info('购物车中有套装商品，跳过')
            continue
        try:
            # 例如：['increment', '8888', '100001071956', '1', '13', '0', '50067652554']
            # ['increment', '8888', '100002404322', '2', '1', '0']
            item_attr_list = item.find(class_='increment')['id'].split('_')
            p_type = item_attr_list[4]
            promo_id = target_id = item_attr_list[-1] if len(item_attr_list) == 7 else 0

            cart_detail[sku_id] = {
                'name': get_tag_value(item.select('div.p-name a')),  # 商品名称
                'verder_id': item['venderid'],  # 商家id
                'count': int(item['num']),  # 数量
                'unit_price': get_tag_value(item.select('div.p-price strong'))[1:],  # 单价
                'total_price': get_tag_value(item.select('div.p-sum strong'))[1:],  # 总价
                'is_selected': 'item-selected' in item['class'],  # 商品是否被勾选
                'p_type': p_type,
                'target_id': target_id,
                'promo_id': promo_id
            }
        except Exception as e:
            logger.error("商品%s在购物车中的信息无法解析，报错信息: %s，该商品自动忽略", sku_id, e)

    logger.info('购物车信息：%s', cart_detail)
    return cart_detail


'''
修改购物车商品的数量
'''


def change_item_num_in_cart(sku_id, vender_id, num, p_type, target_id, promo_id):
    url = "https://cart.jd.com/changeNum.action"
    data = {
        't': 0,
        'venderId': vender_id,
        'pid': sku_id,
        'pcount': num,
        'ptype': p_type,
        'targetId': target_id,
        'promoID': promo_id,
        'outSkus': '',
        'random': random.random(),
        # 'locationId'
    }
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart",
        "Connection": "keep-alive"
    }
    resp = session.post(url, data=data)
    return json.loads(resp.text)['sortedWebCartResult']['achieveSevenState'] == 2


'''
添加商品到购物车
'''


def add_item_to_cart(sku_id):
    url = 'https://cart.jd.com/gate.action'
    payload = {
        'pid': sku_id,
        'pcount': 1,
        'ptype': 1,
    }
    resp = session.get(url=url, params=payload)
    if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
        result = True
    else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
        soup = BeautifulSoup(resp.text, "html.parser")
        result = bool(soup.select('h3.ftx-02'))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

    if result:
        logger.info('%s  已成功加入购物车', sku_id)
    else:
        logger.error('%s 添加到购物车失败', sku_id)


def get_checkout_page_detail():
    """获取订单结算页面信息

    该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

    :return: 结算信息 dict
    """
    url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
    # url = 'https://cart.jd.com/gotoOrder.action'
    payload = {
        'rid': str(int(time.time() * 1000)),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
        'Host': 'trade.jd.com',
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if not response_status(resp):
            logger.error('获取订单结算页信息失败')
            return ''
        if '刷新太频繁了' in resp.text:
            return '刷新太频繁了'
        soup = BeautifulSoup(resp.text, "html.parser")
        showCheckCode = get_tag_value(soup.select('input#showCheckCode'), 'value')
        if not showCheckCode:
            pass
        else:
            if showCheckCode == 'true':
                logger.info('提交订单需要验证码')
                global is_Submit_captcha, encryptClientInfo
                encryptClientInfo = get_tag_value(soup.select('input#encryptClientInfo'), 'value')
                is_Submit_captcha = True
        risk_control = get_tag_value(soup.select('input#riskControl'), 'value')

        order_detail = {
            'address': soup.find('span', id='sendAddr').text[5:],  # remove '寄送至： ' from the begin
            'receiver': soup.find('span', id='sendMobile').text[4:],  # remove '收件人:' from the begin
            'total_price': soup.find('span', id='sumPayPriceId').text[1:],  # remove '￥' from the begin
            'items': []
        }

        logger.info("下单信息：%s", order_detail)
        return risk_control
    except requests.exceptions.RequestException as e:
        logger.error('订单结算页面获取异常：%s' % e)
    except Exception as e:
        logger.error('下单页面数据解析异常：%s', e)
    return ''


'''
商品下柜检测
'''


def item_removed(sku_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'item.jd.com',
    }
    url = 'https://item.jd.com/{}.html'.format(sku_id)
    page = requests.get(url=url, headers=headers)
    return '该商品已下柜' not in page.text


'''
购买环节
测试三次
'''


def buyMask(sku_id):
    risk_control = get_checkout_page_detail()
    if risk_control == '刷新太频繁了':
        return False
    if len(risk_control) > 0:
        if submit_order(session, risk_control, sku_id, skuids, submit_Time, encryptClientInfo, is_Submit_captcha,
                        payment_pwd, submit_captcha_text, submit_captcha_rid):
            return True


def V3check(skuId):
    select_all_cart_item()
    remove_item()
    validate_cookies()
    logger.info('校验是否还在登录')
    add_item_to_cart(skuId)
    if not item_removed(skuId):
        logger.info('[%s]已下柜商品', skuId)
        sys.exit(1)


def V3AutoBuy(inStockSkuid):
    if skuId in inStockSkuid:
        global submit_Time
        submit_Time = int(time.time() * 1000)
        logger.info('[%s]类型口罩有货啦!马上下单', skuId)
        skuidUrl = 'https://item.jd.com/' + skuId + '.html'
        if buyMask(skuId):
            message.send(skuidUrl, True)
            sys.exit(1)
        else:
            if item_removed(skuId):
                message.send(skuidUrl, False)
            else:
                logger.info('[%s]已下柜商品', skuId)
                sys.exit(1)


def check_Config():
    global configMd5, configTime
    nowMd5 = getconfigMd5()
    configTime = time.time()
    if not nowMd5 == configMd5:
        logger.info('配置文件修改，重新读取文件')
        getconfig()
        configMd5 = nowMd5


# _setDNSCache()
if len(skuids) != 1:
    logger.info('请准备一件商品')
skuId = skuids[0]
flag = 1
while (1):
    try:
        # 初始化校验
        if flag == 1:
            logger.info('当前是V3版本')
            validate_cookies()
            getUsername()
            select_all_cart_item()
            remove_item()
            add_item_to_cart(skuId)
        # 检测配置文件修改
        if int(time.time()) - configTime >= 60:
            check_Config()
        logger.info('第' + str(flag) + '次 ')
        flag += 1
        # 检查库存模块
        inStockSkuid = check_stock(checksession, skuids, area)
        # 自动下单模块
        V3AutoBuy(inStockSkuid)
        # 休眠模块
        timesleep = random.randint(1, 3) / 10
        time.sleep(timesleep)
        # 校验是否还在登录模块
        if flag % 100 == 0:
            V3check(skuId)
    except Exception as e:
        print(traceback.format_exc())
        time.sleep(10)
