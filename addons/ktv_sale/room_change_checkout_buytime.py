# -*- coding: utf-8 -*-
#换房结算,适用于预售-买钟时的换房
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper

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
