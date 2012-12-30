# -*- coding: utf-8 -*-
#换房结算,适用于预售-买断时的换房
import logging
from osv import fields, osv
import decimal_precision as dp
from datetime import *
import ktv_helper

_logger = logging.getLogger(__name__)

class room_change_checkout_buyout(osv.osv):
    """
    换房情况下的结算,在预售时(买钟、买断),如果发生换房业务，则需要进行结算,结算遵循以下业务规则：
    1、预售方式不变,换房时，仍然是买钟、买断，到点关房
    2、换房前支付的现金、抵扣券、信用卡费都作为新开房的预付款处理
    3、换房前的打折卡、会员卡等信息,在换房后结算时还可使用
    4、买断情况下，只补新包厢的当时买断差价即可
    5、买钟情况下，需要根据计费方式补足钟点费、包厢费等费用
    """
    _name = "ktv.room_change_checkout_buyout"
    _inherit = "ktv.room_checkout"

    _order = "bill_datetime DESC"

    _columns = {
            'changed_room_id' : fields.many2one('ktv.room',string="新包厢",required = True,help="换房新换包厢"),
            'changed_buyout_config_id' : fields.many2one('ktv.buyout_config',string="买断",required = True,help="新包厢的买断设置id"),
            }

    def re_calculate_fee(self,cr,uid,context):
        """
        重新计算买断换房信息
        :params context dict required
                context['room_id'] integer 原包厢id required
                context['changed_room_id'] integer 新包厢id required
                context['changed_buyout_config_id'] integer 新买断id required
                context['member_id'] 会员id,可能为空
                context['discount_card_id'] 打折卡id,可能为空
                context['discounter_id'] 员工id,可能为空
        计算方法:
        1 获取原包厢最后结算信息
        2 计算新包厢应收费用信息
        3 计算各项费用应补差额
        4 计算折扣信息

        :return dict 计算后的买断换房结算信息
        """
        #原包厢
        origin_room = self.pool.get('ktv.room').browse(cr,uid,context["origin_room_id"])
        changed_room = self.pool.get('ktv.room').browse(cr,uid,context['changed_room_id'])

        #当前买断信息
        active_buyout_config = self.pool.get('ktv.buyout_config').get_active_buyout_fee(cr,uid,context['buyout_config_id'])

        #最后结账信息
        last_checkout = self.pool.get('ktv.room').get_presale_last_checkout(cr,uid,context["origin_room_id"])

        if not last_checkout:
            raise osv.except_osv(_("错误"), _('找不到包厢:%s的最后结账信息.' % origin_room.name))

        #计算已支付费用(包括使用信用卡、抵扣券、会员卡支付的费用)
        #合计应付
        origin_sum_should_fee = last_checkout.sum_should_fee
        #现金支付
        origin_cash_fee = las_checkout.cash_fee
        #信用卡
        #会员卡
        #抵扣券

        #消费时间
        ret_fee = {
                "origin_room_id" : context["origin_room_id"],
                "changed_room_id" : context['changed_room_id'],
                #原room_operate
                "ref_room_operate_id" : last_checkout.room_operate_id.id,
                "buyout_config_id" : context['buyout_config_id'],
                "open_time" : active_buyout_config['time_from'],
                "close_time" : active_buyout_config['time_to'],
                "consume_minutes" : active_buyout_config['buyout_time'],
                "present_minutes" : 0,
                "room_fee" : 0,
                "service_fee_rate" : 0,
                "service_fee" : 0,
                "sum_hourly_fee" : 0,
                "sum_hourly_fee_p" : 0,
                "sum_buffet_fee" : 0,
                "changed_room_fee" : 0,
                "changed_room_sum_hourly_fee" : active_buyout_config['buyout_fee'],
                "changed_room_sum_hourly_fee" : 0,
                "changed_room_sum_hourly_fee_p" : 0,
                "changed_room_sum_buffet_fee" : 0,
                "changed_room_service_fee" : 0,
                "changed_room_minutes" : 0,
                "merged_room_hourly_fee" : 0,
                "minimum_fee" : 0,
                "minimum_fee_diff" : 0,
                "prepay_fee" : 0,
                "drinks_fee" : 0,
                "uncheckout_drinks_fee" : 0,
                "minimum_drinks_fee" : 0,
                "guest_damage_fee" : 0,
                "member_room_fee_discount_rate" : 0,
                "member_room_fee_discount_fee" : 0,
                "discount_card_room_fee_discount_rate" : 0,
                "discount_card_room_fee_discount_fee" : 0,
                "discounter_room_fee_discount_rate" : 0,
                "discounter_room_fee_discount_fee" : 0,
                "cash_fee" : 0,
                "member_card_fee" : 0,
                "sales_voucher_fee" : 0,
                "credit_card_fee" : 0,
                "on_credit_fee" : 0,
                "free_fee" : 0,

                }
        #卡类相关信息

        #计算新买断费用信息


