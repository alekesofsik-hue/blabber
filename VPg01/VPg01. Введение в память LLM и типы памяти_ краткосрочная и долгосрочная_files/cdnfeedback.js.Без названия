var reasonQuestions = {
	type: 'reason',
	question: "Пожалуйста, подскажите причину нажатия?",
	answers: [
		'<button type="button" class="btn btn-outline-primary reason-btn" id="quality">Не устроило качество видео</button>',
		'<button type="button" class="btn btn-outline-primary reason-btn" id="speed">Не устроила скорость видео</button>',
		'<button type="button" class="btn btn-outline-primary reason-btn" id="fun">Просто из любопытства</button>',
	]
};

var resultQuestions = {
	type: 'result',
	question: "Проблема устранена?",
	answers: [
		'<button type="button" class="btn btn-outline-success result-btn" id="ok">Да</button>',
		'<button type="button" class="btn btn-outline-danger result-btn" id="support">Нет, отписать в техподдержку</button>',
		'<button type="button" class="btn btn-outline-primary result-btn" id="back">Вернуться на старый плеер</button>',
	]
};

var VH_SPEED_COOKIE_NAME = 'vh-speed';

function upgradeCdn(data) {
	var url = '/pl/fileservice/video/upgrade-cdn';
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, false);
	xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	xhr.send(JSON.stringify({'video-hash': data.videoHash}));
}

function feedbackCdn(data) {
	var url = '/pl/fileservice/video/feedback-cdn';
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, false);
	xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	xhr.send(JSON.stringify({'reason': data.reason, 'result': data.result}));
}

function closeFeedback() {
	var url = '/pl/fileservice/video/close-feedback';
	var xhr = new XMLHttpRequest();
	xhr.open("POST", url, false);
	xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	xhr.send(JSON.stringify({'reason': 'close', 'result': 'close'}));
}

function buildQuestion(data) {
	var question = data.question;
	var answers = '';

	data.answers.forEach(function (answer) {
		answers += answer;
	});

	return question + answers;
}

function show(el) {
	el.style.display = 'block';
}

function close(el) {
	el.style.display = 'none';
}

function remove(el) {
	el.parentNode.removeChild(el);
}


/**
 * @param {HTMLElement} vheChangeEl
 */
function showAlternativePlayerBtn(vheChangeEl) {
	var link = vheChangeEl.querySelector('.disclaimer-url');
	var feedbackReason = vheChangeEl.querySelector('.feedback#reason');
	var feedbackResult = vheChangeEl.querySelector('.feedback#result');
	var feedbackClose = vheChangeEl.querySelector('.feedback#close');

	var feedbackStatus = vheChangeEl.dataset['feedbackStatus'];
	var currentCdn = vheChangeEl.dataset['currentCdn'];

	vheChangeEl.style.display = 'block';
	feedbackReason.style.display = 'none';
	feedbackResult.style.display = 'none';

	if (currentCdn === 'integros' || currentCdn === '') {
		//change.style.height = '35px';
		link.innerHTML = window.tt('common', 'Speed problem');
	} else {
		feedbackReason.innerHTML = buildQuestion(reasonQuestions);
		feedbackResult.innerHTML = buildQuestion(resultQuestions);

		link.innerHTML = window.tt('common', 'Вернуться на основной плеер');

		switch (feedbackStatus) {
			case 'noFeedback' :
				remove(feedbackReason);
				remove(feedbackResult);
				break;
			case 'hasReason' :
				remove(feedbackResult);
				remove(feedbackReason);
				break;
			case 'hasResult' :
				//change.style.height = '35px';
				remove(feedbackReason);
				remove(feedbackResult);
				break;
		}
	}

	feedbackClose.addEventListener('click', function (e) {
		e.preventDefault();
		closeFeedback();
		close(vheChangeEl);
	});

	var btns = vheChangeEl.querySelectorAll('.btn');
	btns.forEach(function (btn) {
		btn.addEventListener('click', function (e) {
			if (btn.classList.contains('reason-btn')) {
				vheChangeEl.dataset.reason = btn.id;

				show(feedbackResult);
				close(feedbackReason);
			}

			if (btn.classList.contains('result-btn')) {
				vheChangeEl.dataset.result = btn.id;
				feedbackCdn(vheChangeEl.dataset);
				feedbackResult.innerHTML = 'Спасибо!';

				if (btn.id === 'back') {
					upgradeCdn(vheChangeEl.dataset);
					window.location.reload();
				}

				setTimeout(function () {
					remove(feedbackReason);
					remove(feedbackResult);

					//change.style.height = 'auto';
				}, 2000);
			}
		});
	});

	link.addEventListener('click', function (e) {
		e.preventDefault();
		upgradeCdn(vheChangeEl.dataset);
		window.location.reload();
	});
}

