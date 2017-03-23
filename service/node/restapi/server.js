var fs = require('fs');
var express = require('express');
var bodyParser = require('body-parser');
var process = require('process');
fs.writeFile("/var/run/node.pid", process.pid, function(err) 
{
    if (err) 
    {
        return console.log(err);
    }
}); 
var app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
var routes = require('./api/routes');
app.use('/api', routes);
var port = 8889;
app.listen(port);
console.log('node.js REST API listening on port ' + port);
