jQuery.widget('gc.gcVideoSubtitles', $.gc.gcFileSelectorFolder, {
	options: {
		mainHash: null,
        previewList: [],
		autoGenerateSubtitlesSectionEnabled: window.autoGenerateSubtitlesSectionEnabled !== false
    },
	currentPreview: null,
	_create: function() {
		var self = this;

		this.element.addClass("folder");
        this.element.css('display', 'inline-block');
		this.element.append(self.generateBeforeFolderPart());

		this.filesEl = $('<div class="files-list"></div>');
		this.filesEl.appendTo( this.element );
	},
	init: function() {
	},
	loadSubtitlesLink: function(subtitlesUrl, $content) {
		var self = this;
		var $subtitles = self.subtitles;

		$subtitles.attr("href", subtitlesUrl);
		$subtitles.attr("target", "_blank");
		$subtitles.css('font-size', 'x-large');

		$content.prepend($subtitles);
	},
	selectFile: function(hash) {
		var self = this;

		$.toast(Yii.t('common', 'Субтитры изменены'), {type: "success"});
		this.options.owner.fileSelected(hash);
	},
	generateBeforeFolderPart: function() {
		var self = this;
		var hash = self.options.mainHash;

		var $content = $('<div style="width: 550px">');
		var $messageEl = $('<div></div>');
		var $loading = $('<img src="/public/img/loading.gif">');
		var $subtitles = self.subtitles = $('<a>' + Yii.t('common', 'Текущие субтитры') + '</a>');

		$content.append($loading);
		$content.append($messageEl);

		// get video info
		ajaxCall('/pl/fileservice/video/info', {
			'file-hash': hash,
			'result-format': 'json'
		}, {crossDomain: true}, function (response) {
			$loading.remove();
			if (response.status === 'done') {
				self.fillModalForReadyPreview($content, hash, response.subtitlesUrl, response);
			} else {
				$messageEl.text(Yii.t('common', 'Это видео еще не обработано'));
			}
		});

		return $content;
	},
	fillModalForReadyPreview: function($content, fileHash, subtitlesUrl, response) {
		var self = this;

		var $uploader = $('<div class="uploader"></div>');
		var queueId = "queueVideoSubtitlesUpload";
		var $queue = $("<div id='" + queueId + "'></div>");
        var $generateBtn = $('<div id="uploadifive-undefined" class="uploadifive-button" style="height: 30px; line-height: 30px; overflow: hidden; position: relative; text-align: center; width: 120px;">' + Yii.t('common', 'Сгенерировать') + '<input type="submit" style="font-size: 30px; opacity: 0; position: absolute; right: -3px; top: -3px; z-index: 999;"></div>');
        var $saveSettingsBtn = $('<div id="uploadifive-undefined" class="uploadifive-button" style="height: 30px; line-height: 30px; overflow: hidden; position: relative; text-align: center; width: 120px;">' + Yii.t('common', 'Сохранить') + '<input type="submit" style="font-size: 30px; opacity: 0; position: absolute; right: -3px; top: -3px; z-index: 999;"></div>');

        var $subtitles = self.subtitles;
		var isSubtitlesAutoshow = response.isSubtitlesAutoshow;

		if (!response.hasSubtitles) {
			/*
			var interval = setInterval(function() {
				self.subtitles.remove();

				ajaxCall('/pl/fileservice/video/get-subtitles-status', {'file-hash': fileHash}, {}, function(response) {
					if (response.isDone) {
						$subtitles.attr("href", subtitlesUrl);
						$subtitles.attr("target", "_blank");
						$subtitles.css('font-size', 'x-large');

						$content.prepend($subtitles);

						clearInterval(interval);
					} else {
						$.toast("Cубтитры обрабатываются..." + response.progress + "%", {type: "success" , hideAfter: false});
					}
				});
			}, 5000);
			*/
		} else {
            $subtitles.attr("href", subtitlesUrl);
            $subtitles.attr("target", "_blank");
            $subtitles.css('font-size', 'large');

            $content.prepend($subtitles);
        }

        var $progressbarWrapper = $('<div class="progress md-progress" data-label="">');
        var $progressbar = $('<div class="progress-bar" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">' +
			'<span class="show" style="position:absolute;display:block;width: 100%;color: black;">Подождите, субтитры обрабатываются...</span>' +
			'</div>');
        self.progressbar = $progressbar;
        self.progressbarWrapper = $progressbarWrapper;

        $progressbarWrapper.css('display', 'none');
        $progressbarWrapper.append($progressbar);

        var statusDisclaimerTranslate = Yii.t('common', 'При включенном автопоказе у зрителя при воспроизведении видео автоматически включатся субтитры.');
        var $statusDisclaimer = $('<span><b></b>' + statusDisclaimerTranslate + '</span><p>');
        var $ccStatusCheckbox = $('<input id="wm_chb" type="checkbox" {ccEnabled}>'.replace('{ccEnabled}', isSubtitlesAutoshow ? 'checked' : ''));
        var $checkboxLabel = $('<label for="wm_chb">&nbsp;' + Yii.t('common', 'Показывать субтитры сразу') + '</label>')

		self.autoshowStatusCheckbox = $ccStatusCheckbox

        $content.append($statusDisclaimer);
        $ccStatusCheckbox.appendTo($content);
        $content.append($checkboxLabel);

        $('<p>').appendTo($content);
        $saveSettingsBtn.appendTo($content);

        $('<hr>').appendTo($content);
        var autosubtitlesDisclaimerTranslate1 = Yii.t('common', 'Генерация автосубтитров с помощью сервиса распознавания речи.');
        var autosubtitlesDisclaimerTranslate2 = Yii.t('common', 'После генерации отображение субтитров будет включено автоматически.');
        var autosubtitlesDisclaimerTranslate3 = Yii.t('common', 'Ограничение длительности: 4 часа.');

        var $autosubtitlesDisclaimer = $(
            '<span><b>' + autosubtitlesDisclaimerTranslate1 + ' '
            + autosubtitlesDisclaimerTranslate2 + ' ' +
            '<br>' + autosubtitlesDisclaimerTranslate3 + '</br></span><p>'
        );

		if (self.options.autoGenerateSubtitlesSectionEnabled) {
			$content.append($progressbarWrapper);
			$content.append($autosubtitlesDisclaimer);
			$generateBtn.appendTo($content);
			$('<hr>').appendTo($content);
		}

        var subtitlesUploadDisclaimerTranslate1 = Yii.t('common', 'Загрузка файла субтитров. Требуется формат');
        var subtitlesUploadDisclaimerTranslate2 = Yii.t('common', 'рекомендуемая кодировка');
        var $subtitlesUploadDisclaimer = $('<span><b>' + subtitlesUploadDisclaimerTranslate1 +
            ' .srt <br>(' + subtitlesUploadDisclaimerTranslate2 + ' UTF-8)</br></span><p>');

        $content.append($subtitlesUploadDisclaimer);
        $uploader.appendTo($content);
		$queue.appendTo($content);
		$generateBtn.click(function () {
			self.generateVideoSubtitles(fileHash, subtitlesUrl, $content);
		});

        $saveSettingsBtn.click(function () {
            self.saveSubtitlesSettings(fileHash);
        });
		// define action handlers

		var uploadUrl = '/fileservice/widget/upload?deprecated=14'
			+ '&secure=' + window.isEnabledSecureUpload
			+ '&host=' + window.fileserviceUploadHost;

		var uploadifiveParams = {
			auto: true,
			buttonText: Yii.t('common', 'Загрузить субтитры'),
			width: 120,
			id: "videoSubtitlesUpload" + fileHash,
			queueID: queueId,
			dnd: false,
			removeCompleted: true,
			multi: false,
			fileSizeLimit: self.options.fileSizeLimit,
			uploadScript: uploadUrl,
			formData: {fullAnswer: true},
			onUploadError: function(file, errorCode, errorMsg) {
				$.toast(Yii.t('common', 'Ошибка загрузки файла'), {type: "danger"});
			},
			onUploadComplete: function(e, res) {
				res = JSON.parse(res);
				self.changeVideoSubtitles(fileHash, res.hash, subtitlesUrl, $content);
			}
		};

		uploadifiveParams.onInit = function(filesToUpload, settings) {
			if (window.isEnabledSecureUpload && window.fileserviceUploadHost) {
				getUploadifySecretLink(filesToUpload, settings);
			}

			var $fileInput = $('input[type=file]', $content);
			$fileInput.attr('accept', '.srt');
		};
		// При добавлении очередного файла создаются еще input'ы и по этому событию их можно обработать
		uploadifiveParams.onUpload = uploadifiveParams.onInit;

		setTimeout(function() {
			$uploader.uploadifive(uploadifiveParams);
		}, 500);
	},
	// one of previewHash and previewUrl is null
	changeVideoSubtitles: function(fileHash, subtitlesHash, subtitlesUrl, $content) {
		var self = this;
		var params = {
			'file-hash': fileHash
		};
		var previewParamProvided = true;
		if (subtitlesHash) {
			params = Object.assign({}, params, {'subtitles-hash': subtitlesHash});
		} else if (subtitlesUrl) {
			params = Object.assign({}, params, {'subtitles-url': subtitlesUrl});
		} else {
			previewParamProvided = false;
			console.log('Preview param is not provided');
		}
		if (previewParamProvided) {
			$.toast(window.tt('common', 'Подождите, субтитры обрабатываются') + '...', {
				type: 'success',
				hideAfter: false
			});

			var interval = setInterval(function() {
				var $subtitles = self.subtitles;
				self.subtitles.remove();

				ajaxCall('/pl/fileservice/video/subtitles-ready', params, {
					crossDomain: true,
					suppressNotify: true
				}, function (response) {
					if (response.success) {
						if (response.message && response.message.length > 0) {
							$.toast(window.tt('common', response.message), {type: 'success'});
						}
						ajaxCall('/pl/fileservice/video/change-subtitles', params, {
							crossDomain: true,
							suppressNotify: true
						}, function (response) {
							if (response && response.success && response.message && response.message.length > 0) {
								$.toast(window.tt('common', response.message), {type: 'success'});
							}
							$subtitles.attr("href", subtitlesUrl);
							$subtitles.attr("target", "_blank");
							$subtitles.css('font-size', 'x-large');

							$content.prepend($subtitles);
							self.selectFile(subtitlesHash);

							clearInterval(interval);
						});
					}
				});
			}, 5000);
		}
	},
	generateVideoSubtitles: function(fileHash, subtitlesUrl, $content) {
		var self = this;
		var params = {
			'file-hash': fileHash
		};

		$.toast(window.tt('common', 'Подождите, субтитры обрабатываются') + '...', {type: "success", hideAfter: false});

		ajaxCall('/pl/fileservice/video/generate-subtitles', params, {
			crossDomain: true,
			suppressNotify: true
		}, function (response) {
			if (response && response.success && response.message && response.message.length > 0) {
				$.toast(window.tt('common', response.message), {type: 'success'});
			}
		});

		var interval = setInterval(function() {
			var $subtitles = self.subtitles;
			var $progressbar = self.progressbar;
            var $progressbarWrapper = self.progressbarWrapper;

            $progressbarWrapper.css('display', 'block');
            $progressbarWrapper.css('position', 'relative');
			self.subtitles.remove();

			ajaxCall('/pl/fileservice/video/get-subtitles-status', params, {
				crossDomain: true,
				suppressNotify: true
			}, function (response) {
				if (response.isDone) {
                    if (response.status === 'success') {
						if (response.message && response.message.length > 0) {
							$.toast(window.tt('common', response.message), {type: "success"});
						}
                        $subtitles.attr("href", subtitlesUrl);
                        $subtitles.attr("target", "_blank");
                        $subtitles.css('font-size', 'x-large');

                        $content.prepend($subtitles);

                        self.selectFile(fileHash);

                        clearInterval(interval);
					} else {
						$subtitles = $('<h6>' + window.tt('common', 'Ошибка выполнения генерации') + '</h6>');
                        $content.prepend($subtitles);

                        clearInterval(interval);
					}
				} else {
					if (response.message && response.message.length > 0) {
						$.toast(window.tt('common', response.message), {type: 'success'});
					}
                    $progressbar.css('width', response.progress + '%');
                    $progressbar.attr('aria-valuenow', response.progress);
				}
			});

		}, 4000);
	},
    saveSubtitlesSettings: function(fileHash) {
        var self = this;
        var params = {
            'file-hash': fileHash,
			'autoshow-status': self.autoshowStatusCheckbox[0].checked ? 1 : 0,
        };

		$.toast(window.tt('common', 'Сохранение настроек субтитров') + '...', {type: "success", hideAfter: false});

		ajaxCall('/pl/fileservice/video/autoshow-subtitles-status', params, {
			crossDomain: true,
			suppressNotify: true
		}, function (response) {
			if (response && response.success && response.message && response.message.length > 0) {
				$.toast(window.tt('common', response.message), {type: 'success'});
			}
		});
    }
} );