// /**
//  *
//  * @param {string} currentCdn
//  *
//  * @returns {Promise}
//  */
// function checkUserSpeed(currentCdn) {
// 	var url = 'https://{url}/speed/speed.bin?rnd=' + Math.random() + '&host=vh-06';
// 	if (currentCdn === 'integros') {
// 		url = url.replace('{url}', 'vh-06-78293b36.cdn.integros.com');
// 	} else {
// 		url = url.replace('{url}', 'vh-06.gcdn.co');
// 	}
//
// 	return new Promise(function (resolve, reject) {
// 		var xhr = new XMLHttpRequest();
// 		xhr.timeout = 20000;
// 		xhr.open('GET', url, true);
// 		var downloadStartTime = window.performance.now();
//
// 		xhr.onloadend = function (event) {
// 			var fileSize = event.lengthComputable ? event.loaded : 1048576;
// 			var duration = window.performance.now() - downloadStartTime;
// 			var speedKb = fileSize / duration;
// 			resolve(speedKb, duration);
// 		};
// 		xhr.ontimeout = function () {
// 			reject();
// 		};
// 		xhr.onerror = function () {
// 			reject();
// 		};
//
// 		xhr.send(null);
// 	});
// }

(function () {
	var vheCdnChangeElList = document.querySelectorAll('.vhe-cdn-change');
	// Если блоков со смной CDN не найдено, то выходим
	if (vheCdnChangeElList.length === 0) {
		return;
	}

	vheCdnChangeElList.forEach(function (change) {
		change.style.display = 'none';
	});

	/** @var {HTMLElement} vheCdnChangeEl */
	var vheCdnChangeEl = vheCdnChangeElList[0];

	// Если это User Gc или пользователь под сублогином, то всегда отображаем кнопку
	if (window.accountUserId === -2 || window.isSublogined) {
		showAlternativePlayerBtn(vheCdnChangeEl);
		return;
	}

	// Если пользователь не авторизован, то выходим
	if (window.accountUserId === -1) {
		return;
	}

	showAlternativePlayerBtn(vheCdnChangeEl);

	//
	// /** @var {string} currentCdn */
	// var currentCdn = vheCdnChangeEl.dataset['currentCdn'];
	// /** @var {string} speedCookie */
	// var speedCookie = gcGetCookie(VH_SPEED_COOKIE_NAME);
	// var speedCookieKey = window.requestIp + '_' + currentCdn;
	// // Если мы делали замер, то выходим
	// if (speedCookie === speedCookieKey) {
	// 	return;
	// }
	//
	// // Замеряем скорость инета
	// checkUserSpeed(currentCdn).then(function (speedKb) {
	//     // Ставим куку на неделю, чтобы повторно не проверять
	// 	gcSetCookie(VH_SPEED_COOKIE_NAME, speedCookieKey, {expires: 60 * 60 * 24 * 7, path: '/'});
	// 	if (speedKb < 1000) {
	// 		showAlternativePlayerBtn(vheCdnChangeEl);
	// 	}
	// }).catch(function () {
	// 	showAlternativePlayerBtn(vheCdnChangeEl);
	// });
})();
