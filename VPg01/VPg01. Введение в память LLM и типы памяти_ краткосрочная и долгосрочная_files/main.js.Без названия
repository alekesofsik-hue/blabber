function ajaxCall(url, data, options, successCallback, completeCallback, errorCallback) {
    if ( ! options ) {
        options = {};
    }
    if (options.useQueue) {
        ajaxCallQueue.request(url, data, options, successCallback, completeCallback);
        return;
    }

    var suppressErrors = undefined === options.suppressErrors ? false :options.suppressErrors;
	var enableCsrf = undefined === options.enableCsrf ? false :options.enableCsrf;
	var enableSimpleSign = undefined === options.enableSimpleSign ? false :options.enableSimpleSign;
	const suppressNotify = options.suppressNotify || false;

    if ( options.btn ) {
        options.btn.attr( 'disabled', 'disabled' );
    }
    var method = "post";
    if ( options.method ) {
        method = options.method;
    }

    if (enableCsrf && window.csrfToken !== undefined) {
		if (typeof data === 'object') {
			data['_csrf'] = window.csrfToken;
		}
		else if (typeof data === 'string') {
			data += '&_csrf='+window.csrfToken;
        }
    }
	if (enableSimpleSign && window.requestTime !== undefined && window.requestSimpleSign !== undefined) {
		if (typeof data === 'object') {
			data['requestTime'] = window.requestTime;
			data['requestSimpleSign'] = window.requestSimpleSign;
		}
		else if (typeof data === 'string') {
			data += '&requestTime='+window.requestTime;
			data += '&requestSimpleSign='+window.requestSimpleSign;
		}
	}
	if ( typeof(Storage) !== 'undefined' ) {
		try {
			var session = localStorage.getItem('session');
			var visit = localStorage.getItem('visit');
			var visitor = localStorage.getItem('visitor');
			var hash = localStorage.getItem('hash');
			if (session && hash) {
				if (typeof data === 'object') {
					data['gcSession'] = session;
					data['gcVisit'] = visit;
					data['gcVisitor'] = visitor;
					data['gcSessionHash'] = hash;
				} else if (typeof data === 'string') {
					data += '&gcSession=' + session;
					data += '&gcVisit=' + visit;
					data += '&gcVisitor=' + visitor;
					data += '&gcSessionHash=' + hash;
				}
			}
		} catch (e) {
			// В режиме блокирования кук (как минимум хром) бросает ошибку при доступе к
			// localStorage, хотя объект определен
		}
	}

    var async = true;
    if (options.async === false) {
        async = false;
    }

    var params = {
        url: url,
        type: method,
        data: data,
        async: async,
        complete: function ( jqResponse, status ) {

            error_text_value = 'Ошибка';
            if (typeof Yii != 'undefined') {
                error_text_value = Yii.t( "common", "Error" );
            }

            if ( options.btn ) {
                options.btn.removeAttr( 'disabled' );
            }

            try {
                response = $.parseJSON(jqResponse.responseText);
            } catch (exception) {
                response = jqResponse;
                response.success = false;
                response.message = "Неизвестная ошибка";
            }

			if (status === 'success') {
                if ( response.success ) {
					if (!suppressNotify && response.message && response.message.length > 0) {
                        var message = response.message;
                        var messageOptions = { type: "success" };
                        if (window.isPageRedesigned) {
                            showRedesignAlert('success', message)
                        } else {
                            if ( $.toast ) {
                                $.toast.config.width = Math.min(500, $(window).width() * 0.95);
                                $.toast(message, messageOptions);
                            }
                            else {
                                console.log(message);
                            }
                        }
                    }
                    if ( successCallback ) {
                        successCallback( response );
                    }
                }
                else {
                    if ( !suppressErrors ) {
                        if (window.isPageRedesigned && typeof showRedesignAlert === 'function') {
                            showRedesignAlert('danger', response.message)
                        } else {
                            if ( $.toast ) {
                                $.toast.config.width = Math.min(500, $(window).width() * 0.95);
                                if (response.only_last_error) {
                                    $('.toast .danger').remove();
                                }
                                $.toast(error_text_value + ": " + response.message, {
                                    type: "danger",
                                    sticky: response.toast_sticky === true,
                                });
                            } else {
                                alert(response.message);
                            }
                        }

                    }
                    if (errorCallback) {
                        errorCallback(response);
                    }
                }
            }
            else {
                if ( jqResponse.readyState == 0 ) {
                    return;
                }
                if ( !suppressErrors ) {
                    if ($.toast) {
                        $.toast.config.width = Math.min(500, $(window).width() * 0.95);
                        $.toast(  error_text_value + ": " + jqResponse.statusText, {type: "danger"});
                    } else {
						alert(response.message);
                    }
                }
				console.error('error', jqResponse.statusText);
				console.error(jqResponse.responseText);
                if (errorCallback) {
                    errorCallback(response);
                }
            }
            if (completeCallback) {
                completeCallback(response);
            }
        }
    };

    if (options.crossDomain) {
        params.crossDomain = true;
    }

    $.ajax(params);
}

