jQuery.widget('gc.gcVideoGrid', $.gc.gcFileSelectorFolder, {
	options: {
		mainHash: null,
		previewList: []
	},
	mapFrameHashToSrc: null,
	currentPreview: null,
	watermarkEnableInput: false,
	_create: function() {
		var $messageEl = $('<div></div>');
		this.messageEl = $messageEl;
		this.element.addClass("grid-content");
        this.element.css('display', 'block');
        this.element.append($messageEl);
		var that = this;
		ajaxCall('/pl/fileservice/video/info', {
			'file-hash': this.options.mainHash,
			'result-format': 'json'
		}, {crossDomain: true}, function (response) {
			if (response.videoHash !== null) {
				that.gridEnabled = response.gridEnabled;
				that.gridPosition = response.gridPosition;
				that.gridSize = response.gridSize;
				that.gridOffset = ((response.chunkPadSummator * response.chunkDuration) / 10).toFixed(0) * 10;
				that.chunkDuration = response.chunkDuration;
				that.chunkPadSummator = response.chunkPadSummator;
				that.pregeneratedViewers = response.pregeneratedViewers;
				that.viewersSize = response.viewersSize;
				that.dataSize = response.dataSize;
				that.viewersNumber = response.viewersNumber;
				that.viewersSize = response.viewersSize;
				that.isGoodQuality = response.isGoodQuality;
				that.hasVideoStream = response.hasVideoStream;

				that.element.append(that.generateHtml());
				that.filesEl = $('');
				that.filesEl.appendTo(that.element);

				if ( that.gridSizeSelect ) {
					var value = (that.gridSizeSelect[0].dataset['value']);
					that.gridSizeSelect[0].value = value ? value : 'middle';
				}

				if ( that.gridOffsetSelect ) {
					var offset = (that.gridOffsetSelect[0].dataset['value']);
					that.gridOffsetSelect[0].value = offset ? offset : '0';
				}

				if ( that.gridPregenerateSelect ) {
					var viewers = (that.gridPregenerateSelect[0].dataset['value']);
					that.gridPregenerateSelect[0].value = viewers ? viewers : '0';
				}

				that.onGridEnabled();
				that.gridStatusCheckbox[0].addEventListener('change', that.onGridEnabled.bind(that));

				if ( !that.rootEl ) {
					return;
				}

				that.submitBtn[0].addEventListener('click', that.onSubmitBtnClick.bind(that));
				that.gridPositions[0].addEventListener('click', that.onPositionDomClick.bind(that));
				that.angle = {
					'left-top': false, 'center-top': false, 'right-top': false,
					'left-middle': false, 'full-screen': false, 'right-middle': false,
					'left-bottom': false, 'center-bottom': false, 'right-bottom': false
				};

				that.initGrid();
				that.initSelected();
			} else {
				$messageEl.text(window.tt('common', 'Это видео еще не обработано'));
			}
		});
	},
	onSubmitBtnClick: function() {
		var gridStatus = this.gridStatusCheckbox[0].checked ? 1 : 0;
		var gridOffset = this.gridOffsetSelect[0].value;
		var gridPregenerate = this.gridPregenerateSelect[0].value;
		var gridSize = this.gridSizeSelect[0].value;
		var gridPositions = this.wpsInput[0].value;
		var that = this;

		ajaxCall('/pl/fileservice/video/grid', {
			'file-hash': this.options.mainHash,
			'grid-status' : gridStatus,
			'grid-size' : gridSize,
			'grid-positions' : gridPositions,
			'grid-offset' : parseInt((gridOffset / that.chunkDuration).toFixed(0)),
			'grid-pregenerate' : gridPregenerate,
			'result-format': 'json'
		}, {}, function (response) {
		});
	},
	init: function() {
	},
	initGrid: function() {
		var that = this;
		var init = /** @type {string} */ (this.rootEl[0].dataset['value']);
		init.split(' ').forEach(function(key) {
			if (key.trim() !== '') {
				that.angle[key] = true;
			}
		});
	},
	generateHtml: function() {
		var self = this;
		var hash = self.options.mainHash;

		var gridEnabled = this.gridEnabled;
		var gridSize = this.gridSize;
		var gridOffset = this.gridOffset;
		var gridPosition = this.gridPosition;
		var gridPregenerate = this.pregeneratedViewers;

		$gridStatusCheckbox = $('<input id="wm_chb" type="checkbox" {gridEnabled}>'.replace('{gridEnabled}', gridEnabled ? 'checked' : ''));

		$gridPregenerateSelect = $(
			'<select id="watermark-pregenerate" class="wss-list" data-value="{gridPregenerate}">'.replace('{gridPregenerate}', gridPregenerate) +
			'<option value="5">' + window.tt('common', '{n} зритель|{n} зрителя|{n} зрителей', 5) + ' (' + window.tt('common', 'по умолчанию') + ')' +'</option>' +
			'<option value="100">' + window.tt('common', '{n} зритель|{n} зрителя|{n} зрителей', 100) + '</option>' +
			'<option value="500">' + window.tt('common', '{n} зритель|{n} зрителя|{n} зрителей', 500) + '</option>' +
			'<option value="1000">' + window.tt('common', '{n} зритель|{n} зрителя|{n} зрителей', 1000) + '</option>' +
			'</select>'
		);
    $gridOffsetSelect = $(
      '<select id="watermark-offset" class="wss-list" data-value="{gridOffset}">'.replace('{gridOffset}', gridOffset) +
      '<option value="0">' + window.tt('common', 'Сразу') + ' (' + window.tt('common', 'по умолчанию') + ')' + '</option>' +
      '<option value="10">' + window.tt('common', 'С {n} секунды', 10) + '</option>' +
      '<option value="20">' + window.tt('common', 'С {n} секунды', 20) + '</option>' +
      '<option value="30">' + window.tt('common', 'С {n} секунды', 30) + '</option>' +
      '</select>'
    );
		$gridSizeSelect = $(
			'<select id="watermark-size" class="wss-list" data-value="{gridSize}">'.replace('{gridSize}', gridSize) +
			'<option value="small">' + window.tt('common', 'Маленький') + '</option>' +
			'<option value="middle">' + window.tt('common', 'Средний') + '</option>' +
			'<option value="big">' + window.tt('common', 'Большой') + '</option>' +
			'</select>'
		);
		$gridPositions = $(
			'<div id="wps-video-preview" class="wps-video-preview js--wps-video-preview">' +
				'<div class="wps-position" data-position="left-top"></div>' +
				'<div class="wps-position" data-position="center-top"></div>' +
				'<div class="wps-position" data-position="right-top"></div>' +
				'<div class="wps-position" data-position="left-middle"></div>' +
				'<div class="wps-position-without-border" data-position="full-screen">' +
					'<span class="inside-icon fa fa-arrows-alt fa-2x" data-position="full-screen"></span></div>' +
				'<div class="wps-position" data-position="right-middle"></div>' +
				'<div class="wps-position" data-position="left-bottom"></div>' +
				'<div class="wps-position" data-position="center-bottom"></div>' +
				'<div class="wps-position" data-position="right-bottom"></div>' +
			'</div>'
		);
		$wpsInput = $('<input id="wps-input-position" type="hidden" name="watermark_position">');

		$rootEl = $(
			'<div class="wps-root js--wps-root" data-value="{gridPosition}">'.replace('{gridPosition}', gridPosition) +
			'<div class="wps-label">' +
			window.tt('common', 'Выберите положения watermark-a. По умолчанию будет выбрана вся поверхность видео.') +
			'</div>'
		);
		$rootEl.append($gridPositions);
		$rootEl.append('</div>');

		$wssSizeList = $('<div class="wss-list-text grid-size" id="wss-list-text"></div>');
		$wssOffsetList = $('<div class="wss-list-text grid-offset" id="wss-list-text"></div>');
		$wssPregenerateList = $('<div class="wss-list-text grid-pregenerate" id="wss-list-text"></div>');

		$submitBtn = $(
			'<div id="uploadifive-undefined" class="uploadifive-button" style="height: 30px; line-height: 30px; overflow: hidden; position: relative; text-align: center; width: 120px;">'
			+ window.tt('common', 'Сохранить')
			+ '<input type="submit" style="font-size: 30px; opacity: 0; position: absolute; right: -3px; top: -3px; z-index: 999;">'
			+'</div>'
		);

		self.gridStatusCheckbox = $gridStatusCheckbox;
		self.gridSizeSelect = $gridSizeSelect;
		self.gridPositions = $gridPositions;
		self.gridOffsetSelect = $gridOffsetSelect;
		self.gridPregenerateSelect = $gridPregenerateSelect;
		self.rootEl = $rootEl;

		self.wssPregenerateList = $wssPregenerateList;
		self.wssOffsetList = $wssOffsetList;
		self.wssSizeList = $wssSizeList;

		self.wpsInput = $wpsInput;
		self.submitBtn = $submitBtn;

		var $content = $('<div class="wdb-root">');
		$content.append($gridStatusCheckbox);

		var $usersTitle = window.tt('common', '{n} пользователь|{n} пользователя|{n} пользователей', self.viewersNumber);

		var $goodQualityDisclaimer = self.isGoodQuality
			? ''
			: window.tt('common', 'Видеозащита применится только после полной подготовки видео, это может занять некоторое время')
			+ '.<br/>'
			+ window.tt('common', 'До окончания подготовки пользователи не смогут смотреть видео')
			+ '.<br/>';

		$content.append(
			'<label for="wm_chb">&nbsp;' + window.tt('common', 'Защитить видео с помощью watermark') + '</label>' +
			'<div class="text-muted">' +
			'<p class="text-danger"><b>' +
			window.tt('common', 'Включенная видеозащита увеличивает занимаемый размер видео в два раза') + '.<br/>' +
			/*'Вы можете удалить файл либо выключить видеозащиту, чтобы освободить дисковое пространство.<br/>' +
			'Сейчас видеозащита сгенерирована для ' +
			self.viewersNumber + ' ' + $usersTitle + ' и занимает '+
			self.viewersSize + ' ('+
			self.viewersNumber * 3 +'% от исходного объема ' +
			self.dataSize + ')<br/>' +
			'Занятое дисковое пространство: ' + window.usedSize + ' из ' + window.totalAllowedSize + ' (' + window.usedSizePercent +')</p><br/>' +*/
			'</p>' + $goodQualityDisclaimer +
			'<br/>' +
			window.tt('common', 'При включении этой опции в видео добавляется код, уникальный для каждого ученика') +
			'.<br/>' +
			window.tt('common', 'Подготовка такого видео к просмотру может занимать некоторое время (до 30 секунд)') +
			'<br/><br/>' +
			window.tt('common', 'Если материалы урока бесплатные для пользователей, то нет смысла их защищать') +
			'.</div></div>'
		);
		$content.append('<div class="wss-root">');
		$content.append($wpsInput);

		if(window.params_52) {
			$content.append(
				'<label for="watermark-pregenerate" class="wss-label">'
				+ window.tt('common', 'Предгенерация')
				+ ':</label>'
			);
			$content.append($gridPregenerateSelect);
			$content.append($wssPregenerateList);
			$content.append('<p>');
		}

		if(window.params_52 || window.iCanSelectGridOffset) {
			$content.append(
				'<label for="watermark-offset" class="wss-label">'
				+ window.tt('common', 'Начинать показ')
				+ ':</label>'
			);
			$content.append($gridOffsetSelect);
			$content.append($wssOffsetList);
			$content.append('<p>');
		}

		$content.append(
			'<label for="watermark-size" class="wss-label">'
			+ window.tt('common', 'Размер watermark-a')
			+ ':</label>'
		);
		$content.append($gridSizeSelect);
		$content.append($wssSizeList);
		$content.append('</div>');
		$content.append($rootEl);
		$content.append($submitBtn);

		return $content;
	},
	onGridEnabled: function() {
		if (!this.gridStatusCheckbox[0].checked) {
			this.wssPregenerateList[0].innerText = this.gridPregenerateSelect[0].options[this.gridPregenerateSelect[0].selectedIndex].innerText
			this.wssOffsetList[0].innerText = this.gridOffsetSelect[0].options[this.gridOffsetSelect[0].selectedIndex].innerText
			this.wssSizeList[0].innerText = this.gridSizeSelect[0].options[this.gridSizeSelect[0].selectedIndex].innerText
		}

		this.wssPregenerateList[0].classList.toggle('wss-list-text--disabled', this.gridStatusCheckbox[0].checked);
		this.wssOffsetList[0].classList.toggle('wss-list-text--disabled', this.gridStatusCheckbox[0].checked);
		this.wssSizeList[0].classList.toggle('wss-list-text--disabled', this.gridStatusCheckbox[0].checked);

		positionEnableClick = this.gridStatusCheckbox[0].checked;

		this.gridPregenerateSelect[0].classList.toggle('wss-list--disabled', !this.gridStatusCheckbox[0].checked);
		this.gridOffsetSelect[0].classList.toggle('wss-list--disabled', !this.gridStatusCheckbox[0].checked);
		this.gridSizeSelect[0].classList.toggle('wss-list--disabled', !this.gridStatusCheckbox[0].checked);
		this.gridPositions[0].classList.toggle('wps-video-preview--disabled', !this.gridStatusCheckbox[0].checked);
	},
	initSelected: function () {
		var that = this;
		var result = '';

		Object.keys(this.angle).map(function (key) {
			var elem = /** @type {HTMLElement} */ (that.rootEl[0].querySelector('[data-position="' + key + '"]'));
			if (elem) {
				if (that.angle[key]) {
					result += ' ' + key;
					if(key == 'full-screen')
						that.gridPositions.css('background', '#ffffff');
					else
						elem.classList.add('wps-position--selected');
				} else {
					if(key == 'full-screen')
						that.gridPositions.css('background', '#8e8e8e');
					else
						elem.classList.remove('wps-position--selected');
				}
			}
		});

		this.wpsInput[0].value = result;
	},
	onPositionDomClick: function (event) {
		if (!positionEnableClick) {
			return;
		}
		var elem = /** @type {HTMLElement} */ (event.target);
		var position = elem.dataset['position'];
		if (position === undefined) {
			return;
		}

		this.angle[position] = !this.angle[position];
		this.initSelected();
	}
} );
