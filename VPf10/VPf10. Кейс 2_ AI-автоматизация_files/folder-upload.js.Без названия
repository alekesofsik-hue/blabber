jQuery.widget( 'gc.gcFileSelectorFolderUpload', $.gc.gcFileSelectorFolder, {
    options: {
        owner: null
    },
    _create: function() {
        var self = this;

        $uploader = $('<div class="uploader"></div>')
        $uploader.appendTo( this.element )

        var queueId = "queue" + "FolderUpload";
        $el = $("<div id='" + queueId + "'></div>")
        $el.appendTo( this.element )

        this.filesEl = $('<div class="files-list"></div>')
        this.filesEl.appendTo( this.element )


        setTimeout( function() {
            var uploadifiveParams = {
                auto: true,
                buttonText: "Загрузить",
                width: 120,
                id: "folderUpload",
                queueID: queueId,
                dnd: false,
                removeCompleted: true,
                multi: true,
                uploadScript : '/fileservice/widget/upload?deprecated=11'
                    + '&secure=' + window.isEnabledSecureUpload
                    + '&host=' + window.fileserviceUploadHost,
                formData: { fullAnswer: true },
                onUploadError: function( file, errorCode, errorMsg ) {
                    alert("ERROR");
                },
                onUploadComplete: function( e,res  ) {
                    var res = JSON.parse( res );
                    self.fileUploaded( res.hash );
                }
            };

            if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
                uploadifiveParams.onUpload = getUploadifySecretLink;
            }

            $uploader.uploadifive(uploadifiveParams);

        }, 100 )



        //this.element.html("Выберите файл")

    },
    init: function() {
        this.loadFiles( "recent", this.filesEl )
    },
    fileUploaded: function( hash ) {
        var self = this;
        var $fileEl = this.createFileEl( hash )

        $fileEl.prependTo( this.filesEl );

        self.markFile( hash, 'recent', true );
    }
} );
