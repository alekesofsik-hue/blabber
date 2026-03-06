(function(){
    var updateCount = function(dataServiceId, value) {
        var $container = $('[data-service-id="'+dataServiceId+'"]');
        var $notifyCount = $container.find('.notify-count');
        value = parseInt(value);
        if (!value) {
            $notifyCount.addClass('hide');
        }
        else {
            $notifyCount.removeClass('hide');
            $notifyCount.html(value);
        }
    };
    //window.accountUserWebSocketConnection.subscribeChannel(
    //    'updateMessagesStat_'+window.accountUserId,
    //    function(message, json){
    //        ajaxCall('/notifications/messageStat/unchecked', {}, {
    //            suppressErrors : true
    //        }, function(response){
    //            updateCount('notifications', response.stat.total);
    //            updateCount('notifications-my', response.stat.my);
    //            updateCount('notifications-inbox', response.stat.inbox);
    //        });
    //    }
    //);
})();