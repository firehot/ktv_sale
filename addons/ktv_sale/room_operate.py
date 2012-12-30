# -*- coding: utf-8 -*-
from osv import osv,fields
from room import room

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

    _columns = {
            "operate_date" : fields.datetime('operate_datetime',required = True),
            "room_id" : fields.many2one('ktv.room','room_id',required = True,help="与此操作关联的包厢id"),
            "ref_room_operate_id" : fields.many2one('ktv.room_operate','ref_room_operate_id',help = "原包厢操作对象,换房时会存在"),
            "bill_no" : fields.char("bill_no",size = 64,required = True,help = "账单号"),
            "room_scheduled_ids" : fields.one2many("ktv.room_scheduled","room_operate_id",help="预定信息列表"),
            "room_opens_ids" : fields.one2many("ktv.room_opens","room_operate_id",help="开房信息列表"),
            "room_checkout_ids" : fields.one2many("ktv.room_checkout","room_operate_id",help="包厢结账信息列表"),
            "room_checkout_buyout_ids" : fields.one2many("ktv.room_checkout_buyout","room_operate_id",help="包厢买断结账信息列表"),
            "room_checkout_buytime_ids" : fields.one2many("ktv.room_checkout_buytime","room_operate_id",help="包厢买钟结账信息列表"),
            "room_change_checkout_buytime_ids" : fields.one2many("ktv.room_change_checkout_buytime","room_operate_id",help="买钟-换房结账信息列表"),
            "room_change_checkout_buyout_ids" : fields.one2many("ktv.room_change_checkout_buyout","room_operate_id",help="买断-换房结账信息列表"),
            }

    _defaults = {
            'operate_date' : fields.datetime.now,
            'bill_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'ktv.room_operate'),
            }

    def _get_current_room_id(self,cr,uid,ids,fieldnames,args,context = None):
        """
        获取当前包厢id,由于存在换房情况,所以当前room_id可能并不是current_room_id
        """
        ret = dict()
        the_room
        for record in self.browse(cr,uid,ids):
            ret[record.id]['current_room_id'] = False


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
        self.pool.get('ktv.room').write(cr,uid,room_id,{'state' : room_state})
        #TODO 添加cron对象
        if cron:
            self._create_operate_cron(cr,uid,cron)

        room_fields = self.pool.get('ktv.room').fields_get(cr,uid).keys()
        room = self.pool.get('ktv.room').read(cr,uid,room_id,room_fields)
        #返回两个对象room和room_operate
        return {'room' : room,'room_operate' : operate_obj}

    def _create_operate_cron(self,cr,uid,cron_vals):
        """
        创建cron定时执行任务,在需要定时执行关房任务时,需要执行
        :params dict cron_vals 定时任务相关属性
        """
        return self.pool.get('ir.cron').create(cr,uid,cron_vals)

    def get_presale_last_checkout(self,cr,uid,id,context = None):
        """
        获取给定包厢id的最后一次预售结账信息
        :params integer room_id 要查询的包厢id
        :return dict 最后一次包厢结账信息
                ret['model_name'] string 返回的最后一次结账的对象类型
                ret['vals'] dict 最后一次结账信息数据
                无最后一次结账信息,返回None
        """
        cur_operate_id = self.browse(cr,uid,id,context)

        #如果当前没有包厢操作信息,或包厢不处于buytime buyout状态时,则返回None
        if not cur_operate_id:
            return None

        #先判断有无换房结算信息,换房结算信息是最后一次结账信息
        #_logger.debug("cur_operate_id 's attr :  %s " % dir(cur_operate_id))
        last_checkouts = cur_operate_id.room_change_checkout_buyout_ids or cur_operate_id.room_change_checkout_buytime_ids

        #如果换房结算信息不存在,则取room_checkout_buyout或room_checkout_buytime
        if not last_checkouts:
            last_checkouts = cur_operate_id.room_checkout_buyout_ids or cur_operate_id.room_checkout_buytime_ids

        if not last_checkouts:
            return None
        return last_checkouts[0]
