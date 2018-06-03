var express = require('express');

var url = require('url');
var querystring = require('querystring');
var EventEmitter = require('events').EventEmitter;
var app = express();
var server = require('http').createServer(app); // Server(app)
var server81 = require('http').createServer(app);
var io = require('socket.io')(server);
var io81 = require('socket.io')(server81);

function start() {
	// The server should listen on port 8080 -> http://localhost:8080/
	server.listen(8080);

	// Define the directory 'view' as the root to serve static files (*.{css,js})
	app.use(express.static('view'));

	// Serve index.html to the client when he requests '/'
	app.get('/', (req, res) => {
		console.log(req.url);
		console.log(url.parse(req.url).pathname);
		fs.readFile('view/index.html', 'utf-8', function(error, content) {
			res.writeHead(200, {"Content-Type": "text/html"});
			res.end(content);
		});
	});
	io.on('connection', socket => {
		console.log('A client is connected');
		socket.emit('message', 'You are connected');

		// Message from HTML client-----------------------------
		socket.on('imessage', gdata => {
			console.log(gdata);
			socket.broadcast.emit('message', gdata);
		});

		// message from main.py---------------------------------
		socket.on('pyMessage', gdata => {
			console.log(gdata);
		});

		// search for closest airfield --------------------------
		// from client index.html
		socket.on('compute_near', gdata => {
			console.log(gdata);
			socket.broadcast.emit('near', gdata); // to main.py
		});
		// from client main.py
		socket.on('near_computed', gdata => {
			socket.broadcast.emit('near_computed', gdata); // to client index.html
		});

		// scenario DIVERSION------------------------------------
		socket.on('action', gdata => {
			socket.broadcast.emit('action', gdata);
		});
		// list of points received from Python (Trajectory)
		socket.on('points', gdata => {
			socket.broadcast.emit('points', gdata);
		});
	});

	console.log('Démarrage du serveur...');
	return server;
}

function start81() {
	server81.listen(8081);
	console.log('[DBG] Server created and listen on port 8081');
	io81.on('connection', function(socket) {
		console.log('[SCK] Connection opened on port 8081');
		socket.on('action', function(gdata) {
			socket.broadcast.emit('action', gdata);
		});
		socket.on('points', function(gdata) {
			socket.broadcast.emit('points', gdata);
		});
		socket.on('position', function(gdata) {
			socket.broadcast.emit('position', gdata);
			console.log('[SCK] position ' + gdata);
		});
	});
	return server81;
};

exports.start = start;
exports.start81 = start81;
