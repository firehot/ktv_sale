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
            #原买断及原包厢信息通过计算获取
            'buyout_config_id' : fields.many2one('ktv.buyout_config',string="买断",required = True,help="新包厢的买断设置id"),
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
        active_buyout_config = self.pool.get('ktv.buyout_config').get_active_buyout_fee(cr,uid,context['changed_buyout_config_id'])

        #最后结账信息
        last_checkout = self.pool.get('ktv.room').get_presale_last_checkout(cr,uid,context["origin_room_id"])

        if not last_checkout:
            raise osv.except_osv(_("错误"), _('找不到包厢:%s的最后结账信息.' % origin_room.name))

        #原包厢结账信息
        last_checkout_info = {
                #原包厢
                "room_id" : last_checkout.room_operate_id.room_id.id,
                #原买断信息
                "buyout_config_id" : last_checkout.buyout_config_id and [last_checkout.buyout_config_id.id,last_checkout.buyout_config_id.name] or None,
                "open_time" : last_checkout.open_time,
                #关闭时间是当前时间
                "close_time" : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                #重新计算消费时长
                "consume_minutes" : ktv_helper.timedelta_minutes(ktv_helper.strptime(last_checkout.open_time),datetime.now()),
                #现金
                "cash_fee" : last_checkout.cash_fee,
                #信用卡
                "credit_card_no" : last_checkout.credit_card_no or None,
                "credit_card_fee" : last_checkout.credit_card_fee,
                #会员卡
                "member_card_id" : last_checkout.member_card_id and last_checkout.member_card_id.id or None,
                "member_card_fee" : last_checkout.member_card_fee,
                #抵扣券
                "sales_voucher_fee" : last_checkout.sales_voucher_fee,
                #挂账
                "on_crediter_id" : last_checkout.on_crediter_id and last_checkout.on_crediter_id.id or None,
                "on_credit_fee" : last_checkout.on_credit_fee,
                #免单
                "freer_id" : last_checkout.freer_id and last_checkout.freer_id.id or None,
                "free_fee" : last_checkout.free_fee,
                #合计付款
                "sum_should_fee" : last_checkout.sum_should_fee,
                }

        #应补钟点费 = 新包厢买断费 - 原支付费用
        changed_room_sum_hourly_fee = active_buyout_config['buyout_fee'] - last_checkout_info['sum_should_fee']

        #计算打折信息
        ret = {
                #原费用信息
                "last_checkout_info" : last_checkout_info,
                "origin_room_id" : context["origin_room_id"],
                "changed_room_id" : context['changed_room_id'],
                #原room_operate
                "ref_room_operate_id" : last_checkout.room_operate_id.id,
                "buyout_config_id" : context['changed_buyout_config_id'],
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
                "changed_room_sum_hourly_fee" : changed_room_sum_hourly_fee,
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
                "discount_fee" : 0,
                "discount_rate" : 0,
                "cash_fee" : 0,
                "member_card_fee" : 0,
                "sales_voucher_fee" : 0,
                "credit_card_fee" : 0,
                "on_credit_fee" : 0,
                "free_fee" : 0,
                }
        #同时只能有一种打折方式可用
        #会员打折费用

        #打折卡打折
        if 'discount_card_id' in context and context['discount_card_id']:
            discount_card = self.pool.get('ktv.discount_card').browse(cr,uid,context['discount_card_id'])
            ret['discount_card_id'] = context['discount_card_id']
            ret['discount_card_room_fee_discount_rate'] = discount_card_room_fee_discount_rate = discount_card.discount_card_type_id.room_fee_discount
            ret['discount_card_room_fee_discount_fee'] = discount_card_room_fee_discount_fee = active_buyout_config['buyout_fee']*(100 - discount_card_room_fee_discount_rate)/100
            ret['discount_rate'] = discount_card_room_fee_discount_rate
            ret['discount_fee'] = discount_card_room_fee_discount_fee

        if 'member_id' in context and context['member_id']:
            the_member = self.pool.get('ktv.member').browse(cr,uid,context['member_id'])
            ret['member_id'] = context['member_id']
            ret['member_room_fee_discount_rate'] = member_room_fee_discount_rate = the_member.member_class_id.room_fee_discount
            ret['member_room_fee_discount_fee'] = member_room_fee_discount_fee = active_buyout_config['buyout_fee']*(100 - member_room_fee_discount_rate)/100
            ret['discount_rate'] = member_room_fee_discount_rate
            ret['discount_fee'] = member_room_fee_discount_fee


        #员工打折
        #TODO
        #if 'discounter_id' in context and context['discounter_id']:

        #默认情况下,重新计算后,费用做如下处理:

        ret['sum_should_fee'] = changed_room_sum_hourly_fee - ret['discount_fee']
        ret['cash_fee'] = ret['sum_should_fee']
        ret['act_pay_fee'] = ret['cash_fee']
        ret['change_fee'] = 0.0
        ret.update({
            'member_card_fee' : 0.0,
            'credit_card_fee' : 0.0,
            'sales_voucher_fee' : 0.0,
            })
        return ret
