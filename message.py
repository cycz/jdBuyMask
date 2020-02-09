# -*- encoding=utf8 -*-
from jdEmail import sendMail
from wechat_ftqq import sendWechat


class message(object):
    """消息推送类"""

    def __init__(self, messageType, sc_key, mail):
        if messageType == '2':
            if not sc_key:
                raise Exception('sc_key can not be empty')
            self.sc_key = sc_key
        elif messageType == '1':
            if not mail:
                raise Exception('mail can not be empty')
            self.mail = mail
        self.messageType = messageType

    def send(self, desp='', isOrder=False):
        desp = str(desp)
        if isOrder:
            msg = desp + ' 类型口罩，已经下单了。24小时内付款'
        else:
            msg = desp + ' 类型口罩，下单失败了'
        if self.messageType == '1':
            sendMail(self.mail, msg)
        if self.messageType == '2':
            sendWechat(sc_key=self.sc_key, desp=msg)

    def sendAny(self, desp=''):
        desp = str(desp)
        msg = desp
        if self.messageType == '1':
            sendMail(self.mail, msg)
        if self.messageType == '2':
            sendWechat(sc_key=self.sc_key, desp=msg)
