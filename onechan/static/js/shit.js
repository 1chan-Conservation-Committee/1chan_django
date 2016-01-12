'use strict';
(function(){
	// taken from Django docs
	function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie != '') {
	        var cookies = document.cookie.split(';');
	        for (var i = 0; i < cookies.length; i++) {
	            var cookie = $.trim(cookies[i]);
	            // Does this cookie string begin with the name we want?
	            if (cookie.substring(0, name.length + 1) == (name + '=')) {
	                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                break;
	            }
	        }
	    }
	    return cookieValue;
	}

	var csrftoken = getCookie('csrftoken');
	$.ajaxSettings.headers = {'X-CSRFToken': csrftoken};

	var secure = (window.location.protocol.search(/https/) != -1) ? 's' : '';
	var ws = new WebSocket("ws" + secure + "://" + window.location.host + "/ws");
	ws.onopen = function(e) {
		console.log(e);
	};
	ws.onmessage = function(e) {
		console.log(e);
		var msg = JSON.parse(e.data);
		switch (msg.type) {
			case "count": {
				if (msg.room == 'default') {
					$('#stats_online').text(msg.data.count);
				};
				break;
			}
		};
	};

	$('#comment_form').submit(function(e){
		$.ajax({
			type: 'post',
			url: e.target.action,
			data: $(e.target).serializeArray(),
			complete: function(xhr, status) {
				var resp = JSON.parse(xhr.responseText);
				console.log(resp);
				$('#comment_form_error_captcha').text('');
				$('#comment_form_error_text').text('');
				if (resp.success) {
					$('#comment_form_text').val('');
				} else {
					$.each(resp.errors, function(key, val){
						$('#comment_form_error_'+key).text(val);
					});
				};
				window.grecaptcha.reset();
			},
			dataType: 'json',
		});
		e.preventDefault();
	});

	$('.post-rate-buttons').click(function(e){
		var value = parseInt(e.target.dataset.rateValue);
		var url = e.currentTarget.dataset.rateUrl;
		$.ajax({
			type: 'POST',
			url: url,
			data: {'value': value},
			complete: function(xhr, status) {
				console.log(status);
			}
		});
		e.preventDefault();
	});

})();
