window.gcSelectVideoFrame = function(options) {
	var hash = options.hash;
	window.gcVideoFrameSelectEl = {};

	if (!(hash in window.gcVideoFrameSelectEl)) {
		window.gcVideoFrameSelectEl[hash] = $('<div class="gc-file-dialog"></div>');
		window.gcVideoFrameSelectEl[hash].appendTo(window.body);
		window.gcVideoFrameSelectEl[hash].gcVideoFrameSelector(options);
	}
	window.gcVideoFrameSelectEl[hash].gcVideoFrameSelector('selectFile', options);
};

jQuery.widget('gc.gcVideoFrameSelector', $.gc.gcFileSelector, {
	options: {
		isMulti: null,
		callback: null,
		accept: '',
		// hash файла (видео), с кадрами которого работаем
		hash: null,
		overrideDefaultFolder: '',
		skipGetInfo: false,
		previewList: [],
	},
	defaultFolder: "frames",
	previousModal: null,
	createModal: function() {
		var self = this;

		if(self.options.overrideDefaultFolder !== '') {
			self.defaultFolder = self.options.overrideDefaultFolder;
		}

		this.detectPreviousActiveModal();
		this.previousModal && this.previousModal.hide()
        var previousModal = this.previousModal

		// Тут уже срабатывает установка активной модалки, потому до этого имеет смысл получить текущую активную
		return window.gcModalFactory.create({
			onShow: function() {
				if (self.folders && self.defaultFolder in self.folders) {
					var folder = self.folders[self.defaultFolder];
					if (folder.widgetEl) {
						folder.widgetEl[folder.widget]('checkNeedToRefresh');
					}
				}
			},
			onHide: function () {
                previousModal && previousModal.show();
			}
		});
	},
	createFolders: function() {
		var self = this;
		if (!self.folders) {
			self.folders = {
				frames: {
					label: window.tt('common', 'Кадры'),
					icon: "glyphicon glyphicon-film",
					widget: 'gcVideoFramesFolder',
					options: {
						previewList: self.options.previewList,
						mainHash: self.options.hash
					}
				},
				subtitles: {
					label: window.tt('common', 'Субтитры'),
					icon: "glyphicon glyphicon-subtitles",
					widget: 'gcVideoSubtitles',
					options: {
                        previewList: self.options.previewList,
                        mainHash: self.options.hash,
					}
				},
			};
			if(window.defenceEnabled) {
				self.folders.grids = {
					label: window.tt('common', 'Защита'),
					icon: "glyphicon glyphicon-copyright-mark",
					widget: 'gcVideoGrid',
					options: {
						previewList: self.options.previewList,
						mainHash: self.options.hash
					}
				};
				self.folders.gridLog = {
					label: window.tt('common', 'История вкл. защиты'),
					icon: "glyphicon glyphicon-copyright-mark",
					widget: 'gcVideoGridLog',
					options: {
						previewList: self.options.previewList,
						mainHash: self.options.hash,
					}
				};
				self.folders.statistics = {
					label: window.tt('common', 'Статистика'),
					icon: "glyphicon glyphicon-stats",
					widget: 'gcVideoStatistics',
					options: {
						previewList: self.options.previewList,
						mainHash: self.options.hash
					}
				};
			}
		}
	},
	getSrcByHash: function(hash) {
		return this.folders[this.defaultFolder].widgetEl.gcVideoFramesFolder('getSrcByHash', hash);
	}
} );
