# -*- coding: utf-8 -*-

import logging
from osv import osv,fields
from room import room
import decimal_precision as dp

_logger = logging.getLogger(__name__)
class room_operate(osv.osv):
    '''
    包厢操作类:
    以下操作都属于包厢操作：
    1 预定
    2 正常开房
    3 买钟
    4 买断
    5 续钟
    6 退钟
    7 换房
    8 并房
    包厢通过cur_room_operate_id与room_operate相关联,用于标示当前包厢所对应的操作
    room_operate与以上各个操作是one2many的关系,这样通过一个room_operate可以获取所有包厢在开房过程中所进行的操作,结账时遍历所有的操作并进行计算即可
    '''
    _name = "ktv.room_operate"
    #由于在其他地方需要引用该对象,所有将name定义为bill_no
    _rec_name = "bill_no"

    _description = "包厢操作类,与包厢是many2one的关系"

    def _compute_fields(self,cr,uid,ids,name,args,context = None):
        """
        计算以下字段的值:
        open_time 以room_opens或room_checkout_buytime或room_checkout_buytime中的open_time为准
        close_time 以最后一次结算时间为准
        consume_minutes
        changed_room_minutes
        """
        ret = {}
        for record in self.browse(cr,uid,ids,context):
            #依次判断所有开房相关操作:room_opens > room_checkout_buyout > room_checkout_buytime
            which_room_open_ops = record.room_opens_ids or record.room_checkout_buyout_ids or record.room_checkout_buytime_ids

            fee_type_id = which_room_open_ops[0].fee_type_id.id
            price_class_id = getattr(which_room_open_ops[0].price_class_id,'id',None)
            open_time = which_room_open_ops[0].open_time
            guest_name = which_room_open_ops[0].guest_name
            persons_count = which_room_open_ops[0].persons_count
            prepay_fee = which_room_open_ops[0].prepay_fee

            #依次判断关房操作,也有可能当前包厢尚未关闭,close_time可能为空
            #room_change > room_checkout > room_change_checkout_buytime > room_change_checkout_buyout > room_checkout_buytime
            #TODO 还需要加上 续钟与退钟操作
            which_room_close_ops = record.room_checkout_ids or record.room_change_ids or record.room_change_checkout_buyout_ids or record.room_checkout_buyout_ids or record.room_change_checkout_buytime_ids or record.room_checkout_buytime_ids
            close_time = None
            last_member = None
            last_buyout_config = None
            if which_room_close_ops:
                close_time = which_room_close_ops[-1].close_time
                #获取最后一次操作的member_id
                last_member =getattr(which_room_close_ops[-1],'member_id',None)
                last_buyout_config = getattr(which_room_close_ops[-1],'buyout_config_id',None)

            if not last_buyout_config:
                #最后买断id
                last_buyout_config = getattr(which_room_open_ops[0],'buyout_config_id',None)
            last_buyout_config_id = getattr(last_buyout_config,'id',None)

            if not last_member:
                last_member = which_room_open_ops[0].member_id

            last_member_id = getattr(last_member,'id',None)


            #计算consume_minutes
            consume_minutes = changed_room_minutes = song_ticket_minutes =present_minutes =  0
            total_fee = room_fee = hourly_fee = changed_room_fee = changed_room_hourly_fee = guest_damage_fee = total_discount_fee = total_after_discount_fee = total_after_discount_cash_fee = 0.0
            on_credit_fee = member_card_fee = credit_card_fee = sales_voucher_fee =  free_fee =  0.0


            for r_ops in (record.room_checkout_ids,record.room_checkout_buyout_ids,record.room_checkout_buytime_ids,record.room_change_checkout_buyout_ids,record.room_change_checkout_buytime_ids):
                for r_op in r_ops:
                    consume_minutes += r_op.consume_minutes
                    changed_room_minutes += r_op.changed_room_minutes
                    song_ticket_minutes += r_op.song_ticket_minutes
                    room_fee += r_op.room_fee
                    hourly_fee += r_op.hourly_fee
                    changed_room_fee += r_op.changed_room_fee
                    changed_room_hourly_fee += r_op.changed_room_hourly_fee
                    guest_damage_fee += r_op.guest_damage_fee

                    member_card_fee += r_op.member_card_fee
                    credit_card_fee += r_op.credit_card_fee
                    on_credit_fee += r_op.on_credit_fee
                    sales_voucher_fee += r_op.sales_voucher_fee
                    free_fee += r_op.free_fee
                    total_fee += r_op.total_fee
                    total_discount_fee += r_op.total_discount_fee
                    total_after_discount_fee += r_op.total_after_discount_fee
                    total_after_discount_cash_fee += r_op.total_after_discount_cash_fee

            ret[record.id] = {
                    'guest_name' : guest_name,
                    'persons_count' : persons_count or 1,
                    'fee_type_id' : fee_type_id,
                    'price_class_id' : price_class_id,
                    'last_member_id' : last_member_id,
                    'last_buyout_config_id' : last_buyout_config_id,
                    'open_time' : open_time,
                    'close_time' : close_time,
                    'prepay_fee' : prepay_fee or 0.0,
                    'consume_minutes' : consume_minutes or 0,
                    'present_minutes' : present_minutes or 0,
                    'room_fee' : room_fee or 0.0,
                    'hourly_fee' : hourly_fee or 0.0,
                    'changed_room_fee' : changed_room_fee or 0.0,
                    'changed_room_hourly_fee' : changed_room_hourly_fee or 0.0,
                    'changed_room_minutes' : changed_room_minutes or 0,
                    'guest_damage_fee' : guest_damage_fee or 0.0,
                    'member_card_fee' : member_card_fee or 0.0,
                    'credit_card_fee' : credit_card_fee or 0.0,
                    'sales_voucher_fee' : sales_voucher_fee or 0.0,
                    'on_credit_fee' : on_credit_fee or 0.0,
                    'free_fee' : free_fee or 0.0,

                    'song_ticket_minutes' : song_ticket_minutes or 0,
                    'total_fee' : total_fee or 0.0,
                    'total_discount_fee' : total_discount_fee or 0.0,
                    'total_after_discount_fee' : total_after_discount_fee or 0.0,
                    'total_after_discount_cash_fee' : total_after_discount_cash_fee or 0.0,
                    }
            return ret

    _columns = {
            "operate_date" : fields.datetime('operate_datetime',required = True),
            "bill_no" : fields.char("bill_no",size = 64,required = True,help = "账单号"),
            "room_scheduled_ids" : fields.one2many("ktv.room_scheduled","room_operate_id",help="预定信息列表"),
            "room_opens_ids" : fields.one2many("ktv.room_opens","room_operate_id",help="开房信息列表"),
            "room_change_ids" : fields.one2many("ktv.room_change","room_operate_id",help="换房信息列表"),
            "room_checkout_ids" : fields.one2many("ktv.room_checkout","room_operate_id",help="包厢结账信息列表"),
            "room_checkout_buyout_ids" : fields.one2many("ktv.room_checkout_buyout","room_operate_id",help="包厢买断结账信息列表"),
            "room_checkout_buytime_ids" : fields.one2many("ktv.room_checkout_buytime","room_operate_id",help="包厢买钟结账信息列表"),
            "room_change_checkout_buytime_ids" : fields.one2many("ktv.room_change_checkout_buytime","room_operate_id",help="买钟-换房结账信息列表"),
            "room_change_checkout_buyout_ids" : fields.one2many("ktv.room_change_checkout_buyout","room_operate_id",help="买断-换房结账信息列表"),

            #以下为计算字段列表,FIXME 字段名称与room_checkout中的完全一致
            #基础信息

            "fee_type_id" : fields.function(_compute_fields,type='many2one',obj="ktv.fee_type",multi='compute_fields',string='计费方式'),
            "price_class_id" : fields.function(_compute_fields,type='many2one',obj="ktv.price_class",multi='compute_fields',string='价格类型(可能为None)'),
            "last_member_id" : fields.function(_compute_fields,type='many2one',obj="ktv.member",multi='compute_fields',string='会员id',help="最近一次使用的会员卡"),
            "last_buyout_config_id" : fields.function(_compute_fields,type='many2one',obj="ktv.buyout_config",multi='compute_fields',string='最近买断id',help="获取当前操作的最后一次买断id"),
            "guest_name" : fields.function(_compute_fields,type='string',multi='compute_fields',string='客人姓名'),
            "persons_count": fields.function(_compute_fields,type='integer',multi='compute_fields',string='客人人数'),
            "open_time" : fields.function(_compute_fields,type='datetime',multi="compute_fields",string="开房时间"),
            "close_time" : fields.function(_compute_fields,type='datetime',multi="compute_fields",string="关房时间"),
            "prepay_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="预付费",digits_compute = dp.get_precision('ktv_fee')),
            "consume_minutes": fields.function(_compute_fields,type='integer',multi="compute_fields",string="消费时长"),
            "present_minutes": fields.function(_compute_fields,type='integer',multi="compute_fields",string="赠送时长"),
            "room_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="包厢费",digits_compute = dp.get_precision('ktv_fee')),
            "hourly_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="钟点费",digits_compute = dp.get_precision('ktv_fee')),
            "changed_room_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="换房包厢费",digits_compute = dp.get_precision('ktv_fee')),
            "changed_room_hourly_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="换房钟点费",digits_compute = dp.get_precision('ktv_fee')),
            "changed_room_minutes": fields.function(_compute_fields,type='integer',multi="compute_fields",string="换房时长"),
            "guest_damage_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="客损费用",digits_compute = dp.get_precision('ktv_fee')),

            #不同支付方式的费用
            "member_card_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="会员卡支付费用",digits_compute = dp.get_precision('ktv_fee')),
            "credit_card_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="信用卡支付费用",digits_compute = dp.get_precision('ktv_fee')),
            "sales_voucher_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="代金券费用",digits_compute = dp.get_precision('ktv_fee')),
            #抵扣券明细
            "all_sales_voucher_ids"
            'on_credit_fee': fields.function(_compute_fields,type='float',multi="compute_fields",string="挂账费用",digits_compute = dp.get_precision('ktv_fee')),
            "free_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="免单费用",digits_compute = dp.get_precision('ktv_fee')),

            #欢唱券
            "song_ticket_minutes": fields.function(_compute_fields,type='integer',multi="compute_fields",string="欢唱券抵扣分钟"),
            "total_fee": fields.function(_compute_fields,type='float',multi="compute_fields",string="折前应收费用",digits_compute = dp.get_precision('ktv_fee')),
            "total_discount_fee" : fields.function(_compute_fields,multi = "compute_fields",string="合计折扣费用",digits_compute = dp.get_precision('ktv_fee')),
            "total_after_discount_fee" : fields.function(_compute_fields,multi = "compute_fields",string="合计应付费用(折后费用)",digits_compute = dp.get_precision('ktv_fee')),
            "total_after_discount_cash_fee" : fields.function(_compute_fields,multi="compute_fields",string="合计应收现金房费(折后费用)",digits_compute = dp.get_precision('ktv_fee')),
            }

    _defaults = {
            'operate_date' : fields.datetime.now,
            'bill_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'ktv.room_operate'),
            'credit_card_fee' : 0.0,
            }

    def calculate_sum_paid_info(self,cr,uid,operate_id,context=None):
        """
        获取该room_operate中所有已支付费用dict
        """
        fields = self.fields_get(cr,uid).keys()
        _logger.debug("fields = %s" % fields)
        _logger.debug("operate_id = %s" % type(operate_id))
        return self.read(cr,uid,operate_id,fields,context)

    def process_operate(self,cr,uid,operate_values):
        """
        包厢操作统一入口,调用不同业务类的操作
        这样设计的好处是隔离了变化,如果需要修改服务端的逻辑,客户端的调用逻辑不用做任何修改
        在客户端新增了业务实体调用,只用增加新的实体即可,其他不用做修改
        在js端也需要封装同样的调用接口来隔离变化
        :params room_id integer 包厢编码
        :operate_values 前端传入的业务操作数据
        :operate[osv_name] 要调用的实体业务对象名称,比如ktv.room_checkout
        调用示例:
        开房操作,返回三个参数 1 操作成功的实体对象 2 包厢应修改的状态 3 cron对象,用于处理对包厢的定时操作：
        (operate_obj,room_state,cron) = self.pool.get(operate_values['osv_name']).process_operate(cr,uid,opeate_values)
        更新当前包厢状态,添加cron对象,返回处理结果
        """
        room_id = operate_values['room_id']
        (operate_obj,room_state,cron) = self.pool.get(operate_values['osv_name']).process_operate(cr,uid,operate_values)
        #更新包厢状态
        if room_state:
            self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room_state})
        #TODO 添加cron对象
        if cron:
            self._create_operate_cron(cr,uid,cron)

        room_fields = self.pool.get('ktv.room').fields_get(cr,uid).keys()
        room = self.pool.get('ktv.room').read(cr,uid,room_id,room_fields)
        #返回两个对象room和room_operate
        _logger.debug("operate_obj = %s " % operate_obj)
        return {'room' : room,'room_operate' : operate_obj}

    def _create_operate_cron(self,cr,uid,cron_vals):
        """
        创建cron定时执行任务,在需要定时执行关房任务时,需要执行
        :params dict cron_vals 定时任务相关属性
        """
        return self.pool.get('ir.cron').create(cr,uid,cron_vals)

    def previous_room_opens_and_change(self,cr,uid,op_id):
        """
        获取最近一次包厢开房信息和换房信息,只适用于正常开房
        :param op_id integer room_operate id
        :return tuple room_open和room_change对象
        """
        operate_id = self.browse(cr,uid,op_id)
        return (operate_id.room_opens_ids and operate_id.room_opens_ids[0] or None,operate_id.room_change_ids and operate_id.room_change_ids[0] or None )