var ajaxCallQueue = new (function () {
    /** @private */
    let self = this;

    this.limit = 4;
    /** @private */
    this.active = 0;
    /** @private */
    this.queue = [];

    this.request = function (url, data, options, successCallback, completeCallback) {
        this.queue.push({
            url: url,
            data: data,
            options: options,
            successCallback: successCallback,
            completeCallback: completeCallback
        });
        this.processQueue();
    }

    /**
     * @private
     */
    this.processQueue = function () {
        if (this.queue.length === 0) {
            return;
        }

        if (this.active >= this.limit) {
            return;
        }

        this.active++;
        let request = this.queue.shift();
        request.options.useQueue = false;

        ajaxCall(
            request.url,
            request.data,
            request.options,
            function (response) {
                try {
                    request.successCallback(response);
                } catch ($e) {
                    console.error($e);
                }
            },
            function () {
                if (request.completeCallback) {
                    try {
                        request.completeCallback();
                    } catch ($e) {
                        console.error($e);
                    }
                }
                self.active--;
                self.processQueue();
            },
        );
    }
})();

function bodyScrollTo( $el, padding ) {
    if (  padding  == null ) {
        padding = 400;
    }
    $( "body,html" ).animate({
        scrollTop: Math.round( $el.offset().top ) - padding
    }, 200 );
}



function initUploadify( $fileElem, options ) {

    var defaultButtonText = Yii.t('common', 'Добавить файлы');
    if ( $fileElem.attr( 'title') ) {
        defaultButtonText = $fileElem.attr( 'title');
    }
    var url = options.url ? options.url : (
        '/fileservice/widget/upload?deprecated=17'
            + '&secure=' + window.isEnabledSecureUpload
            + '&host=' + window.fileserviceUploadHost
    );
    var finalOptions = {
        auto: true,
        buttonText: options.buttonText ? options.buttonText : defaultButtonText,
        width: options.width ? options.width : 200,
        itemTemplate: options.itemTemplate ? options.itemTemplate : false,
        fileSizeLimit: options.fileSizeLimit ? options.fileSizeLimit : '2GB',
        formData: {
            userId: options.userId
        },
        uploadScript: url,
        onUploadError: function (file, errorCode, errorMsg) {
            alert("ERROR");
        },
        onUploadComplete: options.onUploadComplete ? options.onUploadComplete : function (e, res) {
            $hiddenInputEl = $(options.valueElemSelector);
            oldVal = $hiddenInputEl.val();
            newVal = oldVal;
            if (newVal && newVal.length > 0) {
                newVal += ",";
            }
            newVal += res;

            $hiddenInputEl.val(newVal);
            //location.href = location.href;
        },
        multi: options.hasOwnProperty('multi') ? options.multi : true
    };
    if (options.onQueueComplete) {
        finalOptions.onQueueComplete = options.onQueueComplete;
    }
    if (options.onUpload) {
        finalOptions.onUpload = options.onUpload;
    } else if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
        finalOptions.onUpload = getUploadifySecretLink;
    }

    if (options.other) {
        $.each(options.other, function(key, callback) {
            finalOptions[key] = callback;
        });
    }
    $fileElem.uploadifive(finalOptions);

    if ( options.fileSizeLimit ) {
        var fileSizeLimitWarning = options.fileSizeLimitWarning ? options.fileSizeLimitWarning : Yii.t('common', 'Макс. размер 2 ГБ');
        var warning = $("<p class='text-muted'>" + fileSizeLimitWarning + "</p>");
        $fileElem.parent().after(warning);
    }
}

