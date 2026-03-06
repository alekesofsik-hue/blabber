(function () {
    var factory = function () {

    };
    factory.prototype._callback = undefined;
    factory.prototype._queue = [];
    factory.prototype.create = function (el, params, callback) {
        if (this._callback) {
            this._callback(el, params, callback);
        }
        else {
            this._queue.push({
                el: el,
                params: params,
                callback: callback
            });
        }
    };
    factory.prototype.registerCallback = function (callback) {
        this._callback = callback;
        var queue = this._queue;
        var length = queue.length;
        for (var i = 0; i < length; i++) {
            var item = queue[i];
            this._callback(item.el, item.params, item.callback);
        }
        this._queue = [];
    };

    window.UserFormFactory = new factory();
    window.createUserForm = function (el, params, callback) {
        window.UserFormFactory.create(el, params, callback);
    };

    window.gcUserFormModal = function(formParams, modalParams){
        var auth = window.gcModalFactory.create(modalParams);
        modalParams = undefined === modalParams ? {
            show : false
        } : modalParams;
        auth.show();
        auth.hide();
        modalParams.show && auth.hide();
        var $modal = auth.get$Modal();
        $modal.find('.modal-dialog').addClass('auth');
        $modal.find('.modal-body').css('padding', '0');
        var id = auth.getContentId();
        createUserForm(document.getElementById(id), formParams);

        return auth;
    };

    var defaultAuth;
    window.gcGetDefaultModalAuth = function () {
        if (!defaultAuth) {
            defaultAuth = window.gcUserFormModal({
                showSocialAuth: true
            });
        }
        return defaultAuth;
    };
})();