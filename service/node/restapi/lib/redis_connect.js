const DbDriver = require('redis');
const config = require('config');
const fs = require('fs');
const genericPool = require("generic-pool");
const password = fs.readFileSync(config.get('redis.password_file'), 'utf8');

function RedisPool(){};
var poolConnection;

function initPool(callback) {
  const factory = {
    create: function() {
      let client = DbDriver.createClient({
        url: 'redis://' + config.get('redis.user') + ':' + password + '@' + config.get('redis.host') + ':' + config.get('redis.port')
      });
      client.connect();
      return client;
    },
    destroy: function(client) {
      client.disconnect();
    }
  };
  const opts = {
    max: 10, // maximum size of the pool
    min: 2 // minimum size of the pool
  };
  poolConnection = genericPool.createPool(factory, opts);

  if (callback && typeof(callback) == 'function')
    callback(poolConnection);
  else
    return poolConnection;
}

function getInstance(callback) {
  if (! poolConnection) {
    initPool(callback)
  }
  else {
    if (callback && typeof(callback) == 'function')
      callback(poolConnection);
    else
      return poolConnection;
  }
}

RedisPool.initPool = initPool;
RedisPool.getInstance = getInstance;
module.exports = RedisPool;

/* USAGE EXAMPLE

  const redisConnection = require("redis_connect");
  let poolConnection = redisConnection.getInstance();
  const resourcePromise = poolConnection.acquire();
  resourcePromise
    .then(function(client) {
      client.set('restapi:test', 'SUCCESSFUL');
      poolConnection.release(client);
    })
    .catch(function(err) {
      throw(err);
    });

*/
