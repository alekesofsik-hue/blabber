jQuery.widget('gc.gcVideoGridLog', $.gc.gcFileSelectorFolder, {
	options: {
		mainHash: null,
		previewList: []
	},
	mapFrameHashToSrc: null,
	currentPreview: null,
	watermarkEnableInput: false,
	list: [],
	_create: function() {
		var $messageEl = $('<div></div>');
		this.messageEl = $messageEl;
		this.element.addClass("grid-content");
        this.element.css('display', 'block');
        this.element.append($messageEl);
	},
	init: function() {
		var that = this;
		that.usersDictionary = [];
		that.list = [];

		fetch('/pl/fileservice/api/jwt?hash=' + this.options.mainHash)
			.then(function(data) {return data.text();})
			.then(function(jwt) {
				fetch(window.location.protocol +'//' + window.vhApiHost + '/api/grid/get_log_of_grid_change?jwt=' + jwt)
					.then(function(data) {return data.json();})
					.then(function(data) {
						that.list = data.list;
						var userIds = [];
						$.each(that.list, function (index, value) {
							if (userIds.includes(value.user_id)) {
								return;
							}
							userIds.push(value.user_id);
						});

						if (!userIds.length) {
							that.generateDatatable();
							return;
						}

						fetch('/pl/fileservice/video/users-info?json=' + JSON.stringify(userIds))
							.then(function(resp) {return resp.json();})
							.then(function(resp) {
								that.usersDictionary = resp.result;
								that.generateDatatable();
							})
							.catch(function(err) {console.error(err);});
					})
					.catch(function(err) {console.error(err);});
			});
	},
	generateDatatable: function () {
		var $tables = $('<div class="stat-tables"></div>');

		this.element.addClass("grid-log-content");
		this.element.css({
			'padding' : '20px',
			'width' : '85%',
			'display' : 'inline-block',
			'overflow' : 'hidden',
			'overflow-y' : 'auto',
			'height': '590px',
		});

		var datatableOptions = {
			"ordering": false,
			"scrollY": '400px',
			"scrollCollapse": true,
			"paging": true,
			"language": {
				"search": Yii.t('common', 'Поиск:'),
				"lengthMenu": Yii.t('common', 'Показать') + ' _MENU_ ' + Yii.t('common', 'записей'),
				"zeroRecords": Yii.t('common', 'Извините, ничего не найдено'),
				"info": Yii.t('common', 'Количество записей') + ': _MAX_',
				"infoEmpty": Yii.t('common', 'Записей не найдено'),
				"infoFiltered": Yii.t('common', '(отфильтровано') + ' _MAX_ ' + Yii.t('common', 'записей') + ')',
				"paginate": {
					"first": Yii.t('common', 'Первая'),
					"last": Yii.t('common', 'Последняя'),
					"next": Yii.t('common', 'Следующая'),
					"previous": Yii.t('common', 'Предыдущая')
				},
			}
		};

		this.element.empty();
		this.element.append(this.messageEl);
		this.element.append($tables);

		this.generateHtml();
		$tables.append(this.mainTable);

		this.mainTable.DataTable(datatableOptions);
		this.mainTable.parent().parent().parent().css('height', '400px');
	},
	generateHtml: function() {
		var $content = $('<table class="table">');
		var $tableHead = $('<thead>\n' +
			'    <tr>\n' +
			'      <th scope="col">' + Yii.t('common', 'Дата') + '</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Действие') + '</th>\n' +
			'      <th scope="col">' + Yii.t('common', 'Пользователь') + '</th>\n' +
			'    </tr>\n' +
			'  </thead>');

		var $tableRows = this.generateRows();
		var $tableEnd = $('</table>');

		$content.append($tableHead);
		$content.append($tableRows);
		$content.append($tableEnd);

		this.mainTable = $content;

		return $content;
	},
	generateRows: function() {

		var convertDateTime  = function(utcDate) {
			var partsDateTime = utcDate.split(' ');
			var partsDate = partsDateTime[0] ? partsDateTime[0].split('-') : [0,0,0];
			var partsTime = partsDateTime[1] ? partsDateTime[1].split(':') : [0,0,0];
			var date = new Date(Date.UTC(partsDate[0], partsDate[1] - 1, partsDate[2], partsTime[0], partsTime[1], partsTime[2]));
			return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
		};

		var that = this;
		var $content =  $('<tbody>');
		$.each(this.list, function (index, value) {
			var userFullName =  '';
			if (that.usersDictionary[value.user_id]) {
				var firstName = that.usersDictionary[value.user_id].first_name === null || value.deleted ?
					'' : that.usersDictionary[value.user_id].first_name;
				var lastName = that.usersDictionary[value.user_id].last_name === null || value.deleted ?
					'' : that.usersDictionary[value.user_id].last_name;
				userFullName = (firstName + ' ' + lastName).trim();
			}

			$content.append($('<tr>' +
				'<th scope="row">' + convertDateTime(value.date_change) + '</th>' +
				'<td>' + (value.status === '1' ? Yii.t('common', 'Включение') : Yii.t('common', 'Выключение') ) + '</td>'
				+ '<td>' + (userFullName ? userFullName : '#' + value.user_id) + '</td>'
			));
		});

		$content.append($('</tbody>'));

		return $content;
	}
} );
