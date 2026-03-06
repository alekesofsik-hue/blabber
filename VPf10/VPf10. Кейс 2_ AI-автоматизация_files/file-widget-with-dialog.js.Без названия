jQuery.widget( 'gc.gcFileWidget', $.gc.gcFileSelectorFolder, {
	TYPE_IMAGE: 'image',
	TYPE_VIDEO: 'video',
    options: {
        owner: null,
        width: 200,
        height: 200,
        autoSize: false,
		type: this.TYPE_IMAGE,
		accept: '',
        isShowHint: ''
    },
    _create: function() {
        var self = this;
        this.elBlock = $('<div class="file-widget-with-dialog"></div>')
        this.elBlock.insertAfter( this.element );
        this.element.appendTo( this.elBlock );

	    if ( ! this.options.autoSize ) {
		    this.elBlock.width(this.options.width);
	    }

        var hash = this.element.val();
        this.previewEl = $( '<div class="preview-block"></div>' );
        this.previewEl.width( this.options.width );


        if ( this.options.autoSize ) {
            this.elBlock.addClass('auto-size');
        }
        else {
            this.elBlock.height(this.options.height);
            this.previewEl.height( this.options.height );
        }







        this.deleteEl = $('<a class="delete-link" href="javascript:void(0)"><span class="fa fa-times"></span></a>')
        this.deleteEl.appendTo( this.elBlock );

        this.deleteEl.click( function() {
            self.setValue( null )
        });

        this.previewEl.appendTo( this.elBlock );

        this.previewEl.click( function() {
			window.gcSelectFiles({
				selectedHash: hash,
				callback: function( hash ) {
					self.setValue( hash );
				},
				type: self.options.type,
				accept: self.options.accept,
                isShowHint: self.options.isShowHint
			});
		});

        this.showPreview();
    },
    init: function() {
        this.loadFiles( "favorites", this.filesEl )
    },
    showPreview: function() {
        if ( ! this.element.val() ) {
            this.elBlock.addClass("no-image")
            this.elBlock.removeClass("has-image")

			var labelUpload = 'Загрузить<br>' + (this.options.type === this.TYPE_VIDEO ? 'видео' : 'изображение');

            if (typeof Yii != 'undefined') {
				if (this.options.type === this.TYPE_VIDEO) {
					labelUpload = Yii.t('common', 'Upload video');
				} else {
					labelUpload = Yii.t('common', 'Upload picture');
				}
            }

			this.previewEl.html(labelUpload);
            this.deleteEl.hide();
        }
        else {
            this.elBlock.addClass("has-image")
            this.elBlock.removeClass("no-image")
			var thumbnailUrl = this.options.type === this.TYPE_VIDEO
				? getVideoThumbnailUrl(this.element.val(), this.options.width, this.options.height)
				: getThumbnailUrl(this.element.val(), this.options.width, this.options.height);
			this.previewEl.html("<img src='" + thumbnailUrl + "'>");
            this.deleteEl.show();
        }
    },
    setValue: function( hash ) {
        this.element.val( hash )
        this.element.trigger('change')
        this.showPreview();
    }
} );
