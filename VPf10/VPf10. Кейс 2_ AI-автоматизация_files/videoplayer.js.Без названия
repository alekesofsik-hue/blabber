
window.vhs.init(window.vhsRegion);

(function () {
	document.querySelectorAll('.js--lazy-player-button').forEach(function (button) {
		button.addEventListener('click', async function (event) {
			var dataset = event.target.closest('.js--vhi-root').dataset;

			let masterPlayList = '';
			if (dataset.masterPlayListUrl) {
				try {
					let rawJson = null
					const response = await fetch(dataset.masterPlayListUrl)
					if (response.ok) {
						rawJson = await response.json();
					}
					masterPlayList = rawJson?.data?.master_play_list;
				} catch (e) {
					console.log('unable to fetch data: ' + e.message)
				}
			}
			/* for debug period only */
			console.log('got masterPlayList ' + masterPlayList)
			if (masterPlayList && window.appHandleAction) {
				window.appHandleAction({
					type: 'showVideo',
					src: {
						hls: masterPlayList
					},
                    getCurrentPlayerTimeUrl: dataset.getLastSeenTime,
                    setCurrentPlayerTimeUrl: dataset.setLastSeenTime,
                    savePositionKey: dataset.savePositionKey
				})
				/* for debug period only */
				console.log('window.appHandleAction not empty')
				// maybe, these two strings are useless
				event.stopPropagation()
				event.preventDefault()
			} else {
				event.target.closest('.js--lazy-player-image').style.display = 'none';
				var iframe = document.createElement('iframe');
				iframe.setAttribute('id', 'vhplayeriframe-' + dataset.videoHash);
				iframe.setAttribute('src', dataset.iframeSrc);
				iframe.setAttribute('class', 'vhi-iframe js--vhi-iframe');
				iframe.setAttribute('allow', 'autoplay; encrypted-media; clipboard-read; clipboard-write;');
				iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-popups allow-forms allow-downloads');
				iframe.setAttribute('allowFullScreen', '1');
				iframe.setAttribute('frameBorder', '0');
				iframe.setAttribute('scrolling', 'no');
				event.target.closest('.js--lazy-player-iframe').appendChild(iframe);
			}
		});
	});
})();
