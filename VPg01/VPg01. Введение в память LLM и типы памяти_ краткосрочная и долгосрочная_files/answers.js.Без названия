function $t(category, key, fallback = '') {
  if (typeof Yii != 'undefined') {
    return Yii.t(category, key);
  }
  return fallback ? fallback : key;
}

window.initAnswers = function () {
    var attachFile = function(block, insertAfter, uniqId) {
        var $attachFileBlock = block.find( '.attach-file-block' );
        if ( $attachFileBlock.length == 0 ) {
            $attachFileBlock = $( '<div class="attach-file-block"><input type="file" id="i'+uniqId+'" name="attach-file"><input class="attach-files" id="v'+uniqId+'" type="hidden" multiple="true"></div>' )
            $attachFileBlock.insertAfter( insertAfter );
            initUploadify( $attachFileBlock.find('#i'+uniqId), { valueElemSelector: $attachFileBlock.find( '#v'+uniqId ), userId: window.accountUserId , buttonText: window.addFilesLabel } );
        }
    };
    window.initAnswerBlock = function( $el ) {
        if ( $el.data('answer-block-inited') ) {
            return;
        }

        if (
            !!window.presaveInLocalStorageComments
            && $el.is('.simple-answer.user-answer')
        ) {
            var localStorageKey = 'new-comment-for-answer',
                localStorageValue = localStorage.getItem(localStorageKey);

            if (!!localStorageValue) {
                $el.find('.new-comment-textarea').val(localStorageValue);
            }
        }

        $el.find('.new-comment-textarea').autosize();

        $el.find('.action-link').click( function() {
            var that = this;
            var action = $(this).data('action');
            var $parentUserAnswer = $(this).parents('.user-answer');
            var $commentsForm = $parentUserAnswer.find('.comments-tree .comment-form-wrapper form');
            var $commentsTextarea = $commentsForm.find('.new-comment-textarea');
            var commentText = $commentsTextarea.val();

            if (commentText && commentText.length > 0) {
                $(document).trigger('gc:comment:submit:form', [$commentsForm, function() {
                    $(that).trigger('click');
                }]);
            }
            else {
                if ( action == "delete" && ! confirm( $t('common', "Вы уверены?") ) ) {
                    return false;
                }
                $(this).parents('form').find('input[name=action]').val( action );
                $(this).parents('form').submit();
            }
            return false;
        });

        if (
            !!window.presaveInLocalStorageComments
            && $el.is('.simple-answer.user-answer')
        ) {
            $el.find('.new-comment-textarea').change(function () {
                var value = $(this).val();
                if (value.length > 0) {
                    localStorage.setItem(localStorageKey, value);
                } else {
                    localStorage.removeItem(localStorageKey);
                }
            });
        }

        $el.find('.new-comment-textarea').keyup(function ( event ) {
            if ( $( this ).val().length > 0 ) {
                $(this).parents('.new-comment').addClass('active');

                /*if ( event.keyCode == 13 && event.ctrlKey ) {
                    $el.find('.new-comment-to-answer .btn-send').click();
                }*/
            }
            else {
                $(this).parents('.new-comment').removeClass('active');
            }
        });

        $el.find('.new-comment-textarea').focus(function ( event ) {
            $(this).parents('.new-comment').addClass('active');
        });

        $el.find('.new-comment-to-answer .btn-send').click(function () {

            $answerBlock = $(this).parents('.user-answer');
            $commentList = $answerBlock.find( '.comment-list' );
            $textarea = $answerBlock.find('.new-comment-textarea');
            $filesInput = $answerBlock.find('.attach-file-block .attach-files');
            var files = "";
            if ( $filesInput ) {
                files = $filesInput.val();
            }

            options = { btn: $( this) };
            data = { answer_id: $answerBlock.data('id'), text: $textarea.val(), files: files };

            ajaxCall( "/teach/control/answers/addComment", data, options, function() {

                var $newCommentBlock = $( response.commentBlock );

                if (!!window.presaveInLocalStorageComments) {
                    localStorage.removeItem('new-comment-for-answer');
                }

                $textarea.val('');
                $textarea.css('height', 26 );
                $answerBlock.find('.new-comment').removeClass( 'active' );
                $answerBlock.find('.new-comment').removeClass( 'active-with-file' );
                $answerBlock.find('.new-comment .attach-file-block').detach();

                $commentList.append( $newCommentBlock );
                //bodyScrollTo( $newCommentBlock );

                $newCommentBlock.effect( 'highlight', { duration: 1000 }  );
                updateImagesForEditor();
            }  );
            return false;
        });

        $el.find( '.attach-file-link').click( function() {

            $answerBlock = $(this).parents('.user-answer');
            $newCommentBlock = $el.find( '.new-comment' );

            attachFile(
                $newCommentBlock,
                $newCommentBlock.find( '.textarea-block .attach-file-link' ),
                'attachFileValue'
            );

            $newCommentBlock.addClass( 'active-with-file' );


        });

        $el.find( '.linked-answers-link').click( function()
        {
            var $link = $(this);
            var $userAnswerBlock = $(this).parents('.user-answer');
            var answerId = $(this).data('answer-id');


            ajaxCall( "/teach/control/answers/linkedAnswers/answerId/" + answerId, {}, {}, function( response ) {
                $new = $("<div class='linked-answer linked-answers-" + answerId + "' style='margin-top: 20px'>" + response.html + "</div>");
                $new.find( '.user-answer').each( function( index, el ) {
                    window.initAnswerBlock($(el));
                });
                $new.hide();
                $new.insertBefore( $userAnswerBlock )
                $new.show( 'slow');
                $link.parents('.user-answer').addClass( 'linked-answer');
                $link.parents('.linked-answers-link-block').detach();
            } );
        })

        $el.data('answer-block-inited', true );
    };

    var initUserAnswer = function() {
        $('.user-answer').each( function( index, userAnswerEl ) {
            window.initAnswerBlock( $(userAnswerEl) );
        });
    };

    initUserAnswer();

    $('.new-answer .btn-send').click(function () {
        if ( window.sendingComment ) {
            return false;
        }

        $answerBlock = $(this).parents('.user-answer');
        $textarea = $answerBlock.find('.new-comment-textarea');

        var listSelector = $answerBlock.data( 'answers-list-selector' );
        var data = { lesson_id: $answerBlock.data('lesson-id'), text: $textarea.val() };
        var options = { btn: $( this ) };
        window.sendingComment = true;

        ajaxCall( "/teach/control/answers/addAnswer", data, options, function( response ) {
            window.sendingComment = false;
            if ( listSelector ) {
                var $newAnswerBlock = $( response.answerBlock );
                $( listSelector).append( $newAnswerBlock );
                $newAnswerBlock.find('.comment-attach-file-link').trigger('click');
                $textarea.val('').trigger('keyup');
                $textarea.siblings('.emoji-wysiwyg-editor').empty();
                $answerBlock.removeClass( 'active' );

                if (!!window.presaveInLocalStorageComments) {
                    localStorage.removeItem('new-comment-for-answer');
                }

                bodyScrollTo( $newAnswerBlock );
                $newAnswerBlock.effect( 'highlight', { duration: 1000 }  );

                window.initAnswerBlock( $newAnswerBlock );
            }
            else {
                location.href = location.href + "?#answer" + "id";
            }
        } );

        return false;
    } );

    $( '.answer-with-controls .answer-status').click( function() {
        $answerControls = $(this).parents('.user-answer').find( '.answer-controls');
        bodyScrollTo( $answerControls );
        $answerControls.delay(200).effect( 'highlight', { duration: 500} );

    });

    $( '.change-public-level-link').click( function() {

        $publicLevelBlock = $( this).parents( '.public-level-block' );
        var data = {};
        data.level = $(this).data('level');
        data.id = $publicLevelBlock.data('answer-id');
        var options = {};

        ajaxCall( "/teach/control/answers/changePublicLevel", data, options, function( response ) {
            $publicLevelBlock.find( '.actual-public-level-label').text( response.newLabel );
            if ( response.isDefault ) {
                $publicLevelBlock.addClass( 'default-public-level');
            }
            else {
                $publicLevelBlock.removeClass( 'default-public-level');
                if ( $publicLevelBlock.hasClass( 'user-can-hide-answer' ) ) {
                    $publicLevelBlock.remove();
                }
            }
        } );
    });

    var hashCode = function(object){
        var hash = 0;
        if (object === undefined) {
            return hash;
        }
        if (object.length == 0) return hash;
        for (i = 0; i < object.length; i++) {
            char = object.charCodeAt(i);
            hash = ((hash<<5)-hash)+char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    };

    var callAfterLoadImage = function(imgSrc, callback) {
        var newImg = new Image();

        newImg.onload = function() {
            callback(newImg.width, newImg.height);
        };
        newImg.src = imgSrc;
    };

    var updateImagesForEditor = function() {
        if (!(window.userInfo.isAdmin || window.userInfo.isTeacher)) {
            return;
        }
        $('.has-quote-images .simple-filelist-icon img, .has-quote-images .type-file .value img, .comments-tree .has-quote-images .files img').each(function(i, e){
            if ($(e).hasClass('editor-added')) {
                return;
            }
            var $a = $(e).parent('a');
            var labelQuote = 'Цитировать изображение';
            if (typeof Yii != 'undefined') {
                labelQuote = $t('common', 'Quote image');
            }
            if (!document.getElementById('lessonSimpleBlockApp')) {
                $a.after('<div class="quote enable-fabric-editor-button edit-comment-inactive-element"><a href="javascript:void(0);">' + labelQuote + '</a><div>');
            }
            var that = this, editors = {}, $windowCache = {};
            var imageHash = $(e).data('hash');
            var imageSrc = $(e).data('editor-link');
			var cookieName = 'gc-image-editor-size-2';
            var currentSizeFromCookie = window.gcGetCookie(cookieName);
            var currentSize = currentSizeFromCookie ? currentSizeFromCookie : 'scale';
            var parents = $(e).parents('.simple-filelist-icon, .type-file .value, .file');
            var $quote = $('.quote', parents);
            $quote.click(function() {
                var $button = $(this);
                if (jQuery.gc === undefined || jQuery.gc.imageEditor === undefined) {
                    return false;
                }
                var size = currentSize;
                var sizeHash = 's'+size;
                if (editors[sizeHash] === undefined) {
                    var hash = hashCode(imageSrc+sizeHash)+'_'+Math.round(Math.random()*1000000);
                    var $div = $("<div class='modal image-editor-modal'><div class='modal-dialog'><div class='modal-content'><div class='modal-body'></div></div></div></div>");
                    $windowCache[sizeHash] = $div;
                    $div.modal({show: false});
                    $div.find('.modal-body').html([
                        '<div id="i'+hash+'"></div>'

                    ].join(''));

                    var labelScale = $t('common', 'scale', 'масштаб');
                    var labelOriginal = $t('common', 'original', 'оригинал');

                    var sizes = [
                        {value:'300', label:'300px'},
                        {value:'600', label:'600px'},
                        {value:'800', label:'800px'},
                        {value:'1200', label:'1200px'},
                        {value:'scale', label:labelScale},
                        {value:'original', label:labelOriginal}
                    ];
                    var liHtmlArr = [];
                    for (var i =0; i < sizes.length; i++) {
                        var sizeObject = sizes[i];
                        liHtmlArr.push('<li data-size="'+sizeObject.value+'" class="'+(size == sizeObject.value ? 'active' : '')+'">'+sizeObject.label+'</li>');
                    }
                    $div.find('.modal-content').append('<div class="close"><i class="fa fa-times"></div>').prepend([
                        '<ul class="size-selector">',
                        liHtmlArr.join(''),
                        '</ul>'
                    ].join(''));
                    $div.find('.size-selector li').data('button', $button).click(function() {
                        currentSize = $(this).data('size');
                        window.gcSetCookie(cookieName, currentSize, {path : '/'});
                        $('.image-editor-modal').modal('hide');
                        $button.trigger('click');
                    });
                    $('.close', $div).click(function(){
                        $div.modal('hide');
                    });
                    var viewportWidth = $(window).width();
                    var baseCanvasWidth = 600
                        ,canvasWidth = 600
                        ;
                    if ( viewportWidth < 767) {
                        canvasWidth = viewportWidth;
                    }
                    var controlsWidth = 300;
                    var imageSrcModified;
                    if ('original' === size || 'scale' === size) {
                        imageSrcModified = $(e).data('download-link');
                    }
                    else {
                        imageSrcModified = imageSrc.replace(baseCanvasWidth+'x', size+'x');
                    }

                    /*
                    var $closeBtn = $('<button class="text-center btn  btn-block btn-close-editor">Закрыть</button>')
                    $closeBtn.prependTo( $div.find('.modal-body') )
                    $closeBtn.click( function() {
                        $div.modal('hide');
                    })
                    */


                    callAfterLoadImage(imageSrcModified, function(widht, height){
                        if ('scale' === currentSize) {
                            if ( viewportWidth < 767 ) {
                                canvasWidth = viewportWidth;
                                imageSrcModified = imageSrc.replace(baseCanvasWidth+'x', canvasWidth+'x');
                            } else if (widht >= (viewportWidth - 360)) {
                                canvasWidth = Math.floor(viewportWidth * 0.5);
                                imageSrcModified = imageSrc.replace(baseCanvasWidth+'x', canvasWidth+'x');
                            }
                            else {
                                canvasWidth = widht;
                            }
                        }
                        else {
                            canvasWidth = widht;
                        }

                        var audioButton = '<div class="audio-comment" onclick="window.audioComments.record(this);">'
                            +'<span class="audio-status">'+$t('common', 'идет запись...')+'</span>'
                            +'<i  class="fa fa-microphone"></i></div>'
                            +'<div class="audio-control"></div>';
                        if (!window.navigator.getUserMedia) {
                            audioButton = '';
                        }

                        var canvasWidthAdd = 360;
                        if ( viewportWidth < 767 ) {
                            canvasWidthAdd = 5;
                            controlsWidth = 0;
                        }

                        var labelComment = $t('common', 'Add comment', 'Добавить комментарий');
                        var labelSave = $t('common', 'Save', 'Сохранить');

                        $div.find('.modal-dialog').css('width', (canvasWidth+canvasWidthAdd)+'px');
                        editors[sizeHash] = jQuery.gc.imageEditor({
                            id:'i'+hash
                            , backgroundImage: imageSrcModified
                            , afterLoadCallback : function(editor) {
                                $div.find('.gc-fabric-editor').css('width', (canvasWidth + controlsWidth)+'px');
                                $div.find('.canvas-wrapper').css('width', canvasWidth+'px');
                                $('.editor .buttons', $div).after([
                                    ,'<div class="additional-controls" style="padding: 0 10px 0 10px;">'
                                    ,'<div style="margin-bottom: 10px;">'
                                    ,'<textarea placeholder="' + labelComment + '" class="new-comment-textarea normal"></textarea>'
                                    ,'</div>'
                                    , audioButton
                                    ,'<div>'
                                    ,'<button class="save-button btn btn-primary disabled">' + labelSave + '</button>'
                                    ,'</div>'
                                    ,'</div>'
                                ].join(''));

                                $('.new-comment-textarea', $div).keyup(function ( event ) {
                                    if ( $( this ).val().length > 0 ) {
                                        $('.save-button', $div).removeClass('disabled');
                                    }
                                    else {
                                        $('.save-button', $div).addClass('disabled');
                                    }
                                });
                                var canvas = editor.canvas;

                                $('.save-button', $div).click(function(){
                                    //var json = editor.canvas.toJSON();
                                    //json.backgroundImage.src = imageHash;
                                    var parents = $(that).parents('.has-quote-images-settings-container');
                                    var settingsStr = parents.find('.comment-user-settings-json').html();
                                    var $textarea = $div.find('.new-comment-textarea');
                                    var dataAsArray = [
                                        {
                                            name : 'GetCourseComment[comment_text]',
                                            value : $textarea.val()
                                        },
                                        {
                                            name : 'GetCourseComment[settings]',
                                            value : settingsStr
                                        }
                                    ];

                                    $div.find('.additional-controls .audio-value').each(function(i,elem) {
                                        dataAsArray.push({
                                            name: 'GetCourseComment[audioFiles][]',
                                            value: $(elem).val()
                                        });
                                    });

                                    var imageJson = {};
                                    imageJson[imageHash] = {
                                        //svg : encodeURIComponent(editor.canvas.toSVG().replace(/(xlink:href=")https?:\/\/.*?\//g, "$1/"))
                                        svg : encodeURIComponent(editor.canvas.toSVG())
                                    };
                                    dataAsArray.push({
                                        name : 'filesJson',
                                        value : JSON.stringify(imageJson)
                                    });
                                    dataAsArray.push({
                                        name : 'files',
                                        value : imageHash
                                    });
                                    var data = $.param(dataAsArray);
                                    var $btn = $(this);
                                    $btn.attr('disabled', 'disabled');
                                    $(document).trigger('gc:comment:add:ajax', [null, data, function() {
                                        $div.modal('hide');
                                        editor.canvas.clear();
                                        $div.find('.audio-upload').remove();
                                    }, function() {
                                        $btn.removeAttr('disabled');
                                    }]);
                                    //var $commentList = $form.find( '.comment-list' );
                                    //var options = {
                                    //    btn : $(this)
                                    //};
                                    //var filesJson = {};
                                    //
                                    //filesJson[imageHash] = {
                                    //    //svg : encodeURIComponent(editor.canvas.toSVG().replace(/(xlink:href=")https?:\/\/.*?\//g, "$1/"))
                                    //    svg : encodeURIComponent(editor.canvas.toSVG())
                                    //};
                                    //var data = {answer_id: $form.data('id'), text: $textarea.val(), files: imageHash, filesJson: filesJson};
                                    //ajaxCall("/teach/control/answers/addComment", data, options, function() {
                                    //    $div.modal('hide');
                                    //    var $newCommentBlock = $( response.commentBlock );
                                    //
                                    //    $textarea.val('');
                                    //    $form.find('.new-comment').removeClass( 'active' );
                                    //    $form.find('.new-comment').removeClass( 'active-with-file' );
                                    //    $form.find('.new-comment .attach-file-block').detach();
                                    //
                                    //    $commentList.append( $newCommentBlock );
                                    //
                                    //    $newCommentBlock.effect( 'highlight', { duration: 1000 }  );
                                    //    editor.canvas.clear();
                                    //    updateImagesForEditor();
                                    //});
                                });
                            }
                        });
                    });


                }
                $windowCache[sizeHash].modal('show');
            });
            // debugger;
            if(window.location.hash && window.location.hash == '#quote-'+imageHash) {
                $quote.trigger('click');
            } else {

            }
            $(e).addClass('editor-added');
        });
    };
    updateImagesForEditor();

    var openTagsDialog = function( title, buttonText, tagsCallback, defaultTags ) {
        var modal = this.modal = window.gcModalFactory.create({show: false});
        var self = this;
        modal.reset();

        modal.setTitle(title);
        modal.setContent( "" );

        var $tagsEl = $("<input type=text name=tags />");
        $tagsEl.appendTo( modal.getContentEl() )
        var tagsCloudOptions = {
            objectTypeId: 1,
            filterByObjects: false,
            //listUrl : this.element.data('list-url'),
            showArchivedSelector : false,
            showEditLink : false
        };
        if (defaultTags) {
            tagsCloudOptions['defaultTags'] = defaultTags;
        }
        $tagsEl.tagsCloud(tagsCloudOptions);

        $saveBtn = $('<button class="pull-left btn btn-success">'+buttonText+'</button>')
        $saveBtn.appendTo( modal.getFooterEl() );
        $saveBtn.click( function() {
            var tagsStr = $tagsEl.tagsCloud('getTagsStr');
            tagsCallback( tagsStr, modal )
        })

        modal.show();
    }


    var addImagesToWorksLink = function() {
        $('.can-control-extended .answer-main-content .main, .can-control-extended .comment .text .main').each(function(e) {
            if ($(this).hasClass('to-review-button-added')) {
                return;
            }
            var successContent = '<span>Добавлен в отзывы</span>';
            if ($(this).data('to-review-converted')) {
                $el = $(successContent);
            }
            else {

                var labelAddUserReviews = $t('common', 'Add to user reviews', 'Добавить в отзывы пользователя');
                var labelSpecifyReviewTags = $t('common', 'Specify review tags', 'Укажите теги к отзыву');

                var $el = $('<a class="clearfix" href="javascript:void(0)">' + labelAddUserReviews + '</a>');
                var objectId = $(this).data('object-id');
                var objectTypeId = $(this).data('object-type-id');
                var converterTypeId = $(this).data('converter-type-id');
                $el.click(function (e) {
                    openTagsDialog(labelSpecifyReviewTags, labelAddUserReviews, function (tags, modal) {
                        ajaxCall("/pl/cms/ugc/object-to-ugc", {
                            object_id: objectId,
                            object_type_id: objectTypeId,
                            converter_type_id : converterTypeId,
                            tags: tags
                        }, {}, function () {
                            $el.replaceWith($(successContent));
                            modal.hide();
                        });
                    });

                    return false;

                });
            }
            if (
                window.accountId == 1005 || window.accountId == 12 || window.accountId == 1368
                || window.accountId == 19402 || window.accountId == 1398 || window.accountId == 4397
            ) {
                $(this).append($el);
                $(this).addClass("to-review-button-added");
            }
        });
        $( '.user-related-data img.editor-added' ).each( function( e ) {

            var hash = $(this).data('hash');
            if( $( this ).hasClass("add-to-works-link-added") || ! hash ) {
                return;
            }
            var labelAddToWorks = $t('common', 'Add to user works', 'Добавить в работы пользователя');
            var labelTags = $t('common', 'Specify tags for work', 'Укажите теги к работе');

            var $el = $('<a class="clearfix edit-comment-inactive-element" href="javascript:void(0)">' + labelAddToWorks + '</a>')

            $el.click( function(e) {

                var userId = $(this).parents('.user-related-data').data('user-id');
                var $lessonRelatedData = $(this).parents('.lesson-related-data');
                var lessonName = $lessonRelatedData.data('lesson-name');
                var lessonId = $lessonRelatedData.data('lesson-id');
                var defaultTags = $lessonRelatedData.data('lesson-ugc-default-tags');
                var id = $lessonRelatedData.data('id');
                var objectTypeId = $lessonRelatedData.data('object-type-id');

                openTagsDialog(labelTags, labelAddToWorks, function(tags, modal) {
                    var labelTitle = $t('common', 'Lesson', 'Урок');

                    ajaxCall( "/pl/cms/ugc/add-file-to-photo", {
                        userId: userId,
                        fileHash: hash,
                        title: labelTitle + ' "' + lessonName + '"',
                        objectId: id,
                        objectTypeId: objectTypeId,
                        lessonId: lessonId,
                        tags: tags
                    }, {}, function() {
                        modal.hide();
                    } )
                }, defaultTags ? defaultTags.split(',') : null);

                return false;

            });
            $el.insertAfter( $(this).parent() )

            $(this).addClass( "add-to-works-link-added" );
        })
    }
    addImagesToWorksLink();




    $('.comment-list').delegate('.answer-edit-comment-link', 'click', function(){
        var that = this;
        if ($(this).hasClass('disabled')) {
            return false;
        }
        var context = $(this).parents('.lesson-answer-comment');
        var content = $('.text-block .content-area', context);
        var edit = $('.text-block .edit-area', context);

        var url = $(this).attr('href');
        ajaxCall(url, {}, {}, function() {
            if (!response.success) {
                alert(response.content);
                return;
            }
            $(that).addClass('disabled');
            content.hide();
            edit.hide().html(response.content).show(500);
            $( '.attach-file-link', edit ).click( function() {
                var id = edit.parents('.lesson-answer-comment').data('id')+'lafu';
                attachFile(
                    edit,
                    edit.find( '.file-container' ),
                    id
                );
            });
            $('.simple-filelist-filename a', edit).each(function(index) {
                var hash = $(this).parents('li').prev('input[name*="currentFiles"]').attr('value');
                $(this).after(' <span><input type="checkbox" id="f'+hash+'" name="filesToDelete[]" data-hash="'+hash+'"> <label for="f'+hash+'"> удалить</label></span>');
            });
            $('.cancel-edit-link', edit).click(function(){
                edit.html('');
                $(that).removeClass('disabled');
                content.show(500);
                return false;
            });


            $('.btn-save-comment', edit).click(function(){

                var $form = $(this).parents( '.answer-comment-form' )

                var url = $form.data('action');
                var $filesInput = edit.find('.attach-file-block .attach-files');
                var files = '';
                if ( $filesInput ) {
                    files = $filesInput.val();
                }
                if (typeof files === 'undefined') {
                    files = [];
                }
                else {
                    files = files.split(',');
                }
                var currentFiles = {};
                $form.find('input[name*=currentFiles]').each(function(index){
                    var val = $(this).val();
                    currentFiles[val] = val;
                });
                var toDelete = [];
                $form.find('input[name*=filesToDelete]').filter(':checked').each(function(index){
                    delete currentFiles[$(this).data('hash')];
                });
                for(var key in currentFiles) {
                    files.push(currentFiles[key]);
                }
                var data = {
                    comment_id : $form.find('input[name=comment_id]').val()
                    ,text : $form.find('textarea[name=text]').val()
                    ,files  : files.join(',')
                };

                ajaxCall(url, data, {}, function() {
                      if (response.success) {
                          context.replaceWith(response.content);
                          updateImagesForEditor();
                      }
                      else {
                          alert(response.content);
                      }
                });

                return false;
            });
            $('textarea', context).autosize();
            $('textarea', context).addClass("edit-comment-textarea");

        }  );

        return false;
    });

    $(document).on('gc:comment:added', function(event) {
        updateImagesForEditor();
        addImagesToWorksLink();
    });
    $(document).on('gc:comment:edited', function(event) {
        updateImagesForEditor();
        addImagesToWorksLink();
    });

    $('#showMoreAnswers').on('click', function() {
        var $this = $(this);

        ajaxCall(
            '/teach/control/lesson/viewRestAnswers',
            {
                lessonId: window.lessonId,
                startAnswers: window.startAnswers
            },
            {},
            function ( response ) {
                var $answerBlock = $( response.answers );

                $('.answers-list').append($answerBlock);

                initUserAnswer();
                updateImagesForEditor();
                addImagesToWorksLink();

                window.startAnswers += window.answersPerPage;
                if (window.startAnswers > window.answersCount) {
                    $this.hide()
                } else {
                    $this.find('span').text(response.restCount);
                }
            }
        );
    });

	var $emojiContainer = $('body');// todo на body это жетсь, но пока хз куда еще
    if ( window.GcEmojiHelper ) {
    window.GcEmojiHelper.initEmojies($emojiContainer);
    window.GcEmojiHelper.initEmojiTextAreas($emojiContainer);
    }
    //$('.emoji-text').emoji();
    //$('.emoji-textarea').emojiButton();


    class Drawer {
        options = {
            root: '.gc-main-content',
        }
        drawerNode = null;
        contentNode = null;

        constructor() {
            this.render();
            this.drawerNode = $(this.options.root).find('.js-right-drawer');
            this.contentNode = this.drawerNode.find('.js-drawer-content');
        }

        close() {
            this.drawerNode.hide();
        }

        render() {
            $(this.options.root).append(`
				<div class="gc-right-drawer js-right-drawer">
					<div class="gc-history-wrapper">
						<div class="btn-close gc-right-drawer__close"
							onclick="$('.js-right-drawer').hide()"
							data-reactid=".0.1.0">
							<span class="fa fa-times text-muted" data-reactid=".0.1.0.0"></span>
						</div>
						<div class="gc-drawer-content js-drawer-content">
						</div>
					</div>
				</div>
			`);
        }

        showLoader() {
            this.contentNode.html('<div class="gc-drawer-loader"></div>');
        }

        renderContent(content) {
            if (content instanceof Promise) {
                this.showLoader(true);

                content.then((html) => {
                    this.contentNode.html(html);
                })
            } else {
                this.contentNode.html(content);
            }

            this.drawerNode.show();
        }
    }

    const historyDrawer = new Drawer();
    window.showHistoryDrawer = (id) => {
        const history = new HistoryList(id).getHistory();

        historyDrawer.renderContent(history)
    }

    class HistoryList {
        answerId = null;
        url = '/pl/teach/control/answers/answer-log/?id=';

        constructor(id) {
            this.answerId = id;
        }

        async load() {
            return new Promise((resolve, reject) => {
                ajaxCall(this.url + this.answerId, {}, {}, (response) => {
                    if (response.success) {
                        resolve(response.data.items)
                    } else {
                        reject(response.message)
                    }
                }, function () {})
            })
        }

        async getHistory() {
            const history = await this.load();

            return this.makeHistoryList(history);
        }

        makeHistoryList(history) {
            const timeline = $('<ul class="gc-history-timeline"></ul>')

            timeline.html(history.map((item) => {
                return `<li>
					<div class="gc-history-timeline--circle">
						<i></i>
					</div>
					<div class="gc-history-timeline--content">
						<span class="gc-history-timeline--date">${item.datetime}</span>
						<div class="gc-history-timeline--description">
							${item.text}
						</div>
					</div>
				</li>`
            }))

            return $(`<div>
				<div class="gc-drawer-title">История ответа #${this.answerId}</div>
			</div>`).append(timeline);
        }
    }
};

$( window.initAnswers );

jQuery(document).ready(function () {
    document.querySelectorAll('.js--ans-answer-video').forEach(function(el) {
        /** @type HTMLDivElement el **/
        var fileHash = el.dataset['hash'];
        new Clappr.Player({
            language: 'ru-RU',
            parentId: '#' + el.id,
            //source: '//getcourse.cdnvideo.ru/getcourse-vod/_definst_/mp4:fileservice/file/download-proxy/h/' + fileHash + '/playlist.m3u8',
            source: "http://v02.getcourse.ru:8082/vod_hls/fileservice/file/download-proxy/h/" + videoHash + "/master.m3u8",
            autoPlay: false,
            width: '100%'
            // height: '100%'
        });
    });
});