window.errCount = 0;

function sendError(message) {
    window.errCount++;
    if (window.errCount <= 10) {
        $.ajax({
            url: '/pl/gc/log',
            method: 'POST',
            data: {data:  message}
        });
    }
}

function sendCreateLinkError(http, message, exc) {
    var postMessage = '';
    var toastMessage = '';
    if (http.responseJSON) {
        postMessage += (http.responseJSON ? ('json: ' + JSON.stringify(http.responseJSON)) : '');
    }

    toastMessage += 'status: ' + http.status + '; ';
    toastMessage += (http.statusText ? ('statusText: ' +  http.statusText + '; ') : '');
    postMessage += toastMessage;

    postMessage += (message ? ('message: ' + message + ' /// ') : '');

    postMessage += (exc ? ('exc: ' + exc + ' /// ') : '');

    if ($.isFunction($.fn.toast)) {
        $.toast(toastMessage, {type: "danger"});
    }
    console.log(postMessage);
    sendError(postMessage);
}

function getUploadifySecretLink(filesToUpload, settings) {
    var secureDirectUploadUri = '/fileservice/widget/secure-direct-upload';
    try {
        var session = localStorage.getItem('session');
        var requestParams = {"fs_ref": window.location.href};

        if (session !== undefined && session != null){
            var objSession = jQuery.parseJSON(session);

            if (objSession.hasOwnProperty('user_id') && objSession.user_id != null) {
                requestParams.fs_u = objSession.user_id;
            } else {
                requestParams.fs_u = -1;
            }
        }

        secureDirectUploadUri += '?' + jQuery.param(requestParams);
    } catch (err) {
    }

    if (typeof settings !== 'undefined' && settings !== null) {
        delete settings.uploadScript;
    }

    $.ajax({
        url: '/fileservice/widget/create-secret-link',
        method: 'GET',
        data: {
            host: window.fileserviceUploadHost,
            uri: secureDirectUploadUri,
            expires: 600
        },
        success: function (data) {
            if (data.link) {
                if (typeof settings !== 'undefined' && settings !== null) {
                    settings.uploadScript = data.link;
                }
            } else {
                ajaxCall('/fileservice/widget/log-error', {m:  'No link'}, {});
            }
        },
        error: function (http, message, exc) {
            sendCreateLinkError(http, message, exc);
        },
        async: false
    });
}

function panelPutTaskAside( task_id ) {
    $('.aside-loading').css('opacity', 1);
    $('.aside-link').css('opacity', 0).css('cursor', 'default');
    $.ajax({
        url: '/tasks/control/task/setNew',
        method: 'post',
        data: {'id': task_id },
        success: function(data) {
            panelLoad();
        }
    });
}
function panelFinishTask( task_id, result ) {
    $('.aside-loading').css('opacity', 1);
    $.ajax({
        url: '/tasks/control/task/setCompleted',
        method: 'post',
        data: {'id': task_id, result: result },
        success: function(data) {
            panelLoad();
        }
    });

    return false;
}

function panelLoad() {
    $.ajax({
        url: '/tasks/control/task/getPanel',
    success: function(data) {
        $('#task-panel-placeholder').html( data );
        }
    });
}

function setElLoading( el ) {
    $(el).html('<div class="text-center padding-10"><img src="/public/img/loading.gif"></div>');
}


$( function() {
    $('.editable .edit-link').click( function() {
        $(this).parents('.editable').toggleClass('edit');
        $(this).parents('.editable').find( 'input').focus();
    });
})

$( function() {
	$( '.action-link').click( function() {
		if ( $(this).data('gc-confirm' ) ) {
			if ( ! confirm( $(this).data('gc-confirm' ) ) ) {
				return false;
			}
		}
		$( '.page-main-form' ).find( 'input[name=action]').val( $(this).data('action' ) );
		$( '.page-main-form' ).submit();
	});
})


function extend(Child, Parent) {
    var F = function() { }
    F.prototype = Parent.prototype
    Child.prototype = new F()
    Child.prototype.constructor = Child
    Child.superclass = Parent.prototype
}

