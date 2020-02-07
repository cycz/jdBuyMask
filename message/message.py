# -*- encoding=utf8 -*-
from message.jdEmail import sendMail
from message.wechat_ftqq import sendWechat
from log.jdlogger import logger


class message(object):
    """消息推送类"""

    def __init__(self, messageTtpe, sc_key, mail):
        if messageTtpe == '2':
            if not sc_key:
                raise Exception('sc_key can not be empty')
            self.sc_key = sc_key
        elif messageTtpe == '1':
            if not mail:
                raise Exception('mail can not be empty')
            self.mail = mail
        self.messageTtpe = messageTtpe

    def send(self, desp='', isOrder=False):
        desp = str(desp)
        if isOrder:
            msg = desp + ' 类型口罩，已经下单了。24小时内付款'
        else:
            msg = desp + ' 类型口罩，下单失败了，快去抢购！'
        if self.messageTtpe == '1':
            sendMail(self.mail, msg)
        if self.messageTtpe == '2':
            sendWechat(sc_key=self.sc_key, desp=msg)
