const MongoClient = require('mongodb').MongoClient;
const config = require('config');
const fs = require('fs');

const password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
const uri = 'mongodb://'+config.get('mongodb.user')+':'+password+'@'+config.get('mongodb.host')+':'+config.get('mongodb.port')+'/'+config.get('mongodb.database_auth');

const option = {
    appname: 'node_restapi',
    maxPoolSize: 100
};

function MongoPool(){};
var pool_connection;

function initPool(callback) {
  MongoClient.connect(uri, option, function(err, connection) {
    if (err) throw err;
    // await connection.db("admin").command({ ping: 1 });
    pool_connection = connection;
    if (callback && typeof(callback) == 'function')
        callback(pool_connection);
  });
  return MongoPool;
}

function getInstance(callback) {
  if (! pool_connection) {
    initPool(callback)
  }
  else {
    if (callback && typeof(callback) == 'function')
      callback(pool_connection);
  }
}

MongoPool.initPool = initPool;
MongoPool.getInstance = getInstance;
module.exports = MongoPool;
/*
const MongoPool = require("mongo-connect");
MongoPool.getInstance(function (connection){
  // Query MongoDB using connection
  db = await connection.db(config.get('mongodb.database_default'));
  var collection = db.collection(test_collection);
});
*/
