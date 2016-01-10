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
