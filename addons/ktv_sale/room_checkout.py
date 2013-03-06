# -*- coding: utf-8 -*-
#正常开房结账信息
import types
import logging
from datetime import *
from osv import fields, osv
import decimal_precision as dp
import ktv_helper
from room import room

_logger = logging.getLogger(__name__)

class room_checkout(osv.osv):
    """
    包厢结账-正常开房
    """
    _name="ktv.room_checkout"

    _order = "bill_datetime DESC"

    def _compute_consume_minutes(self,cr,uid,ids,name,args,context = None):
        """
        计算消费时长
        """
        ret = {}
        for record in self.browse(cr,uid,ids):
            #close_time可能为空,当时尚未关闭
            close_time = record.close_time if record.close_time else ktv_helper.utc_now_str()
            consume_minutes = ktv_helper.str_timedelta_minutes(record.open_time,close_time)
            ret[record.id]=consume_minutes
        return ret

    def _compute_total_fee(self,cr,uid,ids,name,args,context = None):
        """
        计算以下合计费用：
        total_fee 合计应收金额
        total_discount_fee 合计折扣金额
        total_after_discount_fee 折后应付金额
        total_after_discount_cash_fee 折后应付现金
        cash_change 找零金额
        :return dict id => values
        """
        ret = {}
        for record in self.browse(cr,uid,ids,context):
            total_fee = record.room_fee + record.hourly_fee +  record.service_fee +  record.changed_room_fee + record.changed_room_hourly_fee + record.guest_damage_fee
            total_discount_fee = record.member_room_fee_discount_fee + record.discount_card_room_fee_discount_fee + record.discounter_room_fee_discount_fee
            total_after_discount_fee = total_fee - total_discount_fee - record.prepay_fee
            #折后现金付款金额
            total_after_discount_cash_fee = total_after_discount_fee -  record.member_card_fee - record.credit_card_fee - record.sales_voucher_fee - record.free_fee
            #找零金额 = 实际付款金额 - 现金支付金额
            cash_change = record.act_pay_cash_fee - total_after_discount_cash_fee

            ret[record.id] = {
                    'total_fee' :  total_fee,
                    'total_discount_fee' : total_discount_fee,
                    'total_after_discount_fee' : total_after_discount_fee,
                    'total_after_discount_cash_fee' : total_after_discount_cash_fee,
                    'cash_change' : cash_change,
                    }
        return ret


    _columns = {
            "room_operate_id" : fields.many2one("ktv.room_operate","room_operate_id",required = True,help="结账单所对应的room_operate对象"),
            "room_id" : fields.many2one("ktv.room","room_id",required = True,help="结账单所对应的kt.room对象"),
            "presenter_id" : fields.many2one("res.users","presenter_id",help ="赠送人"),
            "saler_id" : fields.many2one("res.users","saler_id",help ="销售经理"),

            "bill_datetime" : fields.datetime("bill_datetime",required = True,readonly = True,help="结账时间"),
            "price_class_id" : fields.many2one("ktv.price_class","price_class_id",help="价格类型(买断方式下不适用)"),
            "fee_type_id" : fields.many2one("ktv.fee_type","fee_type_id",required = True,help="计费方式"),
            "guest_name" : fields.char("guest_name",size = 20,help="客人姓名"),
            "persons_count" : fields.integer("persons_count",help="客人人数"),
            "open_time" : fields.datetime("open_time",required = True,help="开房时间"),
            "close_time" : fields.datetime("close_time",required = True,help="关房时间"),

            #以下为包厢费用相关字段
            "prepay_fee" : fields.float("prepay_fee",digits_compute = dp.get_precision('ktv_fee'),help="预付金额"),
            "room_fee" : fields.float("room_fee", digits_compute= dp.get_precision('ktv_fee'),help="包厢费"),
            "hourly_fee" : fields.float("hourly_fee",digits_compute = dp.get_precision('ktv_fee'),help="合计钟点费,如果是买断时,则是买断费用,如果是买钟点时,则是买钟费用;如果是自助餐(buffet),则是自助餐费用;如果是按位计钟点,则是按位钟点费合计"),
            #"consume_minutes" : fields.integer('consume_minutes',help="消费时长"),
            "consume_minutes" : fields.function(_compute_consume_minutes,string="消费时长",type='integer'),
            "present_minutes" : fields.integer("present_minutes",help="赠送时长"),

            #换房费用字段
            "changed_room_fee" : fields.float("changed_room_fee",digits_compute = dp.get_precision('ktv_fee'),help="换房应补包厢费用"),
            "changed_room_hourly_fee" : fields.float("changed_room_hourly_fee",digits_compute = dp.get_precision('ktv_fee'),help="换房应补钟点费"),
            "changed_room_minutes" : fields.integer("changed_room_minutes",help="换房消费时长"),

            "guest_damage_fee" : fields.float("guest_damage_fee",digits_compute = dp.get_precision('ktv_fee'),help="客损费用"),

            #FIXME 暂不使用 服务费
            "service_fee_rate" : fields.float("service_fee_rate",digits = (15,4),help="服务费费率"),
            "service_fee" : fields.float("service_fee",digits_compute = dp.get_precision('ktv_fee'),help="服务费"),

            #FIXME 最低消费暂不使用
            "minimum_fee" : fields.float("minimum_fee",digits_compute = dp.get_precision('ktv_fee'),help="低消费用"),
            "minimum_fee_diff" : fields.float("minimum_fee_diff",digits_compute = dp.get_precision('ktv_fee'),help="低消差额"),
            "drinks_fee" : fields.float("drinks_fee",digits_compute = dp.get_precision('ktv_fee'),help="酒水费"),
            "uncheckout_drinks_fee" : fields.float("uncheckout_drinks_fee",digits_compute = dp.get_precision('ktv_fee'),help="未结酒水费"),
            "minimum_drinks_fee" : fields.float("minimum_drinks_fee",digits_compute = dp.get_precision('ktv_fee'),help="计入低消酒水费"),

            #会员卡折扣
            "member_id" : fields.many2one("ktv.member","member_id",help="会员信息"),
            "member_room_fee_discount_rate" : fields.float("minimum_room_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="会员-房费折扣"),
            "member_room_fee_discount_fee" : fields.float("minimum_room_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="会员-房费折扣"),
            "member_drinks_fee_discount_rate" : fields.float("minimum_drinks_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="会员-酒水费折扣"),
            "member_drinks_fee_discount_fee" : fields.float("minimum_drinks_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="会员-酒水费折扣"),

            #打折卡打折
            "discount_card_id" : fields.many2one("ktv.discount_card","discount_card_id",help="打折卡id"),
            "discount_card_room_fee_discount_rate" : fields.float("discount_card_room_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="打折卡-房费折扣"),
            "discount_card_room_fee_discount_fee" : fields.float("discount_card_room_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="打折卡-房费折扣"),
            "discount_card_drinks_fee_discount_rate" : fields.float("discount_card_drinks_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="打折卡-酒水费折扣"),
            "discount_card_drinks_fee_discount_fee" : fields.float("discount_card_drinks_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="打折卡-酒水费折扣"),

            #员工打折字段
            "discounter_id" : fields.many2one("res.users","discounter_id",help="打折人id"),
            "discounter_room_fee_discount_rate" : fields.float("discounter_room_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="操作员-房费折扣"),
            "discounter_room_fee_discount_fee" : fields.float("discounter_room_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="操作员-房费折扣"),
            "discounter_drinks_fee_discount_rate" : fields.float("discounter_drinks_fee_discount_rate",digits_compute = dp.get_precision('ktv_fee'),help="操作员-酒水费折扣"),
            "discounter_drinks_fee_discount_fee" : fields.float("discounter_drinks_fee_discount_fee",digits_compute = dp.get_precision('ktv_fee'),help="-酒水费折扣"),

            #各种付款方式
            #会员卡/储值卡
            "member_card_fee" : fields.float("member_card_fee",digits_compute = dp.get_precision('ktv_fee'),help="会员卡支付金额"),
            #信用卡&储蓄卡
            "credit_card_no" : fields.char("credit_card_no",size = 64,help="信用卡号"),
            "credit_card_fee" : fields.float("credit_card_fee",digits_compute = dp.get_precision('ktv_fee'),help="信用卡支付金额"),
            #抵用券
            "sales_voucher_fee" : fields.float("sales_voucher_fee",digits_compute = dp.get_precision('ktv_fee'),help="抵用券支付金额"),
            #免单
            "freer_id" : fields.many2one("res.users","freer_id",help="免单人"),
            "free_fee" : fields.float("free_fee",digits_compute = dp.get_precision('ktv_fee'),help="免单费用"),
            #按位消费免单
            "freer_persons_id"  : fields.many2one("res.users","freer_persons_id",help="免单人"),
            "free_persons_count" : fields.integer("free_persons_count",help="按位消费免单人数"),
            #挂账
            "on_crediter_id" : fields.many2one("res.users","on_crediter_id",help="挂账人"),
            "on_credit_fee" : fields.float("on_credit_fee",digits_compute = dp.get_precision('ktv_fee'),help="免单费用"),

            #欢唱券
            "song_ticket_minutes" : fields.integer("song_ticket_minutes",help="欢唱券抵扣消费时间"),

            "act_pay_cash_fee" : fields.float("act_pay_cash_fee",digits_compute = dp.get_precision('ktv_fee'),help="实际现金付款金额"),

            #以下为计算字段
            "total_fee" : fields.function(_compute_total_fee,multi="total_fee",string="合计应收房费,打折之前的费用",digits_compute = dp.get_precision('ktv_fee')),
            "total_discount_fee" : fields.function(_compute_total_fee,multi = "total_fee",string="合计折扣费用",digits_compute = dp.get_precision('ktv_fee')),
            "total_after_discount_fee" : fields.function(_compute_total_fee,multi = "total_fee",string="合计应付费用(折后费用)",digits_compute = dp.get_precision('ktv_fee')),
            "total_after_discount_cash_fee" : fields.function(_compute_total_fee,multi="total_fee",string="合计应收现金房费(折后费用)",digits_compute = dp.get_precision('ktv_fee')),
            "cash_change" : fields.function(_compute_total_fee,multi="total_fee",string="现金找零",digits_compute = dp.get_precision('ktv_fee')),
            }

    _defaults = {
            #正常开房时,关房时间是当前时间
            "bill_datetime" : fields.datetime.now,
            "persons_count" : 0,
            "prepay_fee" : 0,
            "room_fee" : 0,
            "hourly_fee" : 0,
            "consume_minutes" : 0,
            "present_minutes" : 0,

            "changed_room_fee" : 0,
            "changed_room_hourly_fee" : 0,
            "changed_room_minutes" : 0,

            "guest_damage_fee" : 0,

            "service_fee_rate" : 0,
            "service_fee" : 0,
            "minimum_fee" : 0,
            "minimum_fee_diff" : 0,
            "drinks_fee" : 0,
            "uncheckout_drinks_fee" : 0,
            "minimum_drinks_fee" : 0,

            "member_room_fee_discount_rate" : 0,
            "member_room_fee_discount_fee" : 0,
            "discount_card_room_fee_discount_rate" : 0,
            "discount_card_room_fee_discount_fee" : 0,
            "discounter_room_fee_discount_rate" : 0,
            "discounter_room_fee_discount_fee" : 0,

            "member_card_fee" : 0,
            "credit_card_fee" : 0,
            "sales_voucher_fee" : 0,
            "free_fee" : 0,
            "free_persons_count" : 0,
            "on_credit_fee" : 0,
            "song_ticket_minutes" : 0,

            "act_pay_cash_fee" : 0,
            "total_fee" : 0,
            "total_discount_fee" : 0,
            "total_after_discount_fee" : 0,
            "total_after_discount_cash_fee" : 0,
            "cash_change" : 0,
            }
    def set_discount_info(self,cr,uid,total_fee,member_id=None,discount_card_id=None,discounter_id=None):
        """
        计算并设置折扣信息
        根据传入的数据计算打折费用
        优先级 discounter_id > member_id > discount_card_id
        :param total_fee float 总费用
        :param member_id integer 会员id
        :param discount_card_id integer 打折卡id
        :param discounter_id integer 打折人(员工id)
        :rtype dict

        """
        discount_rate = total_discount_fee = 0.0
        ret = {}
        if discount_card_id:
            discount_card = self.pool.get('ktv.discount_card').browse(cr,uid,discount_card_id)
            ret['discount_card_id'] = discount_card_id
            discount_rate = ret['discount_card_room_fee_discount_rate'] = discount_card.discount_card_type_id.room_fee_discount
            total_discount_fee = ret['discount_card_room_fee_discount_fee'] = ktv_helper.float_round(cr,total_fee*(100 - discount_rate)/100)

        if member_id:
            the_member = self.pool.get('ktv.member').browse(cr,uid,member_id)
            ret['member_id'] = member_id
            discount_rate = ret['member_room_fee_discount_rate'] = the_member.member_class_id.room_fee_discount
            total_discount_fee = ret['member_room_fee_discount_fee'] = ktv_helper.float_round(cr,total_fee*(100.0 - discount_rate)/100.0)

        #员工打折
        #TODO
        #if 'discounter_id' in context and context['discounter_id']:
        ret['discount_rate'] = discount_rate
        ret['total_discount_fee']  = total_discount_fee
        return ret

    def re_calculate_fee(self,cr,uid,context):
        '''
        计算正常开房-结账费用信息
        :params context 包含计算上下文信息,required
        :param context['room_id'] integer required 结账包厢id
        :params context[fee_type_id] integer 计费方式id required
        :params context[price_class_id] integer 价格类型 required
        :params context[member_id] integer 会员卡id
        :params context[discount_card_id] integer 打折卡id
        :params context[discounter_id] integer 员工id,用于记录打折员工信息
        :return 计算费用后的结账对象 dict
        计算步骤:
        1 计算正常开房及关房(room_opens),计算费用
        2 计算换房数据(可能会存在多次换房信息)(room_chnage),计算换房费用
        3 计算折扣费用
        4 根据付款方式,价格类型计算实际应付费用
        5 返回计算结果,类型为dict
        '''

        _logger.info(context)

        #获取当前包厢费用信息
        room_id = context.pop('room_id')
        room = self.pool.get('ktv.room').browse(cr,uid,room_id)

        cur_operate_id = room.current_room_operate_id

        ret = {
                "room_id" : room_id,
                "fee_type_id" : context['fee_type_id'],
                "price_class_id" : context['price_class_id'],
                "open_time" : None,
                "close_time" : ktv_helper.utc_now_str(),
                "persons_count" : 0,
                "consume_minutes" : 0,
                "present_minutes" : 0,
                "room_fee" : 0,
                "changed_room_fee" : 0,
                "sum_hourly_fee" : 0,
                "sum_hourly_fee_p" : 0,
                "changed_room_hourly_fee" : 0,
                "changed_room_minutes" : 0,
                "merged_room_hourly_fee" : 0,
                "minimum_fee" : 0,
                "minimum_fee_diff" : 0,
                "service_fee_rate" : 0,
                "service_fee" : 0,
                "discount_rate" : 0,
                "discount_fee" : 0,
                }

        member = None
        if "member_id" in context and context['member_id']:
            member = self.pool.get('ktv.member').browse(context['member_id'])

        #计算room_opens应付费用合计
        (room_opens_sum_hourly_fee,room_opens_consume_minutes,room_opens_sum_hourly_fee_p,room_open_consume_minutes_p) = (0,0,0,0)
        #FIXME 一个room_operate应该只有一个room_opens
        room_opens = cur_operate_id.room_opens_ids and cur_operate_id.room_opens_ids[0]
        if room_opens:
            #原包厢
            origin_room = cur_operate_id.room_id
            ret['open_time'] = room_opens.open_time
            ret['persons_count'] = room_opens.persons_count
            #包厢费
            ret['room_fee'] = origin_room.room_fee
            #服务费率
            ret['service_fee_rate'] = origin_room.service_fee_rate
            #钟点费
            cal_hourly_fee_ctx = {
                    'datetime_open' : room_opens.open_time,
                    'datetime_close' : room_opens.close_time if room_opens.close_time else ktv_helper.utc_now_str(),
                    'price_class_id' : context['price_class_id'],
                    'persons_count' : room_opens.persons_count,
                    }
            if member:
                cal_hourly_fee_ctx['member_class_id'] = member.member_class_id.id

            #钟点费合计
            (room_opens_consume_minutes,room_opens_sum_hourly_fee) = self._get_sum_hourly_fee(cr,uid,origin_room.id,cal_hourly_fee_ctx)
            #按位钟点费合计
            cal_hourly_fee_ctx['is_hourly_fee_p'] = True
            (room_opens_consume_minutes_p,room_opens_sum_hourly_fee_p) = self._get_sum_hourly_fee(cr,uid,origin_room.id,cal_hourly_fee_ctx)
            ret['sum_hourly_fee'] = room_opens_sum_hourly_fee
            ret['consume_minutes'] = room_opens_consume_minutes
            ret['sum_hourly_fee_p'] = room_opens_sum_hourly_fee_p
            ret['consume_minutes_p'] = room_opens_consume_minutes_p

        #计算room_change应付费用合计

        (room_change_sum_hourly_fee,room_change_sum_hourly_fee_p,room_change_minutes,room_change_minutes_p) = (0,0,0,0)
        for room_change in cur_operate_id.room_change_ids:
            changed_room = room_change.changed_room_id
            cal_room_change_hourly_fee_ctx = {
                    'datetime_open' : room_change.open_time,
                    'datetime_close' : room_opens.close_time if room_opens.close_time else ktv_helper.utc_now_str(),
                    'price_class_id' : context['price_class_id'],
                    'persons_count' : room_opens.persons_count,
                    }

            if member:
                cal_room_change_hourly_fee_ctx['member_class_id'] = member.member_class_id.id

            #钟点费合计
            (m,h) =  self._get_sum_hourly_fee(cr,uid,changed_room.id,cal_room_change_hourly_fee_ctx)
            room_change_sum_hourly_fee += h;room_change_minutes += m
            #按位钟点费合计
            cal_room_change_hourly_fee_ctx['is_hourly_fee_p'] = True
            (m,h) =  self._get_sum_hourly_fee(cr,uid,changed_room.id,cal_room_change_hourly_fee_ctx)
            room_change_minutes_p += m;room_change_sum_hourly_fee_p += h

            #服务费
            ret['service_fee_rate'] = changed_room.service_fee_rate
            #计算应补包厢费
            ret['changed_room_fee'] = 0
            #默认以费用高的包厢费为准
            if changed_room.room_fee > ret['room_fee']:
                ret['room_fee'] = changed_room.room_fee

        ret['changed_room_sum_hourly_fee'] = room_change_sum_hourly_fee
        ret['changed_room_minutes'] = room_change_minutes
        ret['changed_room_sum_hourly_fee_p'] = room_change_sum_hourly_fee_p
        ret['changed_room_minutes_p'] = room_change_minutes_p

        #默认无折扣
        discount_rate = 0;discount_fee = 0

        #原钟点费合计
        sum_origin_hourly_fee = room_opens_sum_hourly_fee + room_change_sum_hourly_fee
        sum_origin_hourly_fee_p = room_opens_sum_hourly_fee_p + room_change_sum_hourly_fee_p

        #打折卡折扣
        discount_card = None
        if 'discount_card_id' in context and context['discount_card_id']:
            discount_card = self.pool.get('ktv.discount_card').browse(cr,uid,context['discount_card_id'])
            discount_card_id = context['discount_card_id']
            discount_card_room_fee_discount_rate = discount_card.discount_card_type_id.room_fee_discount
            discount_card_room_fee_discount_fee = sum_origin_hourly_fee*(100 - discount_card_room_fee_discount_rate)/100
            discount_rate = discount_card_room_fee_discount_rate
            discount_fee = discount_card_room_fee_discount_fee

            ret.update({
                "discount_card_id" : discount_card.id,
                "discount_card_room_fee_discount_rate" : discount_card_room_fee_discount_rate,
                "discount_card_room_fee_discount_fee" : discount_card_room_fee_discount_fee,
                })



        #计算会员折扣信息
        #FIXME 此处需要处理会员折扣的问题：
        #存在这样的情况：当前已存在会员钟点折扣设置,此时会员卡又有房费折扣设置,此时取哪一种折扣设置
        #逻辑判断:如果当前是会员时段,则总房费不再折扣,否则按照总房费对会员消费折扣

        if member:
            member_room_fee_discount_rate = member.member_class_id.room_fee_discount
            member_room_fee_discount_fee = sum_origin_hourly_fee*(100 - member.member_class_id.room_fee_discount) /100
            discount_rate = member_room_fee_discount_rate
            discount_fee = member_room_fee_discount_fee
            ret.update({
                "member_id" : member.id,
                "member_room_fee_discount_rate" : member_room_fee_discount_rate,
                "member_room_fee_discount_fee" : member_room_fee_discount_fee,
                })

        ret.update({
                "merged_room_hourly_fee" : 0,
                "minimum_fee" : 0,
                "minimum_fee_diff" : 0,
                "service_fee_rate" : room.service_fee_rate,
                "discount_rate" : discount_rate,
                "discount_fee" : discount_fee,
                })

        #根据计费方式计算费用信息
        fee_type = self.pool.get('ktv.fee_type').browse(cr,uid,context['fee_type_id'])

        _logger.debug("return result = %s,",ret)
        _logger.debug("fee_type = %s,: %s",fee_type.fee_type_code,fee_type.name)
        #只收包厢费
        if fee_type.fee_type_code == fee_type.FEE_TYPE_ONLY_ROOM_FEE:
            ret.update({
                "service_fee_rate" : 0,
                "service_fee" : 0,
                "sum_hourly_fee" : 0,
                "sum_hourly_fee_p" : 0,
                "changed_room_sum_hourly_fee" : 0,
                "changed_room_sum_hourly_fee_p" : 0,
                })

        #只收钟点费
        elif fee_type.fee_type_code == fee_type.FEE_TYPE_ONLY_HOURLY_FEE:
            ret.update({
                "room_fee" : 0,
                "changed_room_fee" : 0,
                "sum_hourly_fee_p" : 0,
                })

        #包厢费加钟点费
        elif fee_type.fee_type_code == fee_type.FEE_TYPE_ROOM_FEE_PLUS_HOURLY_FEE:
            ret.update({"sum_hourly_fee_p" : 0 })
       #按位钟点费
        elif fee_type.fee_type_code == fee_type.FEE_TYPE_HOURLY_FEE_P:
            ret.update({"room_fee" : 0,'changed_room_fee' : 0,"sum_hourly_fee" : 0})
        else:
            #NOTE 其他计费方式不适用
            pass
        #计算其他费用
        #服务费
        ret['service_fee'] = (ret['room_fee'] + ret['changed_room_fee'] + ret['sum_hourly_fee'] + ret['sum_hourly_fee_p'])*ret['service_fee_rate']
        ret['sum_fee'] = ret['room_fee'] + ret['changed_room_fee'] + ret['sum_hourly_fee'] + ret['sum_hourly_fee_p'] + ret['service_fee']
        ret['sum_should_fee'] = ret['sum_fee'] - ret['discount_fee']
        ret['cash_fee'] = ret['sum_should_fee']
        ret['act_pay_fee'] = ret['cash_fee']
        ret['change_fee'] = 0.0
        ret.update({
            'member_card_fee' : 0.0,
            'credit_card_fee' : 0.0,
            'sales_voucher_fee' : 0.0,
            })

        return ret

    def process_operate(self,cr,uid,room_checkout_vals):
        '''
        自客户端传入的数据创建包厢结账单据
        '''
        room_id = room_checkout_vals.pop("room_id")
        cur_rp_id = self.pool.get('ktv.room').find_or_create_room_operate(cr,uid,room_id)
        room_checkout_vals.update({"room_operate_id" : cur_rp_id})
        id = self.create(cr,uid,room_checkout_vals)
        room_checkout_vals['id'] = id
        fields = self.fields_get(cr,uid).keys()
        room_checkout = self.read(cr,uid,id,fields)
        return (room_checkout,room.STATE_FREE,None)

    def get_default_checkout_dict(self,cr,uid):
        """
        获取默认的checkout dict,在计算中经常会使用到
        所有字段被设置为默认值
        """
        fields = self.fields_get(cr,uid).keys()
        defs = self.default_get(cr,uid,fields)
        ret = {f_name : (defs[f_name] if f_name in defs else None) for f_name in fields}
        return ret

    def set_calculate_fields(self,cr,fields_dict):
        fields_dict['total_after_discount_fee'] = fields_dict['total_fee'] - fields_dict['total_discount_fee']
        fields_dict['total_after_discount_cash_fee']= fields_dict['total_after_discount_fee'] -  fields_dict['member_card_fee'] - fields_dict['credit_card_fee'] - fields_dict['sales_voucher_fee'] - fields_dict['free_fee']
        fields_dict['act_pay_cash_fee'] = fields_dict['total_after_discount_cash_fee']
        fields_dict['cash_change'] = 0.0
        return fields_dict

    def _get_sum_hourly_fee(self,cr,uid,room_id,context):
        """
        给定一个消费时间段,根据hourly_fee_discount及member_hourly_fee_discount中的设置计算分段钟点费用
        :param room_id integer 包厢id
        :param context dict required
        :param context[is_hourly_fee_p] boolean  是否是计算按位钟点费 required
        :param context[datetime_open] datetime 包厢消费起始时间 required
        :param context[datetime_close] datetime 包厢消费结束时间 required
        :param context[price_class_id] integer 价格类型id required
        :param context[member_id] integer 会员卡id
        :param context[persons_count] integer 消费人数
        :return decimal 各个时段的钟点费合计
        """
        room = self.pool.get('ktv.room').browse(cr,uid,room_id)
        datetime_open = ktv_helper.strptime(context['datetime_open'])
        datetime_close = ktv_helper.strptime(context['datetime_close'])
        price_class_id = context['price_class_id']
        member_class_id = 'member_class_id' in context and context['member_class_id']
        #计算最低消费人数
        persons_count = 'persons_count' in context and context['persons_count'] or 1
        if persons_count < room.minimum_persons:
            persons_count = room.minimum_persons
        room_type_id = room.room_type_id.id

        domain = {'price_class_id' : price_class_id,'ignore_time_range' : True}
        if member_class_id:
            domain['member_class_id'] = member_class_id
        #hourly_fee_configs 包厢时段设置
        hourly_fee_discount_configs = []
        #member_hourly_fee_config 会员包厢时段设置
        if member_class_id:
            domain['which_fee']="member_hourly_fee_discount"
            hourly_discount_configs = self.pool.get('ktv.member_hourly_fee_discount').get_active_conifg(cr,uid,room_type_id,domain)

        #判断是否计算按位钟点费
        is_hourly_fee_p = 'is_hourly_fee_p' in context and context['is_hourly_fee_p']
        if is_hourly_fee_p:
            hourly_discount_configs = self.pool.get("ktv.hourly_fee_p_discount").get_active_configs(cr,uid,room_type_id,domain)
        #否则取hourly_fee_discount设置
        elif not hourly_fee_discount_configs:
            hourly_discount_configs = self.pool.get('ktv.hourly_fee_discount').get_active_configs(cr,uid,room_type_id,domain)

        #合计钟点费及消费分钟数
        sum_hourly_fee = 0
        sum_consume_minutes = 0
        #形成config_array数组
        def construct_config_array():
            ret_array =[]
            for c in hourly_discount_configs:
                config_datetime_from = ktv_helper.float_time_to_datetime(c['time_from'])
                config_datetime_to = ktv_helper.float_time_to_datetime(c['time_to'])
                #如果config_datetime_to < config_datetime_from,则config_datetime_to + 1 day
                if config_datetime_to < config_datetime_from:
                    config_datetime_to = config_datetime_to + timedelta(days = 1)

                #先形成时间顺序的数组
                #FIXME 此处要求在设置时间时,必须是连续的
                ret_array.append({
                    'datetime_from' : config_datetime_from,
                    'datetime_to' : config_datetime_to,
                    'hourly_fee' : c['hourly_fee'],
                    'hourly_discount' : c['hourly_discount'],
                    })
            return ret_array

        config_array =  construct_config_array()

        #根据获取到的设置进行分段费用计算
        for c in hourly_discount_configs:
            config_datetime_from = ktv_helper.float_time_to_datetime(c['time_from'])
            config_datetime_to = ktv_helper.float_time_to_datetime(c['time_to'])
            #如果config_datetime_to < config_datetime_from,则config_datetime_to + 1 day
            if config_datetime_to < config_datetime_from:
                config_datetime_to = config_datetime_to + timedelta(days = 1)

            #判断时间情况如下所列,共有6种情况
            #         |--1--|-2--|--3--|--4-|
            # |----|
            #                                  |----|
            #             |---------------|
            #      |----------------------------|
            #      |----------|
            #                             |---------|


            #设置的最早时段
            config_datetime_min = config_array[0]['datetime_from']
            config_datetime_max = config_array[-1]['datetime_to']

            #情况1:消费时间不在设置时间区间内,按照正常费用设置
            if datetime_close <= config_datetime_min or datetime_open >= config_datetime_max:
                config_array = []
                config_array.append({
                    "datetime_from" : datetime_open,
                    "datetime_to" : datetime_close,
                    "hourly_fee" : room.hourly_fee_p if is_hourly_fee_p else room.hourly_fee,
                    "hourly_discount" : 100,
                    })

            #情况2: 消费时段包含在设置时段内
            #更新第一个的datetime_from 更新最后一个的datetime_to
            if datetime_open >= config_datetime_min and datetime_close <= config_datetime_max:
                #删除不在消费时段内的元素
                [config_array.remove(c_fee) for c_fee in config_array if c_fee['datetime_to'] <= datetime_open]
                [config_array.remove(c_fee) for c_fee in config_array if c_fee['datetime_from'] >= datetime_close]
                config_array[0]['datetime_from'] = datetime_open
                config_array[-1]['datetime_to'] = datetime_close

            #3:消费时段包含设置时段
            #在首尾分别添加费用设置
            if datetime_open < config_datetime_min and datetime_close > config_datetime_max:
                config_array.insert(0,{
                    "datetime_from" : datetime_open,
                    "datetime_to" : config_datetime_min,
                    "hourly_fee" : room.hourly_fee_p if is_hourly_fee_p else room.hourly_fee,
                    "hourly_discount" : 100,
                    })
                config_array.append({
                    "datetime_from" : datetime_max,
                    "datetime_to" : config_datetime_close,
                    "hourly_fee" : room.hourly_fee_p if is_hourly_fee_p else room.hourly_fee,
                    "hourly_discount" : 100,
                    })

                #4:消费起始时间早于设置开始时间,消费结束时间早于设置结束时间
                #在数组头部添加费用设置,删除后部的元素
            if datetime_open < config_datetime_min and datetime_close < config_datetime_max:
                #删除不在消费时段内的元素
                [config_array.remove(c_fee) for c_fee in config_array if c_fee['datetime_from'] >= datetime_close]
                config_array.insert(0,{
                    "datetime_from" : datetime_open,
                    "datetime_to" : config_datetime_min,
                    "hourly_fee" : room.hourly_fee_p if is_hourly_fee_p else room.hourly_fee,
                    "hourly_discount" : 100,
                    })
                config_array[-1]['datetime_to'] = datetime_close


                #5:消费起始时间晚于设置开始时间,消费结束时间晚于设置结束时间
                #删除数组头部不符合要求的数据,在数组尾部添加费用设置
            if datetime_open >= config_datetime_min and datetime_close >= config_datetime_max:
                #删除不在消费时段内的元素
                [config_array.remove(c_fee) for c_fee in config_array if c_fee['datetime_to'] <= datetime_open]
                config_array.append({
                    "datetime_from" : config_datetime_max,
                    "datetime_to" : datetime_close,
                    "hourly_fee" : room.hourly_fee_p if is_hourly_fee_p else room.hourly_fee,
                    "hourly_discount" : 100,
                    })
                config_array[0]['datetime_from'] = datetime_open


        #逐个计算费用信息
        for c in config_array:
            consume_minutes= ktv_helper.timedelta_minutes(c["datetime_from"],c["datetime_to"])
            c['sum_hourly_fee']= c['hourly_fee']*consume_minutes/60 if not is_hourly_fee_p else  c['hourly_fee']*consume_minutes/60*persons_count
            c['consume_minutes']= consume_minutes
            #以下计算合计费用
            sum_hourly_fee += c['sum_hourly_fee']
            sum_consume_minutes += c['consume_minutes']

        #如果没有钟点费用信息,则设置默认钟点费信息
        if not config_array:
            sum_consume_minutes = ktv_helper.timedelta_minutes(datetime_open,datetime_close)

            sum_hourly_fee = room.hourly_fee_p*sum_consume_minutes/60*persons_count if is_hourly_fee_p else room.hourly_fee*sum_consume_minutes/60

        _logger.debug("sum_consume_minutes = %d;sum_hourly_fee = %d",sum_consume_minutes,sum_hourly_fee)

        return (sum_consume_minutes,ktv_helper.float_round(cr,sum_hourly_fee))
