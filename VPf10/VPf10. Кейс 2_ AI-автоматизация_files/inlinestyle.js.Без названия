(function($)
{
	$.Redactor.prototype.inlinestyle = function()
	{
		return {
			langs: {
				en: {
					"style": Yii.t("common", "Стиль")
				}
			},
			init: function()
			{
				var tags = {
					"marked": {
                        title: Yii.t("common", "Отмечен"),
						args: ['mark']
					},
					"code": {
                        title: Yii.t("common", "Код"),
						args: ['code']
					},
					"sample": {
						title: Yii.t("common", "Пример"),
						args: ['samp']
					},
					"variable": {
                        title: Yii.t("common", "Переменная"),
						args: ['var']
					},
					"shortcut": {
						title: Yii.t("common", "Ярлык"),
						args: ['kbd']
					},
					"cite": {
						title: Yii.t("common", "Цитирование"),
						args: ['cite']
					},
					"sup": {
						title: Yii.t("common", "Сверху"),
						args: ['sup']
					},
					"sub": {
						title: Yii.t("common", "Снизу"),
						args: ['sub']
					}
				};


				var that = this;
				var dropdown = {};

				$.each(tags, function(i, s)
				{
					dropdown[i] = { title: s.title, func: 'inline.format', args: s.args };
				});


				var button = this.button.addAfter('format', 'inline', this.lang.get('style'));
				this.button.addDropdown(button, dropdown);

			}


		};
	};
})(jQuery);
