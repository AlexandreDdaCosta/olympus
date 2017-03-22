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
var port = process.env.PORT || 8889;
var router = express.Router();
router.get('/', function(req, res) {
    res.json({ message: 'Olympus back-end API listening for requests' });   
});
app.use('/api', router);
app.listen(port);
console.log('node.js REST API listening on port ' + port);
