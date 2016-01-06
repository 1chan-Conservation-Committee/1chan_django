'use strict';
(function(){
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
})();