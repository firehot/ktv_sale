# -*- coding: utf-8 -*-
#换房结算,适用于预售-买钟时的换房
from datetime import *
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper
import fee_type
from room import room


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
        #原包厢
        origin_room = self.pool.get('ktv.room').browse(cr,uid,context["room_id"])
        #换房后的包厢
        changed_room = self.pool.get('ktv.room').browse(cr,uid,context['changed_room_id'])

        #最后结账信息
        last_checkout = self.pool.get('ktv.room').get_presale_last_checkout(cr,uid,context["room_id"])

        if not last_checkout:
            raise osv.except_osv(_("错误"), _('找不到包厢:%s的最后结账信息.' % origin_room.name))

        #原包厢结账信息
        last_checkout_info = {
                #原包厢
                "room_id" : last_checkout.room_operate_id.room_id.id,
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

        #以下获取新包厢买钟总费用
        #原买钟时间
        buy_minutes = last_checkout.consume_minutes
        #赠送时长
        present_minutes = last_checkout.present_minutes

        #prepay_fee 计算预付费用
        #预付费用 = prepay_fee + sum_should_fee
        prepay_fee = last_checkout.prepay_fee + last_checkout.sum_should_fee

        #(包厢id,包厢费,最低消费,按位最低消费,最低计费人数,会员标志,钟点费,钟点费折扣(%),按位钟点费,按位钟点费折扣(%))
        (r_id,room_fee,minimum_fee,minimum_fee_p,minimum_persons,is_member_hourly_fee,hourly_fee,hourly_discount,hourly_fee_p,hourly_p_discount) = self.pool.get('ktv.room').get_current_fee_tuple(cr,uid,context['changed_room_id'],context)

        #默认无折扣
        discount_rate = 0;discount_fee = 0
        #客人人数
        persons_count = ('persons_count' in context and context['persons_count']) or minimum_persons
        #换房后钟点费合计:
        new_sum_hourly_fee = hourly_fee*buy_minutes

        #时长合计 = 买钟时间 + 赠送时间
        sum_minutes = buy_minutes + present_minutes

        #应补买钟费费用 = 新包厢总买钟费用 - 原支付费用
        changed_room_sum_hourly_fee = new_sum_hourly_fee - prepay_fee

        #计算新包厢消费时长及关闭时间
        #在原包厢已消费时长
        al_consume_minutes = ktv_helper.timedelta_minutes(datetime.now(),ktv_helper.strptime(last_checkout.open_time))
        #在新包厢消费时长
        changed_open_time = datetime.now()
        #在新包厢的消费时长
        changed_consume_minutes = buy_minutes - al_consume_minutes

        changed_close_time = changed_open_time + timedelta(minutes = changed_consume_minutes)
        #计算打折信息
        ret = {
                #原费用信息
                "last_checkout_info" : last_checkout_info,
                "room_id" : context["room_id"],
                "changed_room_id" : context['changed_room_id'],
                "fee_type_id" : last_checkout.fee_type_id.id,
                #TODO 需要处理price_class_id
                #"price_class_id" : last_checkout.price_class_id.id,
                "open_time" : ktv_helper.strftime(changed_open_time),
                "close_time" : ktv_helper.strftime(changed_close_time),
                "consume_minutes" : 0,
                "present_minutes" : present_minutes,
                "room_fee" : 0,
                "service_fee_rate" : 0,
                "service_fee" : 0,
                "sum_hourly_fee" : 0,
                "sum_hourly_fee_p" : 0,
                "sum_buffet_fee" : 0,
                "changed_room_fee" : room_fee,
                "changed_room_sum_hourly_fee" : changed_room_sum_hourly_fee,
                "changed_room_sum_hourly_fee_p" : 0,
                "changed_room_sum_buffet_fee" : 0,
                "changed_room_service_fee" : 0,
                "changed_room_minutes" : changed_consume_minutes,
                "merged_room_hourly_fee" : 0,
                "minimum_fee" : 0,
                "minimum_fee_diff" : 0,
                "prepay_fee" : prepay_fee,
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
            ret['discount_card_room_fee_discount_fee'] = discount_card_room_fee_discount_fee = new_sum_hourly_fee*(100 - discount_card_room_fee_discount_rate)/100
            ret['discount_rate'] = discount_card_room_fee_discount_rate
            ret['discount_fee'] = discount_card_room_fee_discount_fee

        if 'member_id' in context and context['member_id']:
            the_member = self.pool.get('ktv.member').browse(cr,uid,context['member_id'])
            ret['member_id'] = context['member_id']
            ret['member_room_fee_discount_rate'] = member_room_fee_discount_rate = the_member.member_class_id.room_fee_discount
            ret['member_room_fee_discount_fee'] = member_room_fee_discount_fee = new_sum_hourly_fee*(100 - member_room_fee_discount_rate)/100
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

    def process_operate(self,cr,uid,buytime_vals):
        """
        处理换房-买钟结账信息
        原包厢关闭,新包厢打开
        :param buytime_vals dict 换房-买买钟相关信息
        :param buyout_vals['room_id'] 原包厢
        :param buyout_vals['changed_room_id'] 新包厢
        """
        room_id = buytime_vals.pop("room_id")
        changed_room_id = buytime_vals['changed_room_id']

        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)

        #修改原包厢状态
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room.STATE_FREE,'current_room_operate_id' : None})
        #修改新包厢状态
        self.pool.get('ktv.room').write(cr,uid,changed_room_id,{'state' : room.STATE_BUYTIME,'current_room_operate_id' : cur_rp_id})

        buytime_vals.update({"room_operate_id" : cur_rp_id})

        room_change_buytime_id = self.create(cr,uid,buytime_vals)
        fields = self.fields_get(cr,uid).keys()
        room_change_buytime = self.read(cr,uid,room_change_buytime_id,fields)
        return (room_change_buytime,None,self._build_cron(changed_room_id,room_change_buytime))

    def _build_cron(self,changed_room_id,room_buytime_vals):
        """
        生成cron对象的值
        """
        cron_vals = {
                "name" : room_buytime_vals["room_operate_id"][1],
                "nextcall" : ktv_helper.strptime(room_buytime_vals['close_time']),
                "model" : "ktv.room",
                "function" : "write",
                #需要定时修改包厢状态,并清空包厢当前operate_id
                "args" : "(%s,{'state' : '%s','current_room_operate_id' : None})" % (changed_room_id ,room.STATE_FREE)
                }
        return cron_vals


