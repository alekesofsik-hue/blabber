jQuery.widget( 'gc.gcFileSelectorFolder', {
	TYPE_IMAGE: 'image',
	TYPE_VIDEO: 'video',
	TYPE_VIDEO_NOTE: 'video_note',
    TYPE_AUDIO: 'audio',
	FOLDER_TYPE_CUSTOM: 'custom',
	ORDER_TYPE_FILENAME: 'filename',
	ORDER_TYPE_DATE: 'date',
    options: {
        owner: null,
        folder: null,
        selectedHash: null,
		fileSizeLimit: '6GB',
		fileSizeLimitWarning: (typeof Yii != 'undefined') ? Yii.t('common', 'Max size {n} GB', 6) : 'Max size 6 GB',
		fileType: this.TYPE_IMAGE,
		accept: '',
		onUploadComplete: null,
		folderType: null,
		directoryId: null,
		label: '',
		directories: null,
		directoriesSelectEl: null,
		currentSearch: null,
		fromWebinar: false,
		extensions: null,
		fileDialogLabel: null,
		forceFileType: null
	},

    _create: function() {
        var self = this;

		var isFromWebinar = this.options.fromWebinar;

		this.contentEl = this.options.contentEl
		this.options.orderBy = self.ORDER_TYPE_DATE

        this.element.addClass("folder")
		var $folderHeader = $('<div class="folder-header"></div>')
		this.folderHeaderEl = $folderHeader

        $folderHeader.appendTo(this.element)

		var $title = $('<div class="folder-title" contenteditable="false" data-filename="' +
			this.options.label + '">' + this.options.label + '</div>');

		if (self.options.folderType === self.FOLDER_TYPE_CUSTOM) {
            $title.click(function () {
                $(this).attr('contenteditable', 'true').attr("tabindex", -1).focus()
				$(this).css('background-color', '#d2d2d2')
            })

			$title.on('keypress', function (e) {
                if (e.keyCode === 13) {
                    e.preventDefault(e)
                    self.renameDirectory($(this))
                }
            })

            $title.on('focusout', function () {
                self.renameDirectory($(this))
            })
		}

        $title.appendTo(isFromWebinar ? '' : $folderHeader)

		var $line = $('<div></div>');
        $line.css('display', isFromWebinar ? 'block' :  'none');

        var typeLabel;
		if (self.options.fileDialogLabel !== null) {
			typeLabel = self.options.fileDialogLabel;
		} else {
			switch (self.options.fileType) {
				case self.TYPE_VIDEO:
				case self.TYPE_AUDIO:
					typeLabel = self.options.fileType
					break;
				case self.TYPE_IMAGE:
					typeLabel = 'image|images'
					break;
			}
		}

		var $searchFileInput = $('<div class="search-file-input">'
			+ '<input class="files-search-input" placeholder="' + window.tt('common', 'Search by name') + '">'
			+ '</div>'
		);
        var $searchZoomer = $('<div class="search-zoomer glyphicon glyphicon-search"></div>')
		var $filesNumber = $('<div class="files-number">0 ' + window.tt('common', typeLabel, 0) + '</div>')
		var $sortForm = $('<div class="sort-form"><select id="order-by">'
			+ '<option value="date">' + window.tt('common', 'Date added') + '</option>'
			+ '<option value="filename">' + window.tt('common', 'name') + '</option>'
			+ '</select></div>'
		);
		var $deleteFolder = $('<div class="delete-folder-btn btn btn-secondary">'
			+ window.tt('common', 'Delete folder')
			+ '</div>'
		);

		self.filesNumber = $filesNumber

		if (self.options.folderType === self.FOLDER_TYPE_CUSTOM) {
            $deleteFolder.appendTo(isFromWebinar ? '' : $folderHeader)
        }

		$('<br>').appendTo(isFromWebinar ? '' : $folderHeader)
        $filesNumber.appendTo(isFromWebinar ? '' : $folderHeader)
        $sortForm.appendTo(isFromWebinar ? '' : $folderHeader)
        $sortForm.change(function () {
            self.changeOrder($(this))
        })

        $searchFileInput.appendTo(isFromWebinar ? '' : $folderHeader)
        $searchZoomer.appendTo(isFromWebinar ? '' : $folderHeader)

        $searchZoomer.click(function () {
        	if ($searchFileInput.css('display') === 'none') {
                $searchFileInput.fadeIn(1500);
                $searchFileInput.css('display', 'inline-block')
                $searchFileInput.find('.files-search-input').focus()
			}
        })

        $deleteFolder.click(function () {
			var isAgreed = confirm(window.tt('common', 'The folder and all files in it will be deleted.'));

			if (isAgreed) {
				self.deleteFolder()
			}
        })

        $searchFileInput.focusout(function (e) {
            self.searchFiles(e, $searchFileInput)
        })

        $searchFileInput.on("keypress", function (e) {
            self.searchFiles(e, $searchFileInput)
        })

        // Left part of line
		var $leftPartWrapper = $('<div></div>');
		$leftPartWrapper.css('display', 'inline-block');
		$leftPartWrapper.appendTo($line);
		var $uploader = $('<div class="uploader"></div>');
		$uploader.appendTo($leftPartWrapper);

	    var $rightPartWrapper = $('<div></div>');
	    $rightPartWrapper.css('display', 'inline-block').css('vertical-align', 'top').css('padding', '4px 0 0 20px');
	    $rightPartWrapper.appendTo($line);

		var $clear = $("<span class='clear-link'>" + window.tt('common', 'Reset') + "</span>")
			.appendTo( $rightPartWrapper )
			.click(function() {
				self.selectFile( null );
			});


	    // Right part of line
		if (self.options.fileType === self.TYPE_VIDEO) {
			var $rightPart = self.buildUploadByLink();
			$rightPart.appendTo($rightPartWrapper);
		}

		$line.appendTo($folderHeader);

		var queueId = "queue" + this.options.folder;
		var $queue = $("<div id='" + queueId + "' class='queues'></div>")
        $queue.css('display', 'contents')
		$queue.appendTo($folderHeader)
		if (self.options.fileType === self.TYPE_VIDEO || self.options.fileType === self.TYPE_AUDIO) {
            $queue.css('height', '5px')
		}

		this.filesEl = $('<div class="files-list"></div>')
		this.filesEl.appendTo(this.element)

		if (window.fileserviceTusFeatureEnabled && tus.isSupported) {
			$('<div class="tus-uploader" />').appendTo($uploader).tusUploader({
				'accept': self.options.accept,
				'progressContainer': $queue,
				'onSuccess': function (url, file) {
					$.ajax({
						url: url,
						method: 'PUT',
						success: function (data) {
							self.fileUploaded(data.hash, data.filename);
                            $queue.text('')
							if (self.options.onUploadComplete) {
								self.options.onUploadComplete(data.hash);
							}
						},
					});
				},
			});

			if ( self.options.fileSizeLimit && self.options.fileSizeLimitWarning ) {
				$("<p class='text-muted'>" + self.options.fileSizeLimitWarning + "</p>")
					.appendTo($uploader);
			}

			return;
		}

		var uploadifiveParams = {
			auto: true,
			buttonText: window.tt('common', 'Upload'),
			width: 120,
			id: "folderUpload" + self.options.folder,
			queueID: queueId,
			dnd: false,
			removeCompleted: true,
			multi: true,
			fileSizeLimit: self.options.fileSizeLimit,
			uploadScript: '/fileservice/widget/upload?deprecated=12'
				+ '&secure=' + window.isEnabledSecureUpload
				+ '&host=' + window.fileserviceUploadHost,
			formData: {fullAnswer: true},
			onUploadError: function(file, errorCode, errorMsg) {
				alert("ERROR");
			},
			onUploadComplete: function(e, res) {
				res = JSON.parse(res);
				self.fileUploaded(res.hash, res.filename);
                $queue.text('')

				if (self.options.onUploadComplete) {
					self.options.onUploadComplete(res.hash);
				}
			}
		};


		if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
			uploadifiveParams.onUpload = getUploadifySecretLink;
		}

		if (this.options.accept) {
			// Потому что fileType параметр uploadifive как-то не так работает.
			// При указании video/* кучу видео форматов не позволяет выбрать
			// Если перечислить конкретные расширения файлов (или mime-type'ы), то тоже не все их воспринимает
			uploadifiveParams.onInit = function() {
				var $fileInput = $('input[type=file]', self.element);
				$fileInput.attr('accept', self.options.accept);
			};
			// При добавлении очередного файла создаются еще input'ы и по этому событию их можно обработать
			uploadifiveParams.onUpload = function(filesToUpload, settings) {
				var $fileInput = $('input[type=file]', self.element);
				$fileInput.attr('accept', self.options.accept);

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

				$.ajax({
					url: '/fileservice/widget/create-secret-link',
					method: 'GET',
					data: {
						host: window.fileserviceUploadHost,
						uri: secureDirectUploadUri,
						expires: 600,
						is_video: 1
					},
					success: function (data) {
						if (data.link) {
							settings.uploadScript = data.link;
						}
					},
					error: function (http, message, exc) {sendCreateLinkError(http, message, exc);},
					async: false
				});
			};
		}

        setTimeout( function() {
			$uploader.uploadifive(uploadifiveParams);

            if ( self.options.fileSizeLimit && self.options.fileSizeLimitWarning ) {
                var warning = $("<p class='text-muted'>" + self.options.fileSizeLimitWarning + "</p>");
                $uploader.parent().after( warning );
            }

        }, 100 )

    },
	deleteFolder: function() {
		var self = this
		var dirId = self.options.directoryId

        ajaxCall("/pl/fileservice/directory/delete",
            {directory_id: dirId}, {}, function() {
                var $menuFolder = self.options.directories.find('.custom-directory[data-id=' + dirId + ']')
                var $recentFolder = self.options.directories.find('.folder-picker-recent')
                $menuFolder.remove()
                $recentFolder.click()
            })
	},
	searchFiles: function(e, el) {
		var input = el.find('.files-search-input')[0].value.replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');
		var self = this

        self.currentSearch = input

        if (e.type === 'keypress' && e.keyCode !== 13) {
        	return
		}

		if ((e.type === 'focusout' || (e.type === 'keypress' && e.keyCode === 13)) && input.trim() === '') {
            self.loadFiles(this.options.folder, this.filesEl, null, '')

            el.fadeOut()
			return
		}

        self.loadFiles(this.options.folder, this.filesEl, null, input)
	},
	changeOrder: function(orderEl) {
		var self = this
        var orderBy = orderEl.find('#order-by')[0].value

        self.options.orderBy = orderBy

        self.loadFiles(this.options.folder, this.filesEl, null, this.currentSearch)
    },
	renameDirectory: function($title) {
        var text = $title.text().trim().replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');
        var self = this

        if (!text) {
            $title.text($title.data('filename'));
            $.toast(window.tt('common', 'Incorrect folder name'), {type: "danger"});
        } else {
            ajaxCall("/pl/fileservice/directory/rename",
				{directory_id: self.options.directoryId, name: text}, {}, function() {
             		var $menuFolder = self.options.directories.find('#folder-text-' + self.options.directoryId)

					$menuFolder.text(text)
					$menuFolder.attr('title', text)

					$title.attr('contenteditable', 'false')
                    $title.css('background-color', '')
                    $title.text(text)
			})
        }
	},
	buildUploadByLink: function() {
		var self = this;

		var $content = $('<div></div>');

		if (window.file_upload_blocking) {
			return $content;
		}

		var $uploadByLink = $('<a href="javascript:void(0);">' + window.tt('common', 'Upload file by link') + '</a>');
		$uploadByLink.appendTo($content);

		var $input = $('<input placeholder="' + window.tt('common', 'Link from file storage') + '" type="url"/>');
		$input.css('min-width', '300px');
		$input.hide();
		$input.appendTo($content);

		var $btn = $('<a href="javascript:void(0);">' + window.tt('common', 'Upload') + '</a>');
		$btn.css('padding-left', '10px');
		$btn.hide();
		$btn.appendTo($content);

		var $loading = $('<img src="/public/img/loading.gif">');
		$loading.hide();
		$loading.appendTo($content);

		$uploadByLink.click(function() {
			$uploadByLink.hide();
			$input.show();
			$btn.show();
		});

		$btn.click(function() {
			var url = $input.val();
			if (url.length === 0) {
				$.toast(window.tt('common', 'Enter a link'), {type: "danger"});
				return;
			}

			var hashRegExp = /(?:AB\.)?[a-f\d]{32}\.[\w\d]+/gi;
			var entries = url.match(hashRegExp);
			if (!entries || entries.length === 0) {
				$.toast(Yii.t('common', 'Only links from file storage can be inserted'), {type: "danger"});
				return;
			}


			var hash = entries[entries.length - 1].toLowerCase();
			var hashParts = hash.split('.');
			var ext = hashParts[hashParts.length-1].toLowerCase();

			var $existFileEl = self.getFileElByHash(hash);
			if ($existFileEl.length > 0) {
				$.toast(window.tt('common', 'This file is already in the current folder'), {type: "danger"});
				return;
			}

			if (self.options.accept) {
				var acceptExts = self.options.accept.toLowerCase().match(/[\w\d]+/g);
				if (acceptExts && acceptExts.length > 0) {
					if (!acceptExts.includes(ext)) {
						$.toast(window.tt('common', 'The following formats are allowed') + ': ' + self.options.accept, {type: "danger"});
						return;
					}
				}
			}

			$loading.show();
			$btn.hide();
			ajaxCall('/pl/fileservice/video/exists', {
				'file-hash': hash
			}, {}, function (response) {
				if (response.exists) {
					self.fileUploaded(hash, hash);
					$input.val('');
					$.toast(window.tt('common', 'File uploaded successfully'), {type: "success"});

					if (self.options.onUploadComplete) {
						self.options.onUploadComplete(hash);
					}
				} else {
					$.toast(window.tt('common', 'File not found'), {type: "danger"});
				}
			}, function() {
				$loading.hide();
				$btn.show();
			});
		});

		return $content;
	},
    fileUploaded: function( hash, filename ) {
        var self = this;
        var date = new Date().toISOString().split('T')[0] + ' ' + new Date().toISOString().split('T')[1].slice(0, 8)
        var $fileEl = this.createFileEl( hash, false, filename, date)

		// Если такой уже был, удаляем его перед добавлением такого же
		var $existFileEl = self.getFileElByHash(hash);
		$existFileEl.remove();

        $fileEl.prependTo( this.filesEl );

        self.markFile( hash, this.options.folder, true );

        self.numberOfFiles = ++self.numberOfFiles
        self.filesNumber.text(self.numberOfFiles + ' ' + self.getTypeLabel(self.numberOfFiles))

        if ( this.options.owner.options.isMulti ) {
            self.selectFile( hash )
        }
    },
	getFileElByHash: function(hash) {
		return $('.' + this.getFileClass(hash), this.filesEl);
	},
	getFileKey: function(hash) {
		return hash.replace("\.", "");
	},
	getFileClass: function(hash) {
		return 'file-' + this.getFileKey(hash);
	},
    createFileEl: function( hash, inFavorites, filename, datetime ) {
        var $el = $('<div class="file-item"></div>')
        var self = this;
        self.hash = hash;

        filename = filename || hash
        $el.draggable({
            cursor: "move",
            cursorAt: { top: -12, left: -20 },
            helper: function(e) {
                return $("<div class='ui-widget-header'>" + filename + "</div>");
            },
            start: function(e) {
            },
            drag: function(e) {
				var dragger = $(this)
				var $hoverEl = $(e.toElement)

                if ($hoverEl.attr('class')) {
                	var classes = $hoverEl.attr('class')
                    var parentClasses = $($hoverEl.parentElement).attr('class')

                    if (classes.includes('custom-directory') && self.options.directoryId !== $hoverEl.data('id')) {
					}
                }
            },
            stop: function(e) {
                var dragger = $(this)
                var $hoverEl = $(e.toElement)

                if ($hoverEl.attr('class')) {
                    var classes = $hoverEl.attr('class')

                    if (classes.includes('custom-directory') && self.options.directoryId !== $hoverEl.data('id')) {
						self.moveFile(hash, $hoverEl.data('id'), $el)
                    }
                }
            }
        });

		var fileKey = self.getFileKey(hash);
		var fileClass = self.getFileClass(hash);
		$el.css('position', 'relative');
		$el.data('key', fileKey);
        $el.data('hash', hash)

		$el.addClass(fileClass);
		if (self.options.fileType === self.TYPE_VIDEO) {
			$el.addClass('video-preview');
		}
        /*if ( this.options.owner.isFileSelected( fileKey ) ) {
            $el.addClass("selected")
        }*/

        var $img = $('<img>')

		var src = self.isVideo(this.options.fileType)
			? getVideoThumbnailUrl(hash, 200, 150)
			: getThumbnailUrl(hash, 200, 200);
		$img.attr("src", src);
		$img.data('hash', hash);
        $img.appendTo($el)
        var $titles = $('<div data-filename="' + filename + '" contenteditable="false" class="titles-text" id="' +
			hash + '">' + filename + '</div>');

        $titles.appendTo($el);

        var $createDate = $('<div class="file-create-data">' + datetime + '</div>')
        $createDate.appendTo($el)

        var $bottomPanel = $('<div class="bottom-panel"></div>')
        $bottomPanel.appendTo($el)
        //$selectBtn = $('<button class="btn btn-select btn-primary">Выбрать</button>')
        //$selectBtn.appendTo( $el )

        var $cancelBtn = $('<button class="btn btn-cancel text-left btn-sm btn-link file-action"><span class="glyphicon glyphicon-trash"></span></button>')
		$cancelBtn.attr('title', window.tt('common', 'Delete'))
		$cancelBtn.appendTo($bottomPanel)

        var $downloadBtn = $('<button class="btn btn-link btn-download file-action"><span class="from-favorites glyphicon glyphicon-download-alt"></span></button>')
		$downloadBtn.attr('title', window.tt('common', 'Download'))
		$downloadBtn.appendTo($bottomPanel)
        self.downloadBtn = $downloadBtn

        var $cropBtn = $('<button class="btn btn-link btn-crop file-action"><span class="to-favorites glyphicon glyphicon-scissors"></span></button>');
        $cropBtn.appendTo($bottomPanel);
        self.cropBtn = $cropBtn;

		var $changeVideoPreviewBtn = '';
		if (this.options.fileType === this.TYPE_VIDEO) {
			$cropBtn.hide();

			$changeVideoPreviewBtn = $('<button class="btn btn-link btn-change-video-preview file-action"><span class="to-favorites glyphicon glyphicon-edit"></span></button>');
			$changeVideoPreviewBtn.attr('title', window.tt('common', 'Change cover'));
			$changeVideoPreviewBtn.appendTo($bottomPanel);
			self.setVideoPreviewBtn = $changeVideoPreviewBtn;
		}

        var $favBtn = $('<button class="btn btn-link btn-favorites file-action"><span class="to-favorites glyphicon glyphicon-star-empty"></span><span class="from-favorites glyphicon glyphicon-star"></span></button>')
		$favBtn.attr('title', window.tt('common', 'Add to favorites'));
		$favBtn.appendTo($bottomPanel)
        self.favBtn = $favBtn

		var $allowRenameBtn = $('<button class="btn btn-sm btn-link btn-allow-rename file-action"><span class="glyphicon glyphicon-pencil"></span></button>')
		$allowRenameBtn.attr('title', window.tt('common', 'Change file name'));
		$allowRenameBtn.appendTo($bottomPanel)
		self.allowRename = $allowRenameBtn


		var $applyRenameBtn = $('<button class="btn btn-sm btn-success-outline btn-apply-rename file-action"><span class="glyphicon glyphicon-ok"></span></button>')
		$applyRenameBtn.css('display', 'none')
		$applyRenameBtn.attr('title', window.tt('common', 'Apply changes'));
		$applyRenameBtn.appendTo($bottomPanel)
		self.applyRenameBtn = $applyRenameBtn

        var $moveFileBtn = $('<button class="btn btn-sm btn-link btn-move-file file-action"><span class="glyphicon glyphicon-copy"></span></button>')
		$moveFileBtn.attr('title', window.tt('common', 'Move to another folder'));
		$moveFileBtn.appendTo($bottomPanel)

        //$coverBtn = $('<button class="btn btn-link btn-cover hidden"><span class="glyphicon glyphicon-picture"></span></button>')
        //$coverBtn.appendTo( $el )

        $titles.on("keypress", function (e) {
            if (e.keyCode === 13) {
                e.preventDefault(e)
                var text = $titles.text().trim().replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');
                if (!text) {
                    $(this).text($(this).data('filename'));
					$.toast(window.tt('common', 'Incorrect file name'), {type: "danger"});
                } else {
                    self.renameFile(hash, text)
                    $titles.attr('contenteditable', 'false');
                    $titles.text(text);
					$.toast(window.tt('common', 'File name updated'), {type: "success"});
                    $applyRenameBtn.hide()
                    $allowRenameBtn.show()
                }
            }
        })

        $titles.focusout(function () {
            var text = $titles.text().trim().replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');
            if (!text) {
                $(this).text($(this).data('filename'));
				$.toast(window.tt('common', 'Incorrect file name'), {type: "danger"});
            } else {
                self.renameFile(hash, text)
                $titles.attr('contenteditable', 'false');
                $titles.text(text);
				$.toast(window.tt('common', 'File name updated'), {type: "success"});
                $applyRenameBtn.hide()
                $allowRenameBtn.show()
            }
        })

        if ( inFavorites ) {
            self.favBtn.addClass('in-favorites');
        }

		var handleButtons = function( hash, $el, filename, $titles, self ) {
            $favBtn = $el.find('.btn-favorites')
            $cancelBtn = $el.find('.btn-cancel')
            //$coverBtn = $el.find('.btn-cover')
			$allowRenameBtn = $el.find('.btn-allow-rename')
			$applyRenameBtn = $el.find('.btn-apply-rename')
			$moveFileBtn = $el.find('.btn-move-file')

			var $btnSelect = $el.find('img')

            $btnSelect.click( function() {
                self.selectFile( hash )
            })

            function addBtnHandler( btn, handler ) {
                btn.click( handler )
            }

            addBtnHandler( $favBtn, function() {
                $favBtn = $(this)
                var needPositive = ! $favBtn.hasClass("in-favorites");
                self.markFile( hash, "favorites", needPositive, function( needPositive ) {
                    if ( needPositive ) {
                        $favBtn.addClass('in-favorites')
                    }
                    else {
                        $favBtn.removeClass('in-favorites')
                    }
                })
            });

            addBtnHandler($cancelBtn, function() {
				if (confirm(window.tt('common', 'Are you sure?'))) {
                    self.markFile( hash, self.options.folder, false );
                    $(this).parents('.file-item').remove()
				}
            })

            addBtnHandler($downloadBtn, function() {
                window.open( getDownloadUrl( hash ) );
            })

			addBtnHandler($allowRenameBtn, function() {
				$allowRenameBtn = $(this)
				$allowRenameBtn.hide()
				$applyRenameBtn.show()

				$titles.attr('contenteditable', 'true').attr("tabindex",-1).focus();
			})

			addBtnHandler($applyRenameBtn, function() {
				$applyRenameBtn = $(this)
                var text = $titles.text().trim().replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');
                if (!text) {
                    $(this).text($(this).data('filename'));
					$.toast(window.tt('common', 'Incorrect file name'), {type: "danger"});
                } else {
                    self.renameFile(hash, text)
                    $titles.attr('contenteditable', 'false');
                    $titles.text(text);
					$.toast(window.tt('common', 'File name updated'), {type: "success"});
                    $applyRenameBtn.hide()
                    $allowRenameBtn.show()
                }
			})

            addBtnHandler($cropBtn, function () {
                var jcrop, data = {};

                var active = window.gcModalActive();
                active && active.hide();
                var modal = window.gcModalFactory.create({
                    onHide: function () {
                        jcrop.destroy();
                        active && active.show();
                    }
                });

                var fixCrop = function(c)
                {
                    // console.log('x = '+c.x);
                    // console.log('y = '+c.y);
                    // console.log('x2 = '+c.x2);
                    // console.log('y2 = '+c.y2);
                    // console.log('w = '+c.w);
                    // console.log('h = '+c.h);
                    data.crop = c;
                    data.image = {
                        w : modal.getContentEl().find('img').width(),
                        h : modal.getContentEl().find('img').height()
                    };
                    var $btn = modal.getModalEl().find('.btn-success');
                    if (c.w && c.h) {
                        $btn.removeAttr('disabled');
                    }
                    else {
                        $btn.attr('disabled', 'disabled');
                    }
                    // console.log(data);
                };


                var $imgToEdit = $('<img>');
                $imgToEdit.attr("src", getThumbnailUrl(hash, 550, ''));

                var $editContent = $('<div style="width: 550px;margin: 0 auto;">');
                $editContent.append($imgToEdit);
				var $saveEditImageBtn = $('<button class="btn btn-success" style="margin: 5px;" disabled>'
					+ window.tt('common', 'Save')
					+ '</button>'
				);
				var $cancelEditImageBtn = $('<button class="btn" style="margin: 5px;">'+window.tt('common', 'Cancel')+'</button>');

                $saveEditImageBtn.click(function () {
                    ajaxCall('/pl/fileservice/widget/user-crop', {
                        hash : hash,
                        data : data
                    }, {btn : $saveEditImageBtn}, function(response) {
                        modal.hide();
                        self.fileUploaded(response.hash, response.filename);
                    });
                });

                $cancelEditImageBtn.click(function () {
                    modal.hide();
                });
                var $editButtons = $('<div style="text-align: center">');
                $editButtons.append($saveEditImageBtn).append($cancelEditImageBtn);
                $editContent.append($editButtons);

                modal.getModalEl().find('.modal-dialog').css('max-width', '600px');
                modal.getContentEl().addClass("row-container");
				modal.setTitle(window.tt('common', 'Crop image'));
                modal.setContent($editContent);
                modal.getContentEl().find('img').Jcrop({
                    onChange: fixCrop,
                    onSelect: fixCrop
                }, function() {jcrop = this;});

                modal.show();
            });

            addBtnHandler($moveFileBtn, function (e) {
                var $existedIcon = $($moveFileBtn[0].parentElement).find('.move-directories')

                if ($existedIcon.length > 0) {
                    $existedIcon.remove()
					return
                }

                var directoriesFilteredByType = $(this).parents('.file-dialog-layout').find('span.custom-directory')

				var $directoriesSelectEl = $('<div class="move-directories"><select class="dir-select">'
					+ '<option value="0">'+window.tt('common', 'Select folder')+'</option>'
					+ '</select></div>'
				);
                var $selectEl = $directoriesSelectEl.find('.dir-select')

				$.each(directoriesFilteredByType, function (i, element) {
                    $selectEl.append('<option value="' +
						$(element).data('id') + '">' +
						$(element).text() + '</option>')
                })


                $directoriesSelectEl.css('display', 'none')
                $directoriesSelectEl.css('z-index', '1')
                $directoriesSelectEl.css('max-height', '100px')
                $directoriesSelectEl.css('overflow-y', 'auto')

                self.directoriesSelectEl = $directoriesSelectEl

                $selectEl.change(function () {
                    var selectedOption = $(this).val()
                    var hash = $($directoriesSelectEl[0].parentNode.parentNode).data('hash')
                    var fileEl = $($directoriesSelectEl[0].parentNode.parentNode)

                    self.moveFile(hash, selectedOption, fileEl)

                    $directoriesSelectEl.remove()
                })

                var $directoriesSelect = self.directoriesSelectEl

                $directoriesSelect.appendTo($($moveFileBtn[0].parentElement))

                $directoriesSelect.css({
                        'left': '170px',
						'display': 'block',
						'position': 'absolute'
				})

                $directoriesSelect.find('.dir-select').val(0)

                $directoriesSelect.focusout(function () {
                    $directoriesSelectEl.remove()
                })

            })

			if ($changeVideoPreviewBtn) {
				$changeVideoPreviewBtn.click(function() {
					window.gcSelectVideoFrame({
						hash: hash,
						callback: function (hash) {
							self.fileUploaded(hash);
						},
						overrideDefaultFolder: 'frames'
					});
				});
			}

            /*addBtnHandler($coverBtn, function() {
                if (confirm("Вы уверены?")) {
                    self.markFile( hash, "cover", true );
                }
            })*/
        }

        handleButtons( hash, $el, filename, $titles, self  )

		$titles.click(function () {
			$allowRenameBtn.hide()
			$applyRenameBtn.show()

			$(this).attr('contenteditable', 'true').attr("tabindex", -1).focus();
		})

        return $el;
    },
    markFile: function( hash, mark, positive, callback ) {
		var self = this
        var data = {
            hash: hash,
            mark: mark,
            positive: positive ? 1 : 0,
			fileType: self.options.fileType,
			forceFileType: self.options.forceFileType
        }

        if (mark !== 'favorites' && this.options.folderType === 'custom') {
            data.directory_id = this.options.directoryId;
            data.mark = 'custom';
        }

        if (!positive) {
            var newFileNumber = self.numberOfFiles - 1
            self.filesNumber.text(newFileNumber + ' ' + self.getTypeLabel(newFileNumber))
		}

        ajaxCall( "/pl/fileservice/widget/mark", data, {}, function() {
            if ( callback ) {
                callback( positive );
            }
        } )
    },
	renameFile: function(hash, filename, callback) {
		var data = {
			hash: hash,
			filename: filename,
			positive: 1,
		}

		ajaxCall("/pl/fileservice/widget/rename", data, {}, function() {
			if (callback) {
				callback();
			}
		})
	},
    setSelectedHash: function( selectedHash ) {
    	this.loadFiles( this.options.folder, this.filesEl, selectedHash )
    },
    loadFiles: function(mark, $toElement, selectedHash, substring) {
    	let key = mark + selectedHash;
    	if ( this.loading && this.loading == key ) {
    		return;
	    }
        var self = this;
        $toElement.empty();

        if ( this.options.folder != "recent" ) {
            selectedHash = null;
        }

        if (this.options.folderType === 'custom') {
            mark = this.options.folderType;
		}

        this.loading = key;

		var params = {
			mark: mark,
			selectedHash: selectedHash,
			fileType: this.options.fileType ? this.options.fileType : this.TYPE_IMAGE,
			directoryId: self.options.directoryId,
			orderBy: self.options.orderBy,
			extensions: self.options.extensions
		};

		ajaxCall( '/pl/fileservice/widget/get-by-mark', params, {}, function( response ) {
            var filesNumber = 0;

            for ( key in response.data.files ) {
                var file = response.data.files[key];

                if (substring && !file.filename.toLowerCase().includes(substring.toLowerCase())) {
					continue
                }

                if (!file.created_at) {
					file.created_at = new Date().toISOString().split('T')[0] + ' ' +
						new Date().toISOString().split('T')[1].slice(0, 8)
				}

                var $fileEl = self.createFileEl(file.hash, file.inFavorites, file.filename, file.created_at)
                $fileEl.appendTo( $toElement )
                filesNumber++
            }

			self.numberOfFiles = filesNumber
            self.filesNumber.text(filesNumber + ' ' + self.getTypeLabel(filesNumber))
            self.loading = null;
        } )
    },
	getTypeLabel: function(filesNumber) {
		var self = this
		var typeLabel;
		if (self.options.fileDialogLabel !== null) {
			typeLabel = self.options.fileDialogLabel;
		} else {
			switch (self.options.fileType) {
				case self.TYPE_VIDEO:
					typeLabel = window.tt('common', 'video')
					break;
				case self.TYPE_AUDIO:
					typeLabel = window.tt('common', 'audio')
					break;
				case self.TYPE_IMAGE:
					typeLabel = window.tt('common', 'image|images', filesNumber)
					break;
			}
		}

        return typeLabel
    },
    selectFile: function( hash ) {
        this.options.owner.fileSelected( hash )
    },
    init: function( selectedHash ) {
	    this.loadFiles(this.options.folder, this.filesEl, selectedHash, '')
    },
	checkNeedToRefresh: function() {
		var self = this;
		$('.file-item img', this.filesEl).each(function() {
			var $img = $(this);
			var hash = $img.data('hash');
			var src = self.isVideo(self.options.fileType)
				? getVideoThumbnailUrl(hash, 200, 150)
				: getThumbnailUrl(hash, 200, 200);
			if ($img.attr('src') !== src) {
				$img.attr('src', src);
			}
		});
	},
	numberCases: function(number, one, two, five) {
        const cases = [2, 0, 1, 1, 1, 2];
        const titles = [one, two, five];
        return titles[(number % 100 > 4 && number % 100 < 20) ? 2 : cases[(number % 10 < 5) ? number % 10 : 5]];
	},
	moveFile: function (hash, newDirectoryId, $el) {
		var self = this

        ajaxCall("/pl/fileservice/widget/move-file",
            {hash: hash, directory_id: newDirectoryId}, {}, function() {
                if (self.options.folderType === 'custom' && response.success) {
                    $el.fadeOut()
                    var newFileNumber = self.numberOfFiles - 1
                    self.filesNumber.text(newFileNumber + ' ' + self.getTypeLabel(newFileNumber))
                }
		})
    },
    markFileById: function(id, mark, positive, callback, type) {
        var self = this
        var data = {
            id: id,
            mark: mark,
            positive: positive ? 1 : 0,
			type: type,
			forceFileType: self.options.forceFileType
        }

        if (mark !== 'favorites' && this.options.folderType === 'custom') {
            data.directory_id = this.options.directoryId;
            data.mark = 'custom';
        }

        if (!positive) {
            var newFileNumber = self.numberOfFiles - 1
            self.filesNumber.text(newFileNumber + ' ' + self.getTypeLabel(newFileNumber))
        }

        ajaxCall( "/pl/fileservice/widget/mark-by-id", data, {}, function(response) {
            if (response.success) {
                var hash = response.hash;
                var filename = response.filename;

                var date = new Date().toISOString().split('T')[0] + ' ' + new Date().toISOString().split('T')[1].slice(0, 8)
                var $fileEl = self.createFileEl(hash, false, filename, date)

                // Если такой уже был, удаляем его перед добавлением такого же
                var $existFileEl = self.getFileElByHash(hash);
                $existFileEl.remove();

                $fileEl.prependTo(self.filesEl);

                self.numberOfFiles = ++self.numberOfFiles
                self.filesNumber.text(self.numberOfFiles + ' ' + self.getTypeLabel(self.numberOfFiles))

            }
        } )
    },
	isVideo: function(type) {
		return type === this.TYPE_VIDEO || type === this.TYPE_VIDEO_NOTE;
	}
    /*
    showFileSelected: function( fileKey, isSelected ) {
        var $files = this.filesEl.find( '.file-' + fileKey )
        if ( isSelected ) {
            $files.addClass( "selected" )
        }
        else {
            $files.removeClass( "selected" )
        }
    }*/

} );
