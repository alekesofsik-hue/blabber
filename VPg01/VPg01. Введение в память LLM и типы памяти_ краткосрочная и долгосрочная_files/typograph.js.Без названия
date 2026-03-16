(function($)
{
    $.Redactor.prototype.typograph = function()
    {
        return {
            init: function ()
            {
                //return;
                var self = this;
                var label = 'Типограф';
                if (typeof Yii != 'undefined') {
                    label = Yii.t('common', 'Typograph');
                }
                var button = this.button.add('typograph', label);
                this.button.addCallback(button, function() {
                    self.button.disableAll();

                    self.typograph.makeClear()
                });
            },
            makeClear: function()
            {
                var self = this;
                var html = this.code.get();

                //alert( html )
                ajaxCall( "/cms/control/xdget/typograf" , { textVal: html, type: 'html' }, {}, function( response ) {
                    self.code.set( response.textVal );
                    self.button.enableAll();
                });
            }
        };
    };
})(jQuery);
