//给backbone#collection添加update方法
//update 方法在0.9.10中才添加
_.extend(Backbone.Collection.prototype,{
    // Smartly update a collection with a change set of models, adding,
    // removing, and merging as necessary.
    update: function(models, options) {
      options = _.extend({merge: true, remove: true}, options);
      if (options.parse) models = this.parse(models, options);
      this.add(models, options);
      return this;
    }
});
//ktv_sale入口
openerp.ktv_sale = function(erp_instance) {
	//全局ktv_room_point对象
	erp_instance.ktv_sale = {};
	openerp.ktv_sale.helper(erp_instance);
	openerp.ktv_sale.model(erp_instance);
	openerp.ktv_sale.widget(erp_instance);
	erp_instance.ktv_sale.ktv_room_point = null;
	//App,初始化各种widget,并定义widget之间的交互
	erp_instance.ktv_sale.App = (function() {
		function App($el) {
			this.initialize($el);
		};
		App.prototype.initialize = function($el) {
			this.ktv_room_point_view = new erp_instance.ktv_sale.widget.KtvRoomPointWidget();
			this.ktv_room_point_view.$el = $el;
			this.ktv_room_point_view.start();
		};
		App.prototype.alert = function(options) {
			var alert = new erp_instance.ktv_sale.widget.AlertWidget(null, options);
			alert.appendTo($('.alert-wrapper'));
		}
		return App;
	})();
}

