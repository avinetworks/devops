// wait for document to be ready
document.addEventListener("DOMContentLoaded", function(event) {

	let bodhisvgsReplacements = 0;

	function bodhisvgsReplace(img) {

		// must be an image
		if( img.nodeName !== 'IMG' ){
			return;
		}

		var imgID = img.id;
		var imgClass = img.classList;
		var imgURL = img.src;

		// must be svg
		if( !imgURL.endsWith('svg') ){
			return;
		}

		var xmlHttp = new XMLHttpRequest();
		xmlHttp.onreadystatechange = function() {

			if (xmlHttp.readyState == 4 && xmlHttp.status == 200){

				data = xmlHttp.responseText;

				let parser = new DOMParser();
				const doc = parser.parseFromString(data, 'text/html');

				// get svg now
				var svg = doc.getElementsByTagName('svg')[0];

				var svgID = svg.id;

				// Add replaced image's ID to the new SVG if necessary
				if( typeof imgID === 'undefined' ){
					if( typeof svgID === 'undefined' ) {
						imgID = 'svg-replaced-'+bodhisvgsReplacements;
						svg.setAttribute('id', imgID);
					} else {
						imgID = svgID;
					}
				} else {
					svg.setAttribute('id', imgID);
				}

				// Add replaced image's classes to the new SVG
				if(typeof imgClass !== 'undefined') {
					svg.setAttribute('class', imgClass+' replaced-svg svg-replaced-'+bodhisvgsReplacements);
				}

				// Remove any invalid XML tags as per http://validator.w3.org
				svg.removeAttribute('xmlns:a');

				// Replace image with new SVG
				img.replaceWith(svg);

				bodhisvgsReplacements++;

			}

		}

		xmlHttp.open("GET", imgURL, false);
		xmlHttp.send(null);

	}

	function bodhisvgsIterator(node) {

		if( node.childNodes.length > 0 ){

			for (var i = 0; i < node.childNodes.length; i++) {

				if( node.childNodes[i].nodeName == 'IMG' ){

					// its an image... replace it too
					var img = node.childNodes[i];
					bodhisvgsReplace(img);

				}else{

					// go to another level
					bodhisvgsIterator(node.childNodes[i]);

				}
			}

		}

	}

	// Wrap in IIFE so that it can be called again later as bodhisvgsInlineSupport();
	(bodhisvgsInlineSupport = function() {

		// If force inline SVG option is active then add class
		if ( ForceInlineSVGActive === 'true' ) {

			var allImages = document.getElementsByTagName('img');	// find all images on page

			// loop on images
			for(var i = 0; i < allImages.length ; i++) {

				if( typeof allImages[i].src !== 'undefined' ){

					// check if it has svg
					if( allImages[i].src.match(/\.(svg)/) ){

						// add our class - if not already added
						if( !allImages[i].classList.contains(cssTarget.ForceInlineSVG) ){

							// add class now
							allImages[i].classList.add(cssTarget.ForceInlineSVG);

						}

					}

				}


			}

		}

		// Polyfill to support all ye old browsers
		// delete when not needed in the future
		if (!String.prototype.endsWith) {
			String.prototype.endsWith = function(searchString, position) {
				var subjectString = this.toString();
				if (typeof position !== 'number' || !isFinite(position) || Math.floor(position) !== position || position > subjectString.length) {
					position = subjectString.length;
				}
				position -= searchString.length;
				var lastIndex = subjectString.lastIndexOf(searchString, position);
				return lastIndex !== -1 && lastIndex === position;
			};
		} // end polyfill

		// Another snippet to support IE11
		String.prototype.endsWith = function(pattern) {
			var d = this.length - pattern.length;
			return d >= 0 && this.lastIndexOf(pattern) === d;
		};
		// End snippet to support IE11

		// Check to see if user set alternate class
		if ( ForceInlineSVGActive === 'true' ) {
			var target  = ( cssTarget.Bodhi !== 'img.' ? cssTarget.ForceInlineSVG : 'style-svg' );
		} else {
			var target  = ( cssTarget !== 'img.' ? cssTarget : 'style-svg' );
		}

		// remove .img from class
		target = target.replace("img.","");

		var allImages = document.getElementsByClassName(target);	// find all images with force svg class

		for(var i = 0; i < allImages.length ; i++) {

			if( typeof allImages[i].src == 'undefined'  ){	// not an image

				bodhisvgsIterator(allImages[i]);

			}else{

				var img = allImages[i];
				bodhisvgsReplace(img);

			}

		}

	})(); // Execute immediately

});
