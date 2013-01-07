# -*- coding: utf-8 -*-
#正常开房结账信息
import logging
from osv import fields, osv
import decimal_precision as dp
import ktv_helper

_logger = logging.getLogger(__name__)

#包厢结账对象
class room_checkout(osv.osv):
    _name="ktv.room_checkout"

    _order = "bill_datetime DESC"

    def _compute_sum_fee(self,cr,uid,ids,name,args,context = None):
        """
        计算以下合计费用：
        sum_fee 合计应收金额
        sum_discount_fee 合计折扣金额
        sum_should_fee 应付金额
        change_fee 找零金额
        :return dict id => values
        """
        ret = {}
        for record in self.browse(cr,uid,ids,context):
            sum_fee = record.room_fee + record.sum_hourly_fee +  record.service_fee +  record.changed_room_sum_hourly_fee + record.changed_room_fee + record.merged_room_hourly_fee + record.guest_damage_fee
            sum_discount_fee = record.member_room_fee_discount_fee + record.discount_card_room_fee_discount_fee + record.discounter_room_fee_discount_fee
            sum_should_fee = sum_fee - sum_discount_fee
            #找零金额 = 实际付款金额 - 现金支付金额
            change_fee = record.act_pay_fee - record.cash_fee

            ret[record.id] = {
                    'sum_fee' :  sum_fee,
                    'sum_discount_fee' : sum_discount_fee,
                    'sum_should_fee' : sum_should_fee,
                    'change_fee' : change_fee,
                    }
        return ret


    _columns = {
            "room_operate_id" : fields.many2one("ktv.room_operate","room_operate_id",required = True,help="结账单所对应的room_operate对象"),
            "bill_datetime" : fields.datetime("bill_datetime",required = True,readonly = True,help="结账时间"),
            "open_time" : fields.datetime("open_time",required = True,help="开房时间"),
            "close_time" : fields.datetime("close_time",required = True,help="关房时间"),
            "guest_name" : fields.char("guest_name",size = 20,help="客人姓名"),
            "persons_count" : fields.integer("persons_count",help="客人人数"),
            "consume_minutes" : fields.integer("consume_minutes",required = True,help="消费时长"),
            "present_minutes" : fields.integer("present_minutes",help="赠送时长"),
            "presenter_id" : fields.many2one("res.users","presenter_id",help ="赠送人"),
            "saler_id" : fields.many2one("res.users","saler_id",help ="销售经理"),
            "fee_type_id" : fields.many2one("ktv.fee_type","fee_type_id",required = True,help="计费方式"),
            "room_fee" : fields.float("room_fee", digits_compute= dp.get_precision('Ktv Room Default Precision'),help="包厢费"),
            "service_fee_rate" : fields.float("service_fee_rate",digits = (15,4),help="服务费费率"),
            "service_fee" : fields.float("service_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="服务费"),
            "sum_hourly_fee" : fields.float("sum_hourly_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="合计钟点费,如果是买断时,则是买断费用,如果是买钟点时,则是买钟费用;如果是自助餐(buffet),则是自助餐费用;如果是按位计钟点,则是按位钟点费合计"),
            "changed_room_fee" : fields.float("changed_room_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="换房应补包厢费用"),
            "changed_room_sum_hourly_fee" : fields.float("changed_room_sum_hourly_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="换房应补钟点费"),
            "changed_room_service_fee" : fields.float("changed_room_service_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="换房应补服务费"),
            "changed_room_minutes" : fields.integer("changed_room_minutes",help="换房消费时长度"),
            "merged_room_hourly_fee" : fields.float("merged_room_hourly_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="并房费用"),
            #最低消费暂不使用
            "minimum_fee" : fields.float("minimum_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="低消费用"),
            "minimum_fee_diff" : fields.float("minimum_fee_diff",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="低消差额"),
            #最低消费暂不使用
            "prepay_fee" : fields.float("prepay_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="预付金额"),
            "drinks_fee" : fields.float("drinks_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="酒水费"),
            "uncheckout_drinks_fee" : fields.float("uncheckout_drinks_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="未结酒水费"),
            "minimum_drinks_fee" : fields.float("minimum_drinks_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="计入低消酒水费"),
            "guest_damage_fee" : fields.float("guest_damage_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="客损费用"),

            #会员卡折扣
            "member_card_id" : fields.many2one("ktv.member","member_card_id",help="会员信息"),
            "member_room_fee_discount_rate" : fields.float("minimum_room_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="会员-房费折扣"),
            "member_room_fee_discount_fee" : fields.float("minimum_room_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="会员-房费折扣"),
            "member_drinks_fee_discount_rate" : fields.float("minimum_drinks_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="会员-酒水费折扣"),
            "member_drinks_fee_discount_fee" : fields.float("minimum_drinks_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="会员-酒水费折扣"),

            #打折卡打折
            "discount_card_id" : fields.many2one("ktv.discount_card","discount_card_id",help="打折卡id"),
            "discount_card_room_fee_discount_rate" : fields.float("discount_card_room_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="打折卡-房费折扣"),
            "discount_card_room_fee_discount_fee" : fields.float("discount_card_room_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="打折卡-房费折扣"),
            "discount_card_drinks_fee_discount_rate" : fields.float("discount_card_drinks_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="打折卡-酒水费折扣"),
            "discount_card_drinks_fee_discount_fee" : fields.float("discount_card_drinks_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="打折卡-酒水费折扣"),

            #员工打折字段
            "discounter_id" : fields.many2one("res.users","discounter_id",help="打折人id"),
            "discounter_room_fee_discount_rate" : fields.float("discounter_room_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="操作员-房费折扣"),
            "discounter_room_fee_discount_fee" : fields.float("discounter_room_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="操作员-房费折扣"),
            "discounter_drinks_fee_discount_rate" : fields.float("discounter_drinks_fee_discount_rate",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="操作员-酒水费折扣"),
            "discounter_drinks_fee_discount_fee" : fields.float("discounter_drinks_fee_discount_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="-酒水费折扣"),

            #各种付款方式
            #现金
            "cash_fee" : fields.float("cash_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="现金支付金额"),
            #会员卡/储值卡
            "member_card_fee" : fields.float("member_card_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="会员卡支付金额"),
            #信用卡&储蓄卡
            "credit_card_no" : fields.char("credit_card_no",size = 64,help="信用卡号"),
            "credit_card_fee" : fields.float("credit_card_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="信用卡支付金额"),
            #抵用券
            "sales_voucher_fee" : fields.float("sales_voucher_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="抵用券支付金额"),
            #免单
            "freer_id" : fields.many2one("res.users","freer_id",help="免单人"),
            "free_fee" : fields.float("free_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="免单费用"),
            #按位消费免单
            "freer_persons_id"  : fields.many2one("res.users","freer_persons_id",help="免单人"),
            "free_persons_count" : fields.integer("free_persons_count",help="按位消费免单人数"),
            #挂账
            "on_crediter_id" : fields.many2one("res.users","on_crediter_id",help="挂账人"),
            "on_credit_fee" : fields.float("on_credit_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="免单费用"),
            #欢唱券
            "song_ticket_fee" : fields.float("song_ticket_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="欢唱券抵扣费用"),
            "song_ticket_fee_diff" : fields.float("song_ticket_fee_diff",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="欢唱券抵扣费用差额"),

            "act_pay_fee" : fields.float("act_pay_fee",digits_compute = dp.get_precision('Ktv Room Default Precision'),help="付款金额"),
            #以下为计算字段
            "sum_fee" : fields.function(_compute_sum_fee,multi="sum_fee",string="合计应收房费,打折之前的费用",digits_compute = dp.get_precision('Ktv Room Default Precision')),
            "sum_discount_fee" : fields.function(_compute_sum_fee,multi = "sum_fee",string="合计折扣费用",digits_compute = dp.get_precision('Ktv Room Default Precision')),
            "sum_should_fee" : fields.function(_compute_sum_fee,multi = "sum_fee",string="合计应付费用(折后费用)",digits_compute = dp.get_precision('Ktv Room Default Precision')),
            "change_fee" : fields.function(_compute_sum_fee,multi="sum_fee",string="找零金额",digits_compute = dp.get_precision('Ktv Room Default Precision')),
            }

    _defaults = {
            #正常开房时,关房时间是当前时间
            "bill_datetime" : fields.datetime.now,
            "open_time" : fields.datetime.now,
            "close_time" : fields.datetime.now,
            "consume_minutes" : 0,
            "present_minutes" : 0,
            "room_fee" : 0,
            "service_fee_rate" : 0,
            "service_fee" : 0,
            "sum_hourly_fee" : 0,
            "changed_room_fee" : 0,
            "changed_room_sum_hourly_fee" : 0,
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


    def process_operate(self,cr,uid,room_checkout_vals):
        '''
        自客户端传入的数据创建包厢结账单据
        '''
        room_id = room_checkout_vals.pop("room_id")
        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)
        room_checkout_vals.update({"room_operate_id" : cur_rp_id})
        id = self.create(cr,uid,room_checkout_vals)
        room_checkout_vals['id'] = id
        return room_checkout_vals
