function $t(category, key, fallback = '') {
  if (typeof Yii != 'undefined') {
    return Yii.t(category, key);
  }
  return fallback ? fallback : key;
}

window.audioComments = {
	recordAudio: '',
	recordStatus: '',
	mediaStream: '',

	isMimeTypeSupported(mimeType) {

		return true;

		if (typeof MediaRecorder.isTypeSupported !== 'function') {
			return true;
		}
		if ( mimeType == 'audio/webm' && window.testDisableWebm ) {
			return false;
		}

		return MediaRecorder.isTypeSupported(mimeType);
	},

	record: function (x) {
		var self = $(x);

		if (!self.parent().children('div.audio-upload').length) {
			$('<div class="audio-upload"></div>').appendTo(self.parent());
		}

		var inputUpload = self.parent().children('div.audio-upload');
		var audioStatus = self.children('span.audio-status');
		var microphone = self.children('i.fa-microphone');

		if (
			!window.audioComments.recordStatus
			|| window.audioComments.recordStatus == 'stop'
		) {
			window.audioComments.recordStatus = 'allow';

			var buttons = $(
				[
					'<div class="audio-tip">',
					'<div class="tooltip-inner">',
					'<div class="audio-record"><span class="glyphicon glyphicon-record" aria-hidden="true"></span> ' + $t('common', 'запись') + '</div>',
					'<div class="audio-cancel"><span class="glyphicon glyphicon-trash" aria-hidden="true"></span> ' + $t('common', 'отменить') + '</div>',
					'<div class="audio-save"><span class="glyphicon glyphicon-stop" aria-hidden="true"></span> ' + $t('common', 'стоп') + '</div> ',
					'</div></div>'
				].join(' ')).appendTo(self.next()).hide();

			audioStatus.show().html($t('common', 'разрешите доступ к микрофону...'));
		}

		if (window.audioComments.recordStatus == 'allow') {
			window.audioComments.recordStatus = 'check';

			var recorderType = StereoAudioRecorder;
			var mimeType = "audio/wav";


			if ( this.isMimeTypeSupported("audio/webm") ) {
				recorderType = MediaStreamRecorder;
				mimeType = "audio/webm";
			}

			var isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
			if(isSafari){
				recorderType = StereoAudioRecorder;
				mimeType = "audio/wav";
			}

			window.navigator.mediaDevices.getUserMedia({audio: true})
				.then(function(localMediaStream) {

					window.audioComments.recordAudio = RecordRTC(localMediaStream, {
						type: 'audio',
						mimeType: mimeType,
						recorderType: recorderType,
						disableLogs: false
					});

					window.audioComments.mediaStream = localMediaStream;
					audioStatus.hide();
					buttons.show();
					window.audioComments.recordStatus = 'start';
				})
				.catch(function(err) {
					/* handle the error */
                    console.error(err);
					audioStatus.show().html($t('common', 'доступ к микрофону запрещен!'));
				});

			/*
			window.navigator.mediaDevices.getUserMedia({audio: true}, function (localMediaStream) {
				window.audioComments.recordAudio = RecordRTC(localMediaStream, {
					type: 'audio',
					mimeType: mimeType,
					recorderType: recorderType,
					disableLogs: false
				});

				window.audioComments.mediaStream = localMediaStream;
				audioStatus.hide();
				buttons.show();
				window.audioComments.recordStatus = 'start';

			}, function (e) {
				audioStatus.show().html('доступ к микрофону запрещен!');
			});
			*/
		}

		$('.audio-cancel', buttons).click(function () {
			if (window.audioComments.recordStatus == 'allow') {
				return;
			}
			microphone.css('color', '#999');
			if (window.audioComments.mediaStream) {
				window.audioComments.mediaStream.getAudioTracks()[0].stop();
			}
			audioStatus.html('');
			buttons.remove();
			window.audioComments.recordStatus = 'stop';
		});

		$('.audio-record', buttons).click(function() {
			if (window.audioComments.recordStatus == 'start') {
				window.audioComments.startRecord(audioStatus, microphone);
			}

		});

		//	var extension = this.isMimeTypeSupported("audio/webm") ? "webm" : "wav";
		var extension = isSafari ? "wav": "webm" ;

		$('.audio-save', buttons).click(function () {

			if (window.audioComments.recordStatus == 'recording') {
				buttons.remove();
				window.audioComments.recordStatus = 'stop';

				window.audioComments.recordAudio.stopRecording(function () {

					microphone.css('color', '#999');
					audioStatus.html($t('common', 'сохранение...'));

					window.audioComments.mediaStream.getAudioTracks()[0].stop();


					var now = new Date();
					var fileName = now.getFullYear() + '' + now.getMonth() + '' + now.getDate() + '' + now.getHours() + '' + now.getMinutes() + '' + now.getSeconds();
					fileName += '_';
					fileName += Math.round(Math.random() * 9999) + '.' + extension;

					var formData = new FormData();
					var audioBlob = window.audioComments.recordAudio.getBlob();
					formData.append('Filedata', audioBlob);
					formData.append('BlobfileName', fileName);

					var uploadFormToUrl = function (url, formData) {
						$.ajax({
							url: url,
							type: 'POST',
							data: formData,
							processData: false,
							contentType: false,
							success: function (data) {
								if (data == 'Error') {
									alert($t('common', 'Невозможно сохранить файл!'));
								} else {

									var info = $('<span class="audio-info">'
										+ '<span class="close-info" style="float:right;">x</span>'
										+ '<div>'
										+ '<audio controls=""><source src="' + data.download_url + '" type="audio/mpeg"></audio>'
										+ '<br>' + fileName
										+ '</div>'
										+ '</span>'
									);
									$('.close-info', info).click(function () {
										info.remove();
									});
                                    var audioAnswer = microphone.closest('.audio-answer');
                                    console.log('audioAnswer', audioAnswer);
                                    var input;

                                    if (audioAnswer.length) {
                                        input = $('<input type="hidden" class="audio-value" name="' + audioAnswer.data('name') + '">');
                                        var input2 = $('[name="' + audioAnswer.data('hashInput') + '"]');
                                        if (input2) {
                                            input2.val(data.hash);
                                            console.log(input2);
                                        }
                                        var forRemove = inputUpload
                                            .parents('.addfield.addfield-type-string_with_audio, .addfield.addfield-type-audio')
                                            .find('.js__old-audio-info');
                                        if (forRemove) {forRemove.remove();}
                                        info.addClass('js__old-audio-info');
                                    } else {
                                        input = $('<input type="hidden" class="audio-value" name="GetCourseComment[audioFiles][]">');
                                    }
									input.val(data.hash);
									input.appendTo(info);
									info.appendTo(inputUpload);
									audioStatus.html('');
									self.parent().children('.comment-form-wrapper .new-comment .btn-send').show();
									self.next().next().children('.save-button').removeClass('disabled');
								}
							},
							error: function (error) {
								buttons.show();
								audioStatus.html($t('common', 'ошибка сохранения') +': ' + error.statusText);
							}
						});
					};

					if (window.fileserviceUploadHost) {
						formData.append('fullAnswer', true);
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
								expires: 600
							},
							success: function (data) {
								if (data.link) {
									uploadFormToUrl(data.link, formData);
								} else {
									buttons.show();
									audioStatus.html($t('common', 'ошибка сохранения'));
								}
							},
							error: function (error) {
								buttons.show();
								audioStatus.html($t('common', 'ошибка сохранения') +': ' + error.statusText);
								try{sendCreateLinkError(http, message, exc);}catch (e) {}
							},
							async: false
						});
					} else {
						uploadFormToUrl(
							'/fileservice/widget/upload?deprecated=9'
								+ '&secure=' + window.isEnabledSecureUpload
								+ '&host=' + window.fileserviceUploadHost,
							formData
						);
					}

				});
			}

		});
	},

	startRecord: function(audioStatus, microphone) {
		window.audioComments.recordAudio.startRecording();

		window.audioComments.recordStatus = 'recording';

		audioStatus.show().html($t('common', 'идет запись...'));
		microphone.css('color', 'red !important');
		$('.audio-record').css('color', 'red');
	},

	init: function() {
		$('.audio-comment, .audio-answer').on('click', function() {
			return window.audioComments.record(this);
		});
	}
};

$(function() {
	window.audioComments.init();

	$( document ).ready(function() {
		try {
			window.AudioContext = window.AudioContext || window.webkitAudioContext;
			window.navigator.getUserMedia = window.navigator.getUserMedia || window.navigator.webkitGetUserMedia || window.navigator.mediaDevices.getUserMedia;
			window.URL = window.URL || window.webkitURL;



			if (window.AudioContext && window.navigator.getUserMedia && window.URL) {
				$('.audio-comment, .audio-answer').show();
			}

		} catch (e) {
			$('.audio-comment, .audio-answer').hide();
		}
	});

});
