$(function() {
    $('body').delegate('.b-notifications-subscribe .button', 'click', function(){
        var $el = $(this);
        var isPositive = !$el.hasClass('subscribed');
        var data = {
            object_id: $el.data('object-id')
            , object_type_id: $el.data('object-type-id')
            , is_positive: isPositive ? 1 : 0
        };
        ajaxCall('/notifications/notifications/subscribe', data, {}, function() {
            if (!isPositive) {
                $el.html($el.data('msg-subscribe'));
                $el.removeClass('subscribed');
            }
            else {
                $el.html($el.data('msg-unsubscribe'));
                $el.addClass('subscribed');
            }
        });
    });
});