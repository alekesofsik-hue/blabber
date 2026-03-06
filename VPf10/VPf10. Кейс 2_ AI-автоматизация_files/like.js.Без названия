$(function() {

    var like = 'Нравится';
    var cancelLike = 'Не нравится';

    if (typeof Yii != 'undefined') {

        like = Yii.t( "common", "Like" );
        cancelLike = Yii.t( "common", "Cancel like" );
    }

    var INACTIVE_TEXT = like;
    var ACTIVE_TEXT = cancelLike;

    var channel = window.accountUserWebSocketConnection
	    ? 'likes' + window.accountUserWebSocketConnection.pageKey + window.accountId
	    : undefined;

    $('body').delegate('.b-like .button', 'click', function(){
        var $el = $(this);
        if ($el.hasClass('auth-link')) {
            var active = window.gcModalActive();
            active && active.hide();
            window.gcGetDefaultModalAuth().show();

            return false;
        }
        var inProgress = $el.data('in-progress') === true;
        if (inProgress) {
            return false;
        }
        else {
            $el.data('in-progress', true);
        }
        var isReset = $el.hasClass('like');
        var isPositive = $el.hasClass('positive');
        var data = {
            object_id: $el.data('object-id')
            , object_type_id: $el.data('object-type-id')
            , is_reset: isReset ? 1 : 0
            , is_positive: isPositive ? 1 : 0
        };
        if (channel) {
            data.channel = channel;
        }
        var $parent = $el.parent();
        var count = $parent.find('.positive-count .value').html();
        count = count ? parseInt(count) : 0;
        applyCount($parent, '.positive-count', isReset ? (count ? count - 1 : 0) : count + 1 );
        var likes = {
            values: {}
        };
        likes.values[window.accountUserId] = !isReset;
        applyText($el, likes);
        ajaxCall('/cms/like/like', data, {}, function() {
            var positiveCount = response.likes.positive_count;
            applyCount($parent, '.positive-count', positiveCount);
            var negativeCount = response.likes.negative_count;
            //applyCount($parent, '.negative-count', negativeCount); // todo
            applyText($el, response.likes);
        }, function() {
            $el.data('in-progress', false);
        });
    });

    var applyCount = function ($parent, classSelector, count) {
        if (count > 0) {
            $parent.find(classSelector).removeClass('hide').find('.value').text(count);
        }
        else {
            $parent.find(classSelector).addClass('hide').find('.value').text(count);
        }
    };

    var applyText = function ($el, likes) {
        var text;
        if (likes.values[window.accountUserId] === true) {
            text = ACTIVE_TEXT;
            $el.addClass('like');
        }
        else {
            text = INACTIVE_TEXT;
            $el.removeClass('like');
        }
        $el.find('.html').html(text);
    };

    if (channel) {
        window.accountUserWebSocketConnection.subscribeChannel(channel, function(message, json){
            var $el = $('.'+json.class);
            if (!($el.length > 0)) {
                return;
            }
            var $parent = $el.parent();

            applyCount($parent, '.positive-count', json.likes.positive_count);
            applyCount($parent, '.negative-count', json.likes.negative_count);

            applyText($el.find('.positive'), json.likes);
        });
    }

   $('.positive-count:not(.disable-like-list)').on('click', function (e) {
        url = '/pl/cms/control/like/users-list?object_id=' + $(this).data('object-id') + '&object_type_id=' + $(this).data('object-type-id');
        ajaxCall(url, {}, {}, function (response) {
            var modal = window.gcModalFactory.create({show: false});

            modal.getModalEl().find('.modal-dialog').css('max-width', '600px');
            modal.getModalEl().find('.modal-dialog').css('margin-top', '50px');
            modal.getContentEl().addClass("row-container");
            modal.setTitle(response.title);
            modal.setContent(response.content);
            modal.show();

        });

        return false;
    });


});
