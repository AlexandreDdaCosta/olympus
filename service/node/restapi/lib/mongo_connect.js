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

async function initPool(callback) {
  let connection;
  try {
     connection = await MongoClient.connect(uri, option);
  } catch (err) {
    throw new Error(err);
    process.exit(1);
  }
  if (! connection) {
    throw new Error('MongoDB connection failure.');
    process.exit(1);
  }
  //await connection.db("admin").command({ ping: 1 });
  pool_connection = connection;
  if (callback && typeof(callback) == 'function')
    callback(pool_connection);
  return MongoPool;
}

async function getInstance(callback) {
  if (! pool_connection) {
    await initPool(callback)
  }
  else {
    if (callback && typeof(callback) == 'function')
      callback(pool_connection);
    else
      return pool_connection;
  }
}

MongoPool.initPool = initPool;
MongoPool.getInstance = getInstance;
module.exports = MongoPool;
