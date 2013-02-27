# -*- coding: utf-8 -*-
#换房结算,适用于预售-买钟时的换房
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper
import fee_type

_logger = logging.getLogger(__name__)

class room_change_checkout_buytime(osv.osv):
    """
    换房情况下的结算,在预售时(买钟、买断),如果发生换房业务，则需要进行结算,结算遵循以下业务规则：
    1、预售方式不变,换房时，仍然是买钟、买断，到点关房
    2、换房前支付的现金、抵扣券、信用卡费都作为新开房的预付款处理
    3、换房前的打折卡、会员卡等信息,在换房后结算时还可使用
    4、买断情况下，只补新包厢的当时买断差价即可
    5、买钟情况下，需要根据计费方式补足钟点费、包厢费等费用
    """
    _name = "ktv.room_change_checkout_buytime"
    _inherit = "ktv.room_checkout"
    _order = "bill_datetime DESC"
    _columns = {
            #原结账id,可以是room_checkout_buyout或room_checkout_buytime
            'changed_room_id' : fields.many2one('ktv.room',string="新包厢",required = True,help="换房新换包厢"),
            }

    def re_calculate_fee(self,cr,uid,context):
        '''
        买钟换房重新计算费用
        原系统中,对于买钟换房费用的计算,有两种方式：
        1、按照新包厢全额补差价
        2、按照在原包厢、新包厢中的不同消费时间计算后补差价
        由于第2种方式计算比较复杂,本系统中暂不实现
        :param context['room_id'] integer 原包厢id required
        :param context['changed_room_id'] integer 新包厢id required
        :param context['member_id'] integer 会员卡id
        :param context['discount_card_id'] integer 打折卡id
        :param context['discounter_id'] integer 员工id
        :return dict 重新计算后的买钟换房对象
        计算方法:
        1 获取原包厢最后一次买钟结算(room_checkout_buytime)信息
        2 计算新包厢应收取的各种费用信息
        3 计算各项费用应补差额
        4 计算折扣费用
        5 返回计算后的数据信息
        '''

