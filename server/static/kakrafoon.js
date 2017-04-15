function update_queue_blah(json, text, asd)
{
    html = ['<table>'];
    for (i = 0; i < json.items.length; i++) {
	item = json.items[i];
	html.push('<tr><td>');
	html.push(item.key);
	html.push('</td><td>')
	html.push(item.user);
	html.push('</td><td>');
	html.push('<ul>');
	for (j = 0; j < item.songs.length; j++) {
	    song = item.songs[j];
	    html.push('<li>');
	    html.push(song.filename);
	    html.push('</li>');
	}
	html.push('</ul>');
	html.push('</td></tr>');
    }
    html.push('</table>');
    queueDiv = $('#queue');
    queueDiv.html(html.join(''));
    
}

function zpad(s, n)
{
    if (s.length < n) {
	return zpad('0'+s, n);
    }
    return s;
}

function lalign(s, n)
{
    var l = s.length;
    for (var i = n; i > l; i--)
	s = s + '&nbsp;';
    return s;
}

function makergb(r, g, b)
{
    return zpad(r.toString(16), 2) + zpad(g.toString(16), 2) + zpad(b.toString(16), 2);
}

function update_queue(json, text, asd)
{
    var h = [];
    var itemCount = json.items.length;
    var green = 255;
    var step = Math.max(Math.min(384 / itemCount, 80), 1);
    for (var i = 0; i < itemCount; i++) {
	var item = json.items[i];
	var first = true;
	var songCount = item.songs.length;
	h.push('<span style="color:#' + makergb(255, Math.round(green), 0) + ';">');
	for (j = 0; j < songCount; j++) {
	    var song = item.songs[j];
	    if (first) {
		h.push(zpad(String(item.key), 4));
		h.push('.');
		h.push(zpad(String(song.key), 2));
		first = false;
	    } else {
		h.push('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')
		h.push(zpad(String(song.key), 2));
	    }
	    h.push('&nbsp;&nbsp;');
	    h.push(lalign(item.user, 10));
	    h.push(song.filename);
	    h.push('<br>');
	}
	h.push('</span>');
	green = Math.max(0.0, green - step);
    }
    var queueDiv = $('#queue');
    queueDiv.html(h.join(''));
}


function enqueue() {
    var f = $('#enqueuefiles')[0];
    var files = f.files
    if (files.length < 1) {
	return false;
    }
    var formData = new FormData();
    var json = {};
    json['username'] = 'webui';
    json['queueitems'] = [];
    qi = json['queueitems'];
    for (var i = 0; i < files.length; i++) {
	qi[i] = {}
	qi[i]['songs'] = []
	var songs = qi[i]['songs'];
	songs[0] = {}
	songs[0]['filename'] = files[i].name;
	songs[0]['fileid'] = 'f' + i;
	formData.append('f' + i, files[i])
    }
    formData.append("enqueue_request", JSON.stringify(json));
    var request = new XMLHttpRequest();
    request.open('POST', '/queue');
    request.send(formData);
}

var queue = $.getJSON('/queue', 'blah', update_queue);
//alert(JSON.stringify(queue));
//queue.innerHtml = 'flask';
