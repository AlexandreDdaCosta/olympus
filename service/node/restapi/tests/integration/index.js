var http = require('http');
var options = {
  host: '127.0.0.1',
  port: 8889,
  path: '/api/'
};
http.get(options, function(res){
  console.log('STATUS: ' + res.statusCode);
  console.log('HEADERS: ' + JSON.stringify(res.headers));
  res.setEncoding('utf8');
  res.on('data', function (jsonstring) {
    console.log('JSON: '+ jsonstring);
  });
}).on("error", function(e){
  console.log('ERROR: ' + e.message);
});