function mixin(cls, mixin) {
	for (var key in mixin) {
		if (cls.prototype[key]) {
			// console.log("Class " + cls + " already has a method named " + key + "!");
		}
		else {
			cls.prototype[key] = mixin[key];
		}
	}
}


$( function() {
	if ( $('.date-input').datetimepicker ) {
		$('.date-input').datetimepicker({
			timepicker: false, closeOnDateSelect: true, format:'d.m.Y',
			step: 20, lang:'ru', dayOfWeekStart: 1, todayButton: false, validateOnBlur: true, allowBlank: true, yearStart: '2013', yearEnd: '2020', lazyInit: false
		});

		$('.date-time-input').datetimepicker({
			timepicker: true, closeOnDateSelect: false, format:'d.m.Y H:i',
			step: 20, lang:'ru', dayOfWeekStart: 1, todayButton: false, validateOnBlur: true, allowBlank: true, yearStart: '2013', yearEnd: '2020', lazyInit: false
		});
	}
});


$.fn.scrollTo = function( target, options, callback ){
    if(typeof options == 'function' && arguments.length == 2){ callback = options; options = target; }
    var settings = $.extend({
        scrollTarget  : target,
        offsetTop     : 50,
        duration      : 500,
        easing        : 'swing'
    }, options);
    return this.each(function(){
        var scrollPane = $(this);
        var scrollTarget = (typeof settings.scrollTarget == "number") ? settings.scrollTarget : $(settings.scrollTarget);
        var scrollY = (typeof scrollTarget == "number") ? scrollTarget : scrollTarget.offset().top + scrollPane.scrollTop() - parseInt(settings.offsetTop);
        scrollPane.animate({scrollTop : scrollY }, parseInt(settings.duration), settings.easing, function(){
            if (typeof callback == 'function') { callback.call(this); }
        });
    });
};

function getThumbnailUrl( hash, width, height ) {
    var result = "/fileservice/file/thumbnail/h/" +  hash + "/s/" + width + "x" + height;
    if (window.accountId) {
        result += '/a/'+window.accountId;
    }
    if ( window.fileserviceThumbnailHost ) {
        result = "//" + window.fileserviceThumbnailHost + result;
    }
    return result;
}
function getBorderedThumbnailUrl( hash, width, height, borderName) {

    if ( borderName == "" ) {
        return getThumbnailUrl(hash, width, height);
    }

    var result = "/fileservice/file/bordered/h/" +  hash + "/s/" + width + "x" + height + "/b/" + borderName;
    if (window.accountId) {
        result += '/a/'+window.accountId;
    }
    if ( window.fileserviceThumbnailHost ) {
        result = "//" + window.fileserviceThumbnailHost + result;
    }
    return result;
}
function getDownloadUrl( hash ) {
	var result = "/pl/fileservice/user/file/download?h=" + hash;

    return result;
}

function isImage(hash) {
    let hashParts = hash.split(".");
	if (hashParts.length === 2) {
		let imgExts = ['jpeg', 'jpg', 'gif', 'png', 'heic'];
		return imgExts.includes(hashParts[1]);
	} else {
		return false;
	}
}

function isVideo(hash) {
    var hashParts = hash.toLowerCase().split(".");
    if (hashParts.length === 2) {
        var imgExts = ['mp4', 'mov'];
        return imgExts.includes(hashParts[1]);
    } else {
        return false;
    }
}

/**
 * Когда нужно обновить картинку в обход кэша браузера
 */
function updateThumbnailVersion(hash, version) {
    if (!window.thumbnailVersions) {
        window.thumbnailVersions = {};
    }
    window.thumbnailVersions[hash] = version;
}

function getVideoThumbnailUrl( hash, width, height ) {
    var url = "/pl/fileservice/video/preview-redirect/?file-hash=" + hash;
    if (window.thumbnailVersions && hash in window.thumbnailVersions) {
        url += '&v=' + window.thumbnailVersions[hash];
    }
    return url;
}

function gcGetFileObj( row ) {
    var title = row.title;
    if ( ! title ) title = row.filename;
    if ( ! title ) title = row.hash;

    var result = {
        hash: row.hash,
        title: title,
        description: row.description,
        getThumbnailUrl: function( width, height ) {
            return "/fileservice/file/thumbnail/h/" + this.hash + "/s/" + width + "x" + height;
        },
        getDownloadUrl: function() {
            return "/pl/fileservice/user/file/download?h=" + this.hash;
        }
    };
    return result;
}

