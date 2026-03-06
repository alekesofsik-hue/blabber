jQuery.widget('gc.tusUploader', {
    loadingFiles: [],
    options: {
        owner: null,
        onSuccess: null,
        progressContainer: null,
        accept: null,
    },
    _create: function (callback) {
        var self = this;

        if (!tus.isSupported) {
            console.log('Tus uploader not supported for this browser');
            return;
        }

        const $uploaderContainer = this.element;
        if (this.options.progressContainer === null) {
            this.options.progressContainer = $uploaderContainer;
        }

        const $btn = $('<label class="tus-uploader-btn">' + Yii.t('common', 'Upload') + '</label>').appendTo($uploaderContainer);
        const $input = $('<input type="file" multiple style="display: none;" />').appendTo($btn);
        if (this.options.accept) {
            $input.attr('accept', this.options.accept);
        }

        $input[0].addEventListener("change", function (e) {
            /** @var {FileList} files */
            const files = e.target.files;
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const fileKey = self.composeFileFingerprint(file);
                if (self.loadingFiles.includes(fileKey)) {
                    console.log('File already in upload queue');

                    continue;
                }
                self.loadingFiles.push(fileKey);

                self.uploadFile.call(self, file);
            }
        });
    },
    /** @param {File} file */
    uploadFile: function (file) {
        var self = this;

        let $title = $('<div class="clearfix tus-uploader-title" />').html(file.name)
            .appendTo(self.options.progressContainer);

        const progress = this.createProgressBar(self.options.progressContainer);

        const target = this.createUploadTarget(file);

        let uploadIsActive = false;

        const $resumeBtn = $('<button class="btn btn-default btn-xs">Продолжить</button>')
            .click(function () {
                if (!uploadIsActive) {
                    self.resume(upload);
                    onResume();
                }
            })
            .hide().appendTo($title);

        const $processBtn = $('<span class="glyphicon glyphicon-play tus-progress-icon" />')
            .click(function () {
                if (uploadIsActive) {
                    upload.abort();
                    onPause();
                } else {
                    self.resume(upload);
                    onResume();
                }
            }).hide().appendTo(progress.progressBar);

        const $alert = $('<span class="text-danger" />').hide().appendTo($title);

        const onPause = function () {
            uploadIsActive = false;
            $resumeBtn.show();
            $processBtn
                .addClass('glyphicon-play')
                .removeClass('glyphicon-pause')
                .attr('title', 'Продолжить').show();
            progress.pause();
        };
        const onResume = function () {
            uploadIsActive = true;
            $resumeBtn.hide();
            $processBtn
                .addClass('glyphicon-pause')
                .removeClass('glyphicon-play')
                .attr('title', 'Остановить').show();
            $alert.hide().html('');
            progress.active();
        };

        var hasOnlineListener = false;

        var chunkUploadStart = new Date();
        const chunkSizeDefault = 10000000;
        const chunkSizeMultiplier = 2;
        const chunkSizeMax = 1000000000;
        const chunkUploadSuccessTime = 15;

        // Create a new tus upload
        const upload = new tus.Upload(file, {
            endpoint: target,
            chunkSize: chunkSizeDefault,
            retryDelays: [200, 1000, 10000, 60000],
                metadata: {
                    filename: file.name,
                    filetype: file.type
                },
                removeFingerprintOnSuccess: true,
            fingerprint: function fingerprint(file, options, callback) {
                // removed options.endpoint from original
                return callback(
                    null,
                    self.composeFileFingerprint(file)
                );
            },
            onError: function (error) {
                this.chunkSize = chunkSizeDefault;
                if (navigator.onLine === false) {
                    $alert.html('Нет подключения к сети').show();

                    if (hasOnlineListener === false) {
                            hasOnlineListener = true;
                            window.addEventListener('online', function (e) {
                                hasOnlineListener = false;
                                self.resume(upload);
                                onResume();
                            }, {
                                once: true,
                            });
                    }
                } else {
                    $alert.html('Ошибка загрузки').show();
                }

                if (error.originalRequest) {
                    onPause();
                }

                progress.failed();
            },
            onProgress: function (bytesUploaded, bytesTotal) {
                let percentage = (bytesUploaded / bytesTotal * 100).toFixed(2);
                progress.setPercent(percentage);
            },
            onChunkComplete: function (chunkSize, bytesAccepted, bytesTotal) {
                let now = new Date();
                let chunkUploadDuration = (now - chunkUploadStart) / 1000;
                let uploadSpeed = Math.round(chunkSize / chunkUploadDuration / (1024 * 1024) * 100) / 100;
                console.debug("Uploaded chunk " + chunkSize + " (" + bytesAccepted + " / " + bytesTotal + "), duration: " + chunkUploadDuration + ", speed: " + uploadSpeed);
                chunkUploadStart = now;
                // increase chunk size for fast upload
                if (chunkUploadDuration < chunkUploadSuccessTime && this.chunkSize < chunkSizeMax) {
                    this.chunkSize = Math.round(this.chunkSize * chunkSizeMultiplier);
                    console.debug("Increase chunk size " + chunkSize + " -> " + this.chunkSize);
                }
                // decrease chunk size for slow upload
                if (chunkUploadDuration > chunkUploadSuccessTime * 2 && this.chunkSize > chunkSizeDefault) {
                    this.chunkSize = Math.round(this.chunkSize / chunkSizeMultiplier);
                    console.debug("Decrease chunk size " + chunkSize + " -> " + this.chunkSize);
                }
            },
            onSuccess: function () {
                $processBtn.hide();
                progress.finish();
                if (self.options.onSuccess) {
                    self.options.onSuccess(upload.url, upload.file);
                }
            },
        });

        // Start the upload
        upload.start();
        onResume();
    },
    resume: function (upload) {
        try {
            // update secure link
            if (upload.url) {
                const uploadUrl = new URL(upload.url);
                if (uploadUrl.searchParams.get('e') - ((new Date()).getTime() / 1000) < 3600) {
                    const newUrl = this.createUploadTarget(upload.file, uploadUrl.href, uploadUrl.host);
                    if (newUrl) {
                        upload.url = newUrl;
                    }
                }
            }
        } catch (e) {
            console.log(e);
        }

        upload.start();
    },
    /** @param {File} file */
    composeFileFingerprint: function (file) {
        return ["tus-br", file.name, file.type, file.size, file.lastModified].join("-");
    },
    /**
     * @param {File} fileInfo
     * @param {String} [uri]
     * @param {String} [host]
     */
    createUploadTarget: function (fileInfo, uri, host) {
        let target;
        var tusUri = '/fileservice/tus';

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

            tusUri += '?' + jQuery.param(requestParams);
        } catch (err) {
        }

        $.ajax({
            url: '/fileservice/widget/create-secret-link',
            method: 'GET',
            data: {
                host: host ? host : window.fileserviceUploadHost,
                uri: uri ? uri : tusUri,
                expires: 12 * 3600,
                fileInfo: {
                    name: fileInfo.name,
                    size: fileInfo.size,
                    type: fileInfo.type,
                },
            },
            success: function (data) {
                if (data.link) {
                    target = data.link;
                }
            },
            error: function (http, message, exc) {sendCreateLinkError(http, message, exc);},
            async: false
        });

        return target;
    },
    createProgressBar: function (uploaderContainer) {
        const progress = {
            progressBarContainer: null,
            progressBar: null,
            progressText: null,
            init: function (container) {
                this.progressBarContainer = $('<div class="progress" />').appendTo(container);
                this.progressBar = $('<div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" />').appendTo(this.progressBarContainer);
                this.progressText = $('<span />').appendTo(this.progressBar);
            },
            setPercent: function (value) {
                this.progressBar.attr({
                    'aria-valuenow': value,
                });
                this.progressBar.css({
                    'width': value + '%',
                });
                this.progressText.html(value + '%');
            },
            active: function () {
                this.progressBar
                    .addClass("progress-bar-success progress-bar-striped active")
                    .removeClass("progress-bar-warning progress-bar-danger");
            },
            pause: function () {
                this.progressBar
                    .addClass("progress-bar-warning")
                    .removeClass("progress-bar-danger progress-bar-success progress-bar-striped active");
            },
            failed: function () {
                this.progressBar
                    .addClass("progress-bar-danger")
                    .removeClass("progress-bar-warning progress-bar-success progress-bar-striped active");
            },
            finish: function () {
                this.progressBar
                    .removeClass("progress-bar-striped active");
            },
        };
        progress.init(uploaderContainer);

        return progress;
    },
});
