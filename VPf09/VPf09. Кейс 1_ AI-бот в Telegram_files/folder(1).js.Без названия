jQuery.widget('gc.gcVideoFramesFolder', $.gc.gcFileSelectorFolder, {
	options: {
		mainHash: null,
		previewList: []
	},
	mapFrameHashToSrc: null,
	currentPreview: null,
	_create: function() {
		var self = this;

		this.element.addClass("folder");

		this.element.append(self.generateBeforeFolderPart());

		this.filesEl = $('<div class="files-list"></div>');
		this.filesEl.appendTo( this.element );
	},
	init: function() {
	},
	generateMapHashToSrc: function (previewList) {
		var self = this;
		var prefix = Math.floor(Math.random() * 1000) + 1;
		self.mapFrameHashToSrc = {};
		for (var i = 0; i < previewList.length; i++) {
			var frameHash = prefix + 'frame' + i;
			self.mapFrameHashToSrc[frameHash] = previewList[i];
		}
	},
	createFileEl: function(hash, inFavorites) {
		var $el = $('<div class="file-item"></div>');
		var self = this;
		self.hash = hash;

		var fileKey = self.getFileKey(hash);
		var fileClass = self.getFileClass(hash);
		$el.data('key', fileKey);
		$el.addClass(fileClass);
		$el.addClass('video-frame');

		var $img = $('<img>');
		var frameUrl = self.getSrcByHash(hash);
		$img.attr("src", frameUrl);
		$img.data('hash', hash);
		$img.appendTo($el);

		$img.click(function() {
			var service = window.vhs.createPreviewService(window.vhsRegion);
			service.changeVideoPreview(self.options.mainHash, frameUrl)
				.then(function(result){
					if (result) {
						self.selectFile(self.options.mainHash);
					} else {
						$.toast(window.tt('common', 'Ошибка загрузки файла'), {type: 'danger'});
					}
				})
				.catch(function(){
					$.toast(window.tt('common', 'Ошибка загрузки файла'), {type: 'danger'});
				});
		});

		return $el;
	},
	loadFiles: function(folderName, $toElement, selectedHash) {
		var key = folderName;
		if (this.loading && this.loading === key) {
			return;
		}
		var self = this;
		$toElement.empty();

		this.loading = key;

		for (var frameHash in self.mapFrameHashToSrc) {
			if (!self.mapFrameHashToSrc.hasOwnProperty(frameHash)) {
				continue;
			}
			var $frameEl = self.createFileEl(frameHash, false);
			$frameEl.appendTo($toElement);
		}
		self.loading = null;
	},
	selectFile: function(hash) {
		var self = this;

		$.toast(window.tt('common', 'Превью изменено'), {type: 'success'});
		updateThumbnailVersion(self.options.mainHash, Date.now());
		this.options.owner.fileSelected(hash);
	},
	getSrcByHash: function(hash) {
		return hash in this.mapFrameHashToSrc
			? this.mapFrameHashToSrc[hash]
			: '';
	},
	checkNeedToRefresh: function() {
		var self = this;
		if (this.currentPreview) {
			this.currentPreview.attr("src", getVideoThumbnailUrl(self.options.mainHash, 550, ''));
		}
	},
	generateBeforeFolderPart: function() {
		var self = this;
		var hash = self.options.mainHash;

		var $currentPreview = self.currentPreview = $('<img style="margin-bottom: 10px">');
		$currentPreview.attr("src", getVideoThumbnailUrl(hash, 550, ''));
		$currentPreview.css('width', 'auto').css('height', '360px').css('object-fit', 'contain');
		var $content = $('<div>');
		$content.css('padding-left', '19px');
		var $messageEl = $('<div></div>');
		var $loading = $('<img src="/public/img/loading.gif">');

		$content.append($currentPreview);
		$content.append($loading);
		$content.append($messageEl);

		// get video info

		if (self.options.skipGetInfo) {
			$loading.remove();
			self.generateMapHashToSrc(self.options.previewList);
			self.fillModalForReadyPreview($content, hash);
			self.loadFiles(self.options.folder, self.filesEl);
		} else {
			ajaxCall('/pl/fileservice/video/info', {
				'file-hash': hash,
				'result-format': 'json'
			}, {crossDomain: true}, function (response) {
				$loading.remove();
				if (response.status === 'done') {
					self.generateMapHashToSrc(response.previewList);
					self.fillModalForReadyPreview($content, hash);
					self.loadFiles(self.options.folder, self.filesEl);
				} else {
					$messageEl.text('Это видео еще не обработано');
				}
			});
		}

		return $content;
	},
	fillModalForReadyPreview: function($content, fileHash) {
		var self = this;

		// make elements

		var $uploader = $('<div class="uploader"></div>');
		var queueId = "queueVideoPreviewUpload";
		var $queue = $("<div id='" + queueId + "'></div>");

		// build content

		$uploader.appendTo($content);
		$queue.appendTo($content);

		// define action handlers

		var uploadUrl = '/fileservice/widget/upload?deprecated=13'
			+ '&secure=' + window.isEnabledSecureUpload
			+ '&host=' + window.fileserviceUploadHost;

		var uploadifiveParams = {
			auto: true,
			buttonText: window.tt('common', 'Загрузить превью'),
			width: 140,
			id: "videoPreviewUpload" + fileHash,
			queueID: queueId,
			dnd: false,
			removeCompleted: true,
			multi: false,
			fileSizeLimit: self.options.fileSizeLimit,
			uploadScript: uploadUrl,
			formData: {fullAnswer: true},
			onUploadError: function(file, errorCode, errorMsg) {
				$.toast(window.tt('common', 'Ошибка загрузки файла'), {type: 'danger'});
			},
			onUploadComplete: function(e, res) {
				res = JSON.parse(res);
				var service = window.vhs.createPreviewService(window.vhsRegion);
				service.changeVideoPreviewForHash(fileHash, res.hash)
					.then(function(result){
						if (result) {
							self.selectFile(fileHash);
						} else {
							$.toast(window.tt('common', 'Ошибка загрузки файла'), {type: 'danger'});
						}
					})
					.catch(function(){
						$.toast(window.tt('common', 'Ошибка загрузки файла'), {type: 'danger'});
					});
			}
		};

		// Потому что fileType параметр uploadifive как-то не так работает.
		// При указании video/* кучу видео форматов не позволяет выбрать
		// Если перечислить конкретные расширения файлов (или mime-type'ы), то тоже не все их воспринимает
		uploadifiveParams.onInit = function(filesToUpload, settings) {
			if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
				if (!settings) {
					settings = {}
				}
				getUploadifySecretLink(filesToUpload, settings);
			}

			var $fileInput = $('input[type=file]', $content);
			$fileInput.attr('accept', '.png, .jpg, .jpeg');
		};
		// При добавлении очередного файла создаются еще input'ы и по этому событию их можно обработать
		uploadifiveParams.onUpload = uploadifiveParams.onInit;

		setTimeout(function() {
			$uploader.uploadifive(uploadifiveParams);
		}, 100);
	},
	// one of previewHash and previewUrl is null
	//VG: remove todo?
	changeVideoPreview: function(fileHash, previewHash, previewUrl) {
		var self = this;
		var params = {
			'file-hash': fileHash
		};
		var previewParamProvided = true;
		if (previewHash) {
			params = Object.assign({}, params, {'preview-hash': previewHash});
		} else if (previewUrl) {
			params = Object.assign({}, params, {'preview-url': previewUrl});
		} else {
			previewParamProvided = false;
			console.log('Preview param is not provided');
		}
		if (previewParamProvided) {
			ajaxCall('/pl/fileservice/video/change-preview', params, {}, function() {
				self.selectFile(fileHash);
			});
		}
	}
} );
