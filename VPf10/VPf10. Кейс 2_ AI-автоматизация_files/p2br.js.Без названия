function p2br(str) {
	// Wandelt <p>FooBar</p> in FooBar<BR> um
	// <BR> am Ende innerhalb eines <P>-Blocks (2* neue Zeile) -> einfaches <BR>
	var i, matches, m, str;
	matches = str.match(/<BR>\s*<\/P>/ig);
	for (i in matches) {
    	if (isNaN(i)) continue;
    	m = matches[i].toString();
    	str = replacer(m, "<BR>", str);
	}

	var placeholder = "<PTOBR>"

	str = replacer("</p>", placeholder, str);
	str = replacer("</P>", placeholder, str);
	str = replacer("<p>", "", str);
	str = replacer("<P>", "", str);

	if ( str.slice( -1 * placeholder.length ) == placeholder ) {
		str = str.substring( 0, str.length - placeholder.length )
	}

	str = replacer("<PTOBR>", "<br>", str);
	return str;
}

function replacer(search, replace, str) {
	// str.replace ersetzt nur 1x. Hier wird alles ersetzt
	return str.split(search).join(replace);
}