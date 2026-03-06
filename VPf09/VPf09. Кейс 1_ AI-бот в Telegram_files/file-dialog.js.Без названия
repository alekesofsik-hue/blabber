window.gcSelectFiles = function( options ) {
    var type = ('type' in options) ? options.type : 'image';
    var fileDialogLabel = ('fileDialogLabel' in options) ? options.fileDialogLabel : null;

    if (fileDialogLabel !== null) {
        type = fileDialogLabel;
    }
    if (!window.gcFileSelectEl) {
        window.gcFileSelectEl = {};
    }
    if (!(type in window.gcFileSelectEl)) {
        window.gcFileSelectEl[type] = $('<div class="gc-file-dialog"></div>');
        window.gcFileSelectEl[type].appendTo(window.body);
        window.gcFileSelectEl[type].gcFileSelector(options);
    }
    //window.gcFileSelectEl.gcFileSelector( 'setIsMulti', isMulti )
    window.gcFileSelectEl[type].gcFileSelector('selectFile', options);
};

jQuery.widget( 'gc.gcFileSelector', {
	TYPE_IMAGE: 'image',
	TYPE_VIDEO: 'video',
    TYPE_AUDIO: 'audio',
    options: {
        isMulti: null,
		callback: null,
		type: this.TYPE_IMAGE,
        overrideDefaultFolder: '',
		defaultFolder: "recent",
		accept: '',
        isShowHint: false,
        fileDialogLabel: null,
        extensions: null,
        forceFileType: null
    },
    settingItems: ['frames', 'subtitles', 'grids', 'statistics'],
	currentFolder: null,
    currentFolderWidget: null,
	folders: null,
    actions: null,
    directories: {},
    modal: null,
	previousModal: null,
    _create: function () {
        this.options.type = !this.options.type || this.options.type === undefined
            ? this.TYPE_IMAGE
            : this.options.type;

		this.modal = this.createModal();
		this.modal.getModalEl().addClass('file-dialog-modal')
        this.modal.getModalEl().css('overflow-y', 'auto')
        this.modal.setContent("")
        this.element.appendTo( this.modal.getContentEl() )

		this.createFolders();

        this.createActions();
        this.createMainStructure();
        this.loadDirectories();

        //his.addAccordionEventListeners();

        //this.modal.setTitle("Выбор файла")
        this.modal.getBodyEl().addClass("file-dialog-modal-content")

        if(this.options.overrideDefaultFolder !== '') {
            this.options.defaultFolder = this.options.overrideDefaultFolder;
        }
		this.selectFolder(this.options.defaultFolder, false);
    },
	createModal: function() {
		this.detectPreviousActiveModal();
		// Тут уже срабатывает установка активной модалки, потому до этого имеет смысл получить текущую активную
		return window.gcModalFactory.create();
	},
	createFolders: function() {
		if (!this.folders) {
		    var mainLabel = '';
		    var mainIcon = '';

		    if (this.options.type === this.TYPE_VIDEO) {
                mainLabel = window.tt('common', 'Video');
                mainIcon = 'glyphicon glyphicon-facetime-video';
            } else if (this.options.type === this.TYPE_AUDIO) {
                mainLabel = window.tt('common', 'Audio');
                mainIcon = 'glyphicon glyphicon-volume-up';
            } else {
                mainLabel = window.tt('common', 'Images');
                mainIcon = 'glyphicon glyphicon-camera';
            }

			this.folders = {
				/*my: {
					label: mainLabel,
					icon: mainIcon,
					widget: 'gcFileSelectorFolder'
				},*/
				recent: {
					label: window.tt('common', 'Recent'),
					icon: "glyphicon glyphicon-time",
					widget: 'gcFileSelectorFolder'
				},
				favorites: {
					label: window.tt('common', 'Favorites'),
					icon: "glyphicon glyphicon-star",
					widget: 'gcFileSelectorFolder'
				}
			};

			if (this.options.type !== this.TYPE_VIDEO && this.options.type !== this.TYPE_AUDIO) {
				this.folders = Object.assign({}, this.folders, {
					cover: {
						label: window.tt('common', 'Covers'),
						icon: "glyphicon glyphicon-picture",
						widget: 'gcFileSelectorFolder'
					},
					// pixabay: {
					// 	label: window.tt('common', 'Photobank'),
					// 	icon: "glyphicon glyphicon-globe",
					// 	widget: 'gcFilePixabayFolder'
					// }
				});
			}

			if ( this.options.withIcons ) {
				this.folders = Object.assign({}, {
					icons: {
						label: window.tt('common', 'Icons'),
						icon: "fa fa-check",
						widget: 'gcIconForImageSelector'
					},
					emoji: {
						label: "Emoji",
						icon: "fa fa-smile",
						widget: 'gcEmojiForImageSelector'
					}
				}, this.folders )
			}
		}
	},
    createActions: function() {
        if (!this.actions) {
            var mainLabel = '';

            if (this.options.fileDialogLabel) {
                mainLabel = window.tt('common', this.options.fileDialogLabel);
            } else {
                if (this.options.type === this.TYPE_VIDEO) {
                    mainLabel = window.tt('common', 'video');
                } else if (this.options.type === this.TYPE_AUDIO) {
                    mainLabel = window.tt('common', 'audio');
                } else if (this.options.type === this.TYPE_RECORD) {
                    mainLabel = window.tt('common', 'audio');
                } else {
                    mainLabel = window.tt('common', 'image');
                }
            }

            this.actions = {
                upload: {
                    label: "+ " + window.tt('common', 'Add') + " " + mainLabel,
                    icon: "glyphicon glyphicon-file",
                    widget: 'gcFileUploader'
                },
            };

            // В конструкторе уроков/страниц и т.п. в блоках "видео", и блок "слайдер видео" вывести надпись:
            if (this.options.type === this.TYPE_VIDEO && this.options.isShowHint) {
                this.actions.upload.hint = window.tt('common', 'Видео будет модифицировано для просмотра на разных устройствах');
            }

            if (this.options.type === this.TYPE_VIDEO && window.videoLinkFeatureUsed === 1) {
                this.actions.uploadLinks = {
                    label: "+ " + window.tt('common', 'Add link') + " " + mainLabel,
                    icon: "glyphicon glyphicon-file",
                    widget: 'gcFileUploader'
                };
            }

            this.actions.addById = {
                label: window.tt('common', 'Add by id'),
                icon: "glyphicon glyphicon-file",
                widget: 'gcFileUploader'
            }
        }
    },
    selectFile: function( options ) {

	    if (this.currentFolder && this.currentFolder.widgetEl) {
			var folder = this.currentFolder;

		    if( options.iconParams ) {
			    folder.widgetEl.data( 'iconParams', options.iconParams )
		    }
			folder.widgetEl[folder.widget]('checkNeedToRefresh');
		}

        this.options = options;

        if ( options.isMulti ) {
            this.element.addClass( "multi-select-mode" );
        }
        else {
            this.element.removeClass( "multi-select-mode" );
        }
        this.showMultiStat();

        var active = window.gcModalActive();
        if (active && !active.isActive()) {
            active = null;
        }
        this.previousModal = active;
        this.modal.show();

        this.selectedFilesEl.empty();

        if ( this.options.selectedHash && this.folders['recent'].widgetEl ) {
            this.folders['recent'].widgetEl.gcFileSelectorFolder( 'setSelectedHash', this.options.selectedHash );
        }
	    //if ( this.options.selectedHash && this.folders['my'].widgetEl ) {
		//    this.folders['my'].widgetEl.gcFileSelectorFolder( 'setSelectedHash', this.options.selectedHash );
	    //}

        if ( this.options.isMulti && this.options.selected ) {
            for ( key in this.options.selected ) {
                var item = this.options.selected[key]
                if ( item.hash ) {
                    this.addSelectedFileEl( item.hash, item.caption );
                }
            }
        }
    },
	detectPreviousActiveModal: function() {
		var active = window.gcModalActive();
		if (active && !active.isActive()) {
			active = null;
		}
		// При создании модалки она уже установилась активной, на этот случай сохраняем предыдущее значение,
		// кторое записали как раз перед созданием
		if (!active || !this.modal || active.getId() !== this.modal.getId()) {
			this.previousModal = active;
		}

		return this.previousModal;
	},
    showMultiStat: function() {
        var self = this;

        if ( ! this.options.isMulti ) {
            return false;
        }

        var selectedFiles = self.selectedFilesEl.find('.selected-file-item')

		self.detailEl.find('.selected-info').html(
			window.tt('common', 'images selected')
			+ ": <b>" + selectedFiles.length + "</b>"
		);
    },


    createMainStructure: function() {
        var self = this;

        var storageUsagePercent = parseInt(window.storage_usage_percent)
        var usedStorageSize = self.formatBytes(window.used_storage_size ? parseInt(window.used_storage_size) : 0)
        var maxStorageSize = self.formatBytes(window.max_storage_size ? parseInt(window.max_storage_size) : 0)

        $layout = $('<div class="file-dialog-layout">' +
            '<div class="file-dialog-menu">' +
                '<div class="file-dialog-action-selector"></div>' +
                '<div class="file-dialog-delimiter"><hr></div>' +
                '<div class="file-dialog-folder-selector"></div>' +
                '<div class="file-dialog-size-progress">' +
                    '<div class="progress">' +
                        '<div class="progress-bar progress-bar-danger" role="progressbar" aria-valuenow="' +
                            storageUsagePercent+'" ' + 'aria-valuemin="0" aria-valuemax="100" style="width:' +
                            storageUsagePercent+ '%">' +
                        '</div>' +
                    '</div>' +
                    '<div class="progress-text">' + window.tt('common', 'Used') + '<br>' +
						usedStorageSize + ' ' + window.tt('common', 'from2') + ' ' +
                        maxStorageSize + '</div>' +
                '</div>' +
            '</div>' +
            '<div class="file-dialog-content"></div></div>')
        $layout.appendTo( this.element )

        self.actionSelectorEl = $actions = $layout.find('.file-dialog-action-selector')
        self.folderSelectorEl = $folders = $layout.find('.file-dialog-folder-selector')

        self.contentEl = $layout.find('.file-dialog-content')

		self.detailEl = $('<div class="file-dialog-detail"> <div class="info-div"><button class="btn-confirm btn btn-success">'
			+ window.tt('common', 'Confirm selection')
			+ '</button> <span class="selected-info"></span></div> <div class="selected-files-list"></div></div>'
		);
        self.detailEl.prependTo( this.element )

        self.selectedFilesEl = self.detailEl.find( '.selected-files-list' );

        self.btnConfirm = self.detailEl.find('.btn-confirm')
        self.btnConfirm.click( function() {
            var selectedFiles = []
            self.selectedFilesEl.find('.selected-file-item').each( function() {
                selectedFiles.push( {
                    hash: $(this).data('hash'),
                    caption: $(this).find('input').val()
                })
            })

            self.options.callback( selectedFiles );
            self.modal.hide();
        })

        if( self.isMobile() ) {
          self.folderSelectorEl.css('display', 'none')
          self.contentEl.css('margin-left', '0%')
        }

        for (key in this.actions) {
            var action = this.actions[key]
            $wrapper = $('<div></div>')

            if (key === 'upload') {
                $actionEl = $('<div class="folder-action"> ' + action.label + '</div>')

                $actionEl.addClass('folder-action-' + key)
                $actionEl.addClass('btn')
                $actionEl.addClass('btn-success')

                $actionEl.mouseenter(function () {
                    $(this).css('background-color', '#0cc57c');
                });

                $actionEl.mouseleave(function () {
                    $(this).css('background-color', '#199c68');
                });

                $actionEl.css('border', '1px solid')
                if (self.options.type === self.TYPE_AUDIO || self.options.type === self.TYPE_VIDEO) {
                    $actionEl.css('font-size', '12px')
                } else {
                    $actionEl.css('font-size', '9px')
                }
            } else if (key === 'uploadLinks') {
                $actionEl = $('<div class="folder-action"> ' + action.label + '</div>')

                $actionEl.addClass('folder-action-' + key);
                $actionEl.addClass('btn');
                $actionEl.addClass('btn-success');

                $actionEl.mouseenter(function () {
                    $(this).css('background-color', '#0cc57c');
                });

                $actionEl.mouseleave(function () {
                    $(this).css('background-color', '#199c68');
                });

                $actionEl.css('border', '1px solid');
                if (self.options.type === self.TYPE_AUDIO || self.options.type === self.TYPE_VIDEO) {
                    $actionEl.css('font-size', '12px');
                } else {
                    $actionEl.css('font-size', '9px');
                }
            } else {
                $actionEl = $('<div class="folder-action" style="text-align: center"><a href="#">' + action.label + '</a></div>')
            }

            $actionEl.data('action', key);
            $actionEl.appendTo($wrapper);

            if (action.hasOwnProperty('hint') && action.hint !== '') {
                $('<div style="color: #7B6A6A; font-size: 10px; margin: 10px 0">' + action.hint + '</div>').appendTo($wrapper);
            }

            if (!this.settingItems.includes(this.options.overrideDefaultFolder)) {
                $wrapper.appendTo($actions);
            }

            action.pickerEl = $actionEl;

            $actionEl.click(function (e) {
                self.selectAction($(this).data('action'), $(this), e);
            })
        }

        for (key in this.folders) {
            var folder = this.folders[key]

            $folderEl = $('<div class="folder-directory-picker" title="' +
                folder.label + '"> <span class="icon ' + folder.icon + '"></span>' + folder.label + '</div>')
            $folderEl.addClass('folder-picker-' + key)
            $folderEl.data('folder', key)
            $folderEl.appendTo($folders)

            folder.pickerEl = $folderEl;

            $folderEl.click( function() {
                self.selectFolder($(this).data('folder'), false)
            })
        }


        if (!this.settingItems.includes(this.options.overrideDefaultFolder)) {
            var $createFolderEl = $('<div class="folder-directory-picker" title="'+window.tt('common', 'Create folder')+'">' +
                '<span class="icon glyphicon glyphicon-plus-sign"></span>'+window.tt('common', 'Create folder')+'</div>');

            $createFolderEl.addClass('folder-picker-' + key)
            $createFolderEl.data('folder', 'create-folder')
            $createFolderEl.appendTo($folders)

            $createFolderEl.click(function(e) {
                self.selectAction('directory', $(this), e);
            })
        }
    },
    formatBytes: function (bytes, decimals = 2) {
        if (bytes === 0) return ('0 ' + window.tt('common', 'Byte'));

        const k = 1000;
        const dm = decimals < 0 ? 0 : decimals;
		const sizes = [
			window.tt('common', 'Byte'),
			window.tt('common', 'KB'),
			window.tt('common', 'MB'),
			window.tt('common', 'GB'),
			window.tt('common', 'TB')
		];

        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },
    addAccordionEventListeners: function () {
        var acc = document.getElementsByClassName("menu-accordion");
        var i;

        for (i = 0; i < acc.length; i++) {
            acc[i].addEventListener("click", function() {
                this.classList.toggle("dialogue-active");
                var panel = this.parentNode.querySelector('.menu-panel');
                if (panel.style.maxHeight) {
                    panel.style.maxHeight = null;
                    panel.style.padding = "0px";
                } else {
                    panel.style.maxHeight = "72%";
                }
            });
        }
    },
    selectFolder: function(folderName, fromDirectories = false) {
        var folder = fromDirectories ? this.directories[folderName] : this.folders[folderName]
        var self = this;

        folder.name = folderName;
        self.currentFolder = folder;
        if( !folder.widgetEl ) {
            var widgetEl = $('<div class="folder-content"></div>')
			var folderOptions = {
				owner: this,
				folder: folderName,
                label: folder.label,
				fileType: this.options.type,
                type: this.options.type,
				accept: this.options.accept,
                folderType: folder.type,
                directoryId: folder.directoryId,
                filesNumber: 0,
                contentEl: self.contentEl,
                directories: self.folderSelectorEl,
                directoriesList: self.directories,
                extensions: self.options.extensions,
                fileDialogLabel: self.options.fileDialogLabel,
                forceFileType: self.options.forceFileType
			};
			if ('options' in folder) {
				folderOptions = Object.assign({}, folderOptions, folder.options);
			}
            widgetEl[folder.widget](folderOptions);
            widgetEl.appendTo( self.contentEl );

            widgetEl.addClass("folder-" + folderName + "-content")

            folder.widgetEl = widgetEl;
        }

        if (!folder.pickerEl && fromDirectories) {
            folder.pickerEl = self.folderSelectorEl.find('.folder-directory-picker-' + folderName);
        }

        self.contentEl.find('.folder-content').hide();
        self.folderSelectorEl.find('.selected').removeClass("selected");

        folder.pickerEl.addClass("selected");
        folder.widgetEl.show();
        folder.widgetEl[folder.widget]('init', this.options.selectedHash, this.options.iconParams);
    },
    selectAction: function(actionName, $actionEl, event) {
        var action = this.actions[actionName]
        var self = this;
        var folder = self.currentFolder;
        var type = self.options.type || self.TYPE_IMAGE;
        var forceFileType = self.options.forceFileType

        self.currentAction = action;

        if (actionName === 'addById') {
            event.preventDefault();
            let fileId = prompt(window.tt('common', 'Enter file id'), '');

            if (!fileId) {
                return;
            }

            fileId = fileId.replace(/[^0-9]/g,'');

            if (!fileId) {
                $.toast(window.tt('common', 'Incorrect id'), {type: "danger"});
            } else {
                folder.widgetEl[folder.widget]('markFileById', fileId, folder.name, true, null, type, forceFileType);
            }
        }

        if (actionName === 'uploadLinks') {
            event.preventDefault();
            let fileLink = prompt(window.tt('common', 'Enter video link'), '');

            if (!fileLink) {
                return;
            }

            //проверять гугл \ яндекс?
            var urlPattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
                '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
                '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
                '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
                '(\\?[;&a-z\\d\\!%_.~+=-]*)?'+ // query string
                '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
            if (!urlPattern.test(fileLink)) {
                $.toast(window.tt('common', 'Указана ссылка не верного формата'), {type: "danger"});
                return;
            }

            ajaxCall('/pl/fileservice/video/save-video-link', {'link': fileLink}, {}, function (response) {
                if (response.success) {
                    folder.widgetEl[folder.widget]('fileUploaded', response.hash);
                }
            }, function(response) {
                console.log('ccc', response)
            }, function(response) {
                console.log('eee', response)
            });
            return
        }

        if (actionName === 'upload') {
            $actionEl
                .parents('.file-dialog-layout')
                .find('.folder-' + self.currentFolder.name + '-content')
                .find('input[type=file]')
                .last()
                .click();
        }

        if (actionName === 'directory') {
            var directoryName = prompt(window.tt('common', 'Enter folder name'), window.tt('common', 'New folder'));

            if (directoryName === null) {
                return;
            }

            directoryName = directoryName.trim().replace(/[`!#$%&*()|+\-=?:'<>\{\}\[\]\\\/]/gi, '');

            directoryName = directoryName.trim() === '' ? window.tt('common', 'New folder') : directoryName.trim();
            self.createDirectory(directoryName);
        }
    },
    fileSelected: function( hash, folderCallback ) {

        var self = this;

        if ( this.options.isMulti ) {
            this.addSelectedFileEl( hash );
            this.showMultiStat();
        }
        else {
            this.valueSelected({ hash: hash } )
        }
    },
	valueSelected: function( value ) {
		if ( this.options.callback ) {
			if ( this.options.withIcons ) {
				this.options.callback(value)
			} else {
				this.options.callback(value.hash)
			}
		}
		this.modal.hide();
	},
    addSelectedFileEl: function( hash, caption ) {
        var self = this;

        var $el = $('<div class="selected-file-item"></div>')
        $el.appendTo( self.selectedFilesEl )

        self.selectedFilesEl.sortable({ axis: "x" })

        $el.data('hash', hash )

        $el.addClass('selected-file-' + hash.replace("\.", ""))

		var $img = $('<img>');
		var src = self.getSrcByHash(hash);
		$img.attr("src", src);
        $img.appendTo( $el )

        $unselectBtn = $("<span class='fa fa-trash btn-unselect'></span>")
        $unselectBtn.appendTo( $el )


        $unselectBtn.click( function() {
            $el.remove();
            self.showMultiStat();
        })

        var $descriptionBlock = $("<div class='description-block'> <a href='javascript:void(0)' class='set-description-link'>"
			+ window.tt('common', 'description')
			+ "</a> <input type='text' placeholder='" + window.tt('common','description') + "'></div>"
		);
        $descriptionBlock.appendTo( $el )

        $descriptionBlock.find( '.set-description-link' ).click( function() {
            $descriptionBlock.addClass('active')
            $descriptionBlock.find('input').focus();
        })

        $descriptionBlock.addClass( 'active' )
        if ( caption ) {
            $descriptionBlock.find( 'input' ).val( caption )
        }


        //$unselectBtn.click( function)( {})

    },
	getSrcByHash: function(hash) {
		return this.options.type === this.TYPE_VIDEO
			? getVideoThumbnailUrl(hash, 200, 200)
			: getThumbnailUrl(hash, 200, 200);
	},
    isMobile: function () {
        if( navigator.userAgent.match(/Android/i)
          || navigator.userAgent.match(/webOS/i)
          || navigator.userAgent.match(/iPhone/i)
          || navigator.userAgent.match(/iPad/i)
          || navigator.userAgent.match(/iPod/i)
          || navigator.userAgent.match(/BlackBerry/i)
          || navigator.userAgent.match(/Windows Phone/i)
        ){
          return true;
        }
        else {
          return false;
        }
    },
    createDirectory: function (directoryName) {
	    var self = this

        ajaxCall('/pl/fileservice/directory/create', {
            'name': directoryName,
            'type': self.options.type || self.TYPE_IMAGE,
        }, {}, function (response) {
            var key = 'folder_' + response.id;
            var $folders = self.folderSelectorEl

            self.directories[key] = {
                label: directoryName,
                icon: "glyphicon glyphicon-folder-open",
                widget: 'gcFileSelectorFolder',
                type: 'custom',
                directoryId: response.id
            }
            var folder = self.directories[key]

            var $folderEl = $('<div data-id="' +
                response.id + '" data-folder-id="' +
                key + '" class="folder-directory-picker custom-directory" title="' +
                folder.label + '"><span class="icon ' +
                folder.icon + '"></span><span class="custom-directory" data-id="' +
                response.id + '" id="folder-text-' +
                response.id + '">' +
                folder.label + '</span></div>')

            $folderEl.addClass('folder-directory-picker-' + key)
            $folderEl.data('folder', key)

            $folderEl.appendTo($folders)

            folder.pickerEl = $folderEl;

            $folderEl.click(function() {
                self.selectFolder($(this).data('folder'), true)
            })

            self.selectFolder($folderEl.data('folder'), true)
        });
    },
    loadDirectories: function () {
        var self = this

        ajaxCall('/pl/fileservice/directory/list', { type: self.options.type || self.TYPE_IMAGE },
            {async: false}, function (response) {
            if (response.success && response.directories.length > 0) {
                response.directories.forEach(element => self.directories['folder_' + element.id] = {
                    label: element.name,
                    icon: "glyphicon glyphicon-folder-open",
                    widget: 'gcFileSelectorFolder',
                    type: 'custom',
                    category: element.type,
                    directoryId: element.id
                });
            }

            self.fillDirectories();
        });
    },
    fillDirectories: function () {
	    var self = this;
	    var i = 0;

        if (!this.settingItems.includes(this.options.overrideDefaultFolder)) {
            for (dirKey in this.directories) {
                var directory = this.directories[dirKey]
                if (directory.category !== self.options.type) {
                    continue;
                }

                var $directoryEl = $('<div data-id="' + directory.directoryId + '" data-folder-id="' + dirKey + '" class="folder-directory-picker custom-directory" title="' +
                    directory.label + '"><span class="icon ' +
                    directory.icon + '"></span><span class="custom-directory" data-id="' + directory.directoryId + '" id="folder-text-' +
                    directory.directoryId + '">' +
                    directory.label + '</span></div>')

                $directoryEl.data('folder', dirKey)
                $directoryEl.css('display', 'none')
                $directoryEl.appendTo(self.folderSelectorEl)
                $directoryEl.delay((i++) * 100).fadeTo(1000, 1)
                directory.pickerEl = $directoryEl;
                $directoryEl.click(function () {
                    self.selectFolder($(this).data('folder'), true)
                })

                i++;
            }
        }
    }
} );
