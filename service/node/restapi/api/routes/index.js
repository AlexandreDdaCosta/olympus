var express = require('express');
var router = express.Router();
router.get('/', function(req, res) {
    res.json({ message: 'Olympus back-end API listening for requests via express/node.js.' });   
});
module.exports = router; 