var getProp = function(o, name, defaultValue) {
    return undefined === o[name] ? defaultValue : o[name];
};

$(function () {
    if ($('#blueimp-gallery').length == 0) {
        var $el = $('<div id="blueimp-gallery" class="blueimp-gallery blueimp-gallery-controls"><div class="slides next-click"></div><h3 class="title"></h3><a class="prev">‹</a><a class="next next-click">›</a><a class="play-pause"></a><ol class="indicator"></ol></div>')
        $el.hide();
        $el.appendTo($(document.body));
    }
});

$(function () {
    function handleAction(href, target) {
        var accountDomains = window.accountDomains || [];
        var pathsToWrap = window.pathsToWrap || [];
        var authingUrl = window.authingUrl || '';
        var openInExternalApp = target === '_blank';
        var mainDomain = window.mainDomain || '';
        if (!href.startsWith('https://') && !href.startsWith('http://')) {
            const locationHref = new URL(location.href);
            href = locationHref.origin + href;
            openInExternalApp = false;
        }
        if (accountDomains.includes((new URL(href)).host)) {
            openInExternalApp = false;
        }

        var url = new URL(href);
        for (var path of pathsToWrap) {
            if (url.pathname.startsWith(path)) {
                openInExternalApp = true;
                href = authingUrl !== '' && mainDomain === url.host
                    ? authingUrl + '&redirectUrl=' + encodeURIComponent(url.href)
                    : url.href;
                break;
            }
        }

        window.appHandleAction({
            type: "navigate",
            url: href,
            openInExternalApp: openInExternalApp
        });
    }
    $(".lt-block-wrapper a:visible, .xdget-block.xdget-html a:visible, .xdget-block.xdget-lessonContent a:visible, .lite-page a:visible")
        .on('click', function (event) {
            const elem = event.currentTarget;

            if (
                !elem ||
                !elem.href
            ) {
                return;
            }

            if (
                elem &&
                elem.href &&
                typeof elem.href === 'string' &&
                elem.href.indexOf('#') >= 0
            ) {
                const cleanThisHref = document.location.href.replace(/\#.*$/, '');
                const cleanAnchorHref = elem.href.replace(/\#.*$/, '');
                if (cleanThisHref === cleanAnchorHref) {
                    return;
                }
            }

            if (!elem.href.startsWith('#') && !elem.href.startsWith('javascript:') && window.appHandleAction) {
                event.preventDefault();
                handleAction(elem.href, elem.target);
                return false;
            }
        });
});

$( function() {
    $('.editable-link').each( function( index, el ) {
        $el = $(el)
        $wrapper = $el.parents('.editable-link-wrapper')

        if ( $wrapper.length == 0 ) {
            $wrapper = $('<span class="editable-link-wrapper"/>')
            $el.replaceWith( $wrapper )
            $el.appendTo( $wrapper )
        }

        $link = $('<a class="link"/>')
        if ( $el.data('header')) {
            $header = $('<h1/>')
            $link.appendTo( $header )
            $header.appendTo( $wrapper )
        }
        else {
            $link.appendTo( $wrapper )
        }

        var value = null;

        if ( $el.val() != "" ) {
            value = $el.val();
        } else if ( $el.attr("placeholder") && $el.attr("placeholder") != "" ) {
            if(!window.isPageRedesigned) {
                value = $el.attr("placeholder");
            } else {
                value = Yii.t( "common", "change" );
                $link.addClass('rd-fake-link rd-first-letter-up');
            }
        } else {
            value = 'изменить';

            if (typeof Yii != 'undefined') {
                value = Yii.t( "common", "change" );
            }
            $wrapper.addClass( 'no-value' );
            if(window.isPageRedesigned) {
                $link.addClass('rd-fake-link rd-first-letter-up');
            }
        }

        if (window.isPageRedesigned && typeof Yii != 'undefined') {
            if (value === 'male') {
                value = Yii.t("user", "Male");
            }
            if (value === 'female') {
                value = Yii.t("user", "Female");
            }
        }

        $link.html(value);

        $link.click( function() {
            $(this).parents('.editable-link-wrapper').addClass('edit-mode')
        })

    })
})

window.runOneTimeOnElement = function($el, key, callback) {
    if ($el.data(key)) {
        return;
    }
    $el.data(key, callback($el));
};
window.eachAndRunOneTimeOnElement = function($each, key, callback) {
    $each.each(function(index, el) {
        runOneTimeOnElement($(el), key, callback);
    });
}

function objectToQueryString (a) {
    var prefix, s, add, name, r20, output;
    s = [];
    r20 = /%20/g;
    add = function (key, value) {
        // If value is a function, invoke it and return its value
        value = ( typeof value == 'function' ) ? value() : ( value == null ? "" : value );
        s[ s.length ] = encodeURIComponent(key) + "=" + encodeURIComponent(value);
    };
    if (a instanceof Array) {
        for (name in a) {
            add(name, a[name]);
        }
    } else {
        for (prefix in a) {
            buildParams(prefix, a[ prefix ], add);
        }
    }
    output = s.join("&").replace(r20, "+");
    return output;
};
function buildParams(prefix, obj, add) {
    var name, i, l, rbracket;
    rbracket = /\[\]$/;
    if (obj instanceof Array) {
        for (i = 0, l = obj.length; i < l; i++) {
            if (rbracket.test(prefix)) {
                add(prefix, obj[i]);
            } else {
                buildParams(prefix + "[" + ( typeof obj[i] === "object" ? i : "" ) + "]", obj[i], add);
            }
        }
    } else if (typeof obj == "object") {
        // Serialize object item.
        for (name in obj) {
            buildParams(prefix + "[" + name + "]", obj[ name ], add);
        }
    } else {
        // Serialize scalar item.
        add(prefix, obj);
    }
}

$.fn.serializeObject = function()
{
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

window.gcIsHiddenTab = function(){
    var hidden, state;

    if (typeof document.hidden !== "undefined") {
        state = "visibilityState";
    } else if (typeof document.mozHidden !== "undefined") {
        state = "mozVisibilityState";
    } else if (typeof document.msHidden !== "undefined") {
        state = "msVisibilityState";
    } else if (typeof document.webkitHidden !== "undefined") {
        state = "webkitVisibilityState";
    }

    return document[state] == "hidden";
};
window.gcIsActiveTab = !window.gcIsHiddenTab();
$(window).focus(function() {
    window.gcIsActiveTab = true;
});

$(window).blur(function() {
    window.gcIsActiveTab = false;
});

window.gcGetCookie = function(name) {
    var matches = document.cookie.match(new RegExp(
        "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
    ));
    return matches ? decodeURIComponent(matches[1]) : undefined;
};

window.gcSetCookie = function gcSetCookie(name, value, options) {
    options = options || {};

    var expires = options.expires;

    if (typeof expires == "number" && expires) {
        var d = new Date();
        d.setTime(d.getTime() + expires * 1000);
        expires = options.expires = d;
    }
    if (expires && expires.toUTCString) {
        options.expires = expires.toUTCString();
    }

    value = encodeURIComponent(value);

    var updatedCookie = name + "=" + value;

    for (var propName in options) {
        updatedCookie += "; " + propName;
        var propValue = options[propName];
        if (propValue !== true) {
            updatedCookie += "=" + propValue;
        }
    }

    document.cookie = updatedCookie;
};


function addParamToLocation( key, value)
{
    key = encodeURI(key); value = encodeURI(value);

    var kvp = document.location.search.substr(1).split('&');

    var i=kvp.length; var x; while(i--)
    {
        x = kvp[i].split('=');

        if (x[0]==key)
        {
            x[1] = value;
            kvp[i] = x.join('=');
            break;
        }
    }

    if(i<0) {kvp[kvp.length] = [key,value].join('=');}

    //this will reload the page, it's likely better to store this until finished
    document.location.search = kvp.join('&');
}

function removeParamFromLocation( key )
{
    key = encodeURI(key);

    var kvp = document.location.search.substr(1).split('&');

    var i=kvp.length; var x; while(i--)
    {
        x = kvp[i].split('=');


        if (x[0]==key)
        {
            kvp[i] = null
            break;
        }
    }
    var search = kvp.join("&") != "&" ? kvp.join('&') : "";
//alert(kvp.length > 0 kvp.join('&') : "")
    //this will reload the page, it's likely better to store this until finished
    document.location.search = search;
}


function escapeDoubleQuotes(str) {
	return str.replace(/\\([\s\S])|(")/g,"\\$1$2");
}

function setVisibilityRelation( checkboxSelector, paramsSelector ) {
    var $checkboxSelector = $(checkboxSelector)
    var $paramsSelector = $(paramsSelector)
    var changed = function() {
        var checked = $checkboxSelector.prop('checked');
        if ( checked ) $paramsSelector.show(); else $paramsSelector.hide();
    }
    $checkboxSelector.click( changed )
    changed();
}

function getParamFromLocation( key )
{
    key = encodeURI(key);

    var kvp = document.location.search.substr(1).split('&');

    var i=kvp.length; var x; while(i--)
    {
        x = kvp[i].split('=');


        if (x[0]==key)
        {
            return x[1];
        }
    }
    return null;
}

function getParamFromHash( key )
{
    key = encodeURI(key);

    var kvp = document.location.hash.substr(1).split('&');

    var i=kvp.length; var x; while(i--)
{
    x = kvp[i].split('=');


    if (x[0]==key)
    {
		var res = x[1];
		return res;
    }
}
    return null;
}

var gcParseUrl = function(url) {
    var urlEl = document.createElement('a');
    urlEl.href = url;
    return urlEl;
};

var gcAddResourceElement = function(tag, attr, createElementCallback) {
    var resources = {};

    return function(resourceUrl) {
        if (!resources.hasOwnProperty(resourceUrl)) {
            var list = document.getElementsByTagName(tag);
            var i = list.length, exists = false;
            while (i--) {
                var url = gcParseUrl(list[i][attr]);
                if (url.pathname+url.search == resourceUrl) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                resources[resourceUrl] = createElementCallback(resourceUrl);
                console.log('loaded '+resourceUrl);
            }
        }
    };
};

var gcAddScriptElement = (function() {
    return gcAddResourceElement('script', 'src', function (resourceUrl) {
        var script = document.createElement("script");
        script.type = "text/javascript";
        script.src = resourceUrl;
        document.getElementsByTagName('head')[0].appendChild(script);
        return script;
    });
})();

var gcAddLinkElement = (function() {
    return gcAddResourceElement('link', 'href', function (resourceUrl) {
        var link = document.createElement("link");
        link.rel = "stylesheet";
        link.src = resourceUrl;
        document.getElementsByTagName('head')[0].appendChild(link);
        return link;
    });
})();



function replaceAll(str, find, replace) {
    return str.replace(new RegExp(find, 'g'), replace);
}

serializeObj = function(obj, prefix) {
    var str = [], p;
    for(p in obj) {
        if (obj.hasOwnProperty(p)) {
            var k = prefix ? prefix + "[" + p + "]" : p, v = obj[p];
            if ( typeof v === "undefined" ) {
                continue;
            }
            if ( v == null ) {
                continue;
            }
            str.push((v !== null && typeof v === "object") ?
                serializeObj(v, k) :
            encodeURIComponent(k) + "=" + encodeURIComponent(v));
        }
    }
    return str.join("&");
};

function initListSearch( element, selector ) {

    var filter = function( value ) {
        value = value.toLowerCase();
        var found = false;
        element.find(selector).each(function () {
            var text = $(this).html().toLowerCase();
            if (value == "") {
                $(this).show();
                found = true;
            }
            else {
                if (text.indexOf(value) > -1) {
                    $(this).show();
                    found = true;
                }
                else {
                    $(this).hide();
                }
            }

        })
        return found;
    };

    var placeholderValue = window.isPageRedesigned ? 'Поиск' : 'поиск';
    var notFound = 'ничего не найдено';
    if (typeof Yii != 'undefined') {
        placeholderValue = window.isPageRedesigned ? Yii.t("common", "Поиск") : Yii.t("common", "search");
        notFound = Yii.t("common", "ничего не найдено");
    }

    var liStyle = window.isPageRedesigned ? 'margin: 0; list-style: none; padding: 8px 12px;' : 'margin: 0; list-style: none; padding: 5px 3px;';

    var $searchRuleBlock = $("<li style='" + liStyle + "'><input class='search-input' placeholder='" + placeholderValue + "' type='text'/><div class='nothing-found-label' style='padding-top: 10px; background: lightyellow; display:none'>" + notFound + "</div></li>")
    if(window.isPageRedesigned) {
        if(element.find('li:not(.hidden):not(:has(input))').length >= 5) {
            $searchRuleBlock.prependTo ( element )
        }
    } else {
        $searchRuleBlock.prependTo ( element )
    }
    var searchRuleInput = $searchRuleBlock.find('input')
    searchRuleInput.keyup( function() {
        if ( filter( $(this).val() ) ) {
            $searchRuleBlock.find('.nothing-found-label').hide()
        }
        else {
            $searchRuleBlock.find('.nothing-found-label').show()
        }
    });
}

function initDropdownSearch( $dropdownMenu ) {

    $dropdownMenu = $dropdownMenu.find('.dropdown-menu')

    initListSearch( $dropdownMenu, 'a' );

    $dropdownMenu.parent().on( 'show.bs.dropdown', function() {
        setTimeout( function() {
            $dropdownMenu.find('.search-input').focus();
        })
    })




}


function number_format( number, decimals, dec_point, thousands_sep ) {	// Format a number with grouped thousands
    //
    // +   original by: Jonas Raoni Soares Silva (http://www.jsfromhell.com)
    // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +	 bugfix by: Michael White (http://crestidg.com)

    var i, j, kw, kd, km;

    // input sanitation & defaults
    if( isNaN(decimals = Math.abs(decimals)) ){
        decimals = 2;
    }
    if( dec_point == undefined ){
        dec_point = ",";
    }
    if( thousands_sep == undefined ){
        thousands_sep = ".";
    }

    i = parseInt(number = (+number || 0).toFixed(decimals)) + "";

    if( (j = i.length) > 3 ){
        j = j % 3;
    } else{
        j = 0;
    }

    km = (j ? i.substr(0, j) + thousands_sep : "");
    kw = i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thousands_sep);
    //kd = (decimals ? dec_point + Math.abs(number - i).toFixed(decimals).slice(2) : "");
    kd = (decimals ? dec_point + Math.abs(number - i).toFixed(decimals).replace(/-/, 0).slice(2) : "");


    return km + kw + kd;
}


function onTelegramAuth(user) {
    ajaxCall( "/pl/user/profile/login-with-telegram", { user: user }, {method: 'get'}, function( response ) {
        if ( window.afterTelegramAuthCallback ) {
            window.afterTelegramAuthCallback();
        }
        //alert( response )
    });
}

window.phoneChecked = false;
window.checkFormPhone = function(form) {
    var phoneInput = $(form).find('input.phone-input')
    if ( phoneInput.length > 0 && ! window.phoneChecked ) {
        ajaxCall( "/pl/user/profile/set-phone", { phone: phoneInput.val() }, {}, function( response ) {
            if ( response.data.success) {
                window.phoneChecked = true;
                $(form).submit()
            }
            else {
                alert( response.data.error )
            }
        } );
        return false;
    }
    else {
        return true;
    }

};
window.tt = function(category, text, params) {
    return (typeof Yii != 'undefined') ? Yii.t(category,  text, params) : text;
};


window.renderIcon = function( icon, $parentEl ) {

    let $el = $parentEl.find('.chatium-icon');
    if ( $el.length == 0 ) {
        $el = $('<div class="chatium-icon"/>').appendTo( $parentEl );
    }

    let url = icon.url;
    if ( ! url && icon.image ) {
        url = icon.image;
    }
    if ( icon.hash ) {
        url = getThumbnailUrl(icon.hash, 100, 100);
    }
    if ( url ) {
        $el.empty();
        $('<img/>').attr( 'src', url ).appendTo( $el );
    }
    else if ( icon.iconCssClass ) {
        $el.html("<div class='chatium-icon-text'><span class='" + icon.iconCssClass + "'></span></div>")
        $el.addClass('icon-type-icon' );
    }
    else {
        $el.html( "<div class='chatium-icon-text'>" + ( icon.text ? icon.text : "" ) + "</div>" );
        if ( icon.type ) {
            $el.addClass('icon-type-' + icon.type );
        }

    }
    if ( icon.color ) {
        $el.css('color', icon.color)
    }
    if ( icon.bgColor ) {
        $el.css('background-color', icon.bgColor)
    }
};
