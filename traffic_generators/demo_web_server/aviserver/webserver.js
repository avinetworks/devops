var http = require('http');
var fs = require('fs');
var path = require('path');

html_path = '/';

if (process.argv.length > 2) {
    html_path = process.argv[2];
}

process.chdir(html_path);

function appResponse() {
    var d = new Date();
    h = d.getHours();
    if (h == 8 || h == 20 || h == 13 || h == 1) {
        console.log('delay on');
	return 200;
    } else
        return 95;
}

http.createServer(function (request, response) {
    console.log('request starting...');

    var filePath = '.' + request.url;
    console.log('*' + filePath + '*');
    if (filePath == './')
        filePath = './index.htm';

    var extname = path.extname(filePath);
    var contentType = 'text/html';
    switch (extname) {
        case '.js':
            contentType = 'text/javascript';
            break;
        case '.css':
            contentType = 'text/css';
            break;
        case '.json':
            contentType = 'application/json';
            break;
        case '.png':
            contentType = 'image/png';
            break;      
        case '.jpg':
            contentType = 'image/jpg';
            break;
        case '.wav':
            contentType = 'audio/wav';
            break;
    }

    fs.readFile(filePath, function(error, content) {
        if (error) {
            if(error.code == 'ENOENT'){
                fs.readFile('./404.html', function(error, content) {
                    response.writeHead(404, { 'Content-Type': contentType });
                    response.end(content, 'utf-8');
                });
            }
            else {
                response.writeHead(500);
                response.end('Sorry, check with the site admin for error: '+error.code+' ..\n');
                response.end(); 
            }
        }
        else {
            setTimeout(function() {
            response.writeHead(200, { 'Content-Type': contentType });
            response.end(content, 'utf-8');
            }, appResponse());
        }
    });

}).listen(80);
console.log('Server running at http://127.0.0.1:80/');
