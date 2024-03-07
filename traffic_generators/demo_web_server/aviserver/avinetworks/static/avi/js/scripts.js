/* Mobi Nav */

	$("#header .menu").click(function() {
	    $('#header ul').toggle();
	    $('#header ul').toggleClass('mobi_nav');
	    $('#header .arrow').toggle();
	    $("#header ul.mobi_nav li a").click(function() {
		    $('#header ul').hide();
		    $('#header .arrow').hide();
		});
	});


/*  Text Toggle  */

	$("#team ul li .more").click(function() {
		$(this).parent().parent().find('.text').slideToggle();
		var spanVal = $(this).text();
		if(spanVal == 'Read more'){
			$(this).text('Read less');
		} else {
			$(this).text('Read more');
		};
    });

    $("#investors ul li .more").click(function() {
		$(this).parent().parent().find('.text').slideToggle();
		var spanVal = $(this).text();
		if(spanVal == 'Read Bio'){
			$(this).text('Close Bio');
		} else {
			$(this).text('Read Bio');
		};
    });

/* Scrolling */

	if (($('#wrap').width()) < 767) {
		$('.content').pageScroller({
		    navigation: '#nav',
		    scrollOffset: -51    
		});
	} else {
		$('.content').pageScroller({
		    navigation: '#nav',
		    scrollOffset: -93    
		});
	};