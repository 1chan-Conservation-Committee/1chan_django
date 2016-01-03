'use strict';
(function(){
	$('#comment_form').submit(function(e){
		$.ajax({
			type: 'post',
			url: e.target.action,
			data: $(e.target).serializeArray(),
			complete: function(xhr, status) {
				console.log(status);
				var resp = JSON.parse(xhr.responseText);
				if (resp.success) {

				} else {
					alert(resp.errors);
				};
				window.grecaptcha.reset();
			},
			dataType: 'json',
		});
		e.preventDefault();
	});
})();