if (typeof(window.gcCounter) === "undefined") {
	var getTimeZoneData = function() {
		var today = new Date();
        return encodeURI(today.getFullYear() + "-" + (today.getMonth() + 1) + "-" + today.getDate() + " " + today.getHours() + ":" + today.getMinutes());
	};

	try {
		var tz = getTimeZoneData(),
			urlAdd = "";

		if (window.gcsObjectType) {
			urlAdd = "&objectType=" + window.gcsObjectType;
		}

		if (window.gcsObjectId) {
			urlAdd = "&objectId=" + window.gcsObjectId;
		}

		if (window.gcUniqId) {
			urlAdd += "&uniqId=" + encodeURIComponent(window.gcUniqId);
		}

		if (window.gcsObjectTypeId) {
			urlAdd += "&objectTypeId=" + window.gcsObjectTypeId;
		}

		if (
			undefined !== window.csrfToken && window.csrfToken && undefined !== window.gcSessionId && !window.gcSessionId
		) {
			urlAdd += "&token=" + window.csrfToken;
		}

		let statUrl = "/stat/counter?ref=" + encodeURIComponent(document.referrer) + "&loc=" + encodeURIComponent(document.location.href) + urlAdd + "&tzof=" + tz;

		if (typeof(window.isSessionLocalStorageEnabled) === "undefined" || !window.isSessionLocalStorageEnabled) {
			addCounterImage("gccounterImg", statUrl);
		} else {
			var script = document.createElement("script");
			script.type = "text/javascript";
			script.async = true;
			script.src = statUrl;
			document.body.appendChild(script);
		}
		window.gcCounter = 1;
	} catch (e) {
		addCounterImage("gccounterErrImg");
	}
}

function gcFixIncident( type, subtype ) {
	var data = {};
	data.type = type;
	data.subtype = subtype;
	data.userId = window.accountUserId;
	data.sessionId = window.gcSessionId;

	ajaxCall( "/pl/stat/counter/fix-incident", data, {}, function( response ) {

	} );
}

function addCounterImage(id, src)
{
	var img = new Image(1, 1);

	if (src) {
		img.src = src;
	}

	if (id) {
		img.id = id;
	}

	img.style = "position: absolute; left: 0; top: 0";

	document.body.appendChild(img);
}
