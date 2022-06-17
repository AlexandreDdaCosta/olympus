const config = require('config');
const fs = require('fs');
const password = fs.readFileSync(config.get('redis.password_file'), 'utf8');
const redis_connection_pool = require('redis-connection-pool');

const redis = require('redis');
let client = redis.createClient({
  url: 'redis://' + config.get('redis.user') + ':' + password + '@' + config.get('redis.host') + ':' + config.get('redis.port')
});
client.connect();
const dateObj = new Date();
client.set('user_node:test', dateObj.getTime());

function RedisPool(){};
var pool_connection;

function initPool(callback) {
  console.log(redis_connection_pool);
  let typeit = typeof redis_connection_pool;
  console.log(typeit);
  let pool;
  //pool = new redis_connection_pool.RedisConnectionPool('restapiPool', {
  //pool = require('redis-connection-pool')('myRedisPool', {
  pool = redis_connection_pool.RedisConnectionPoolFactory('restapiPool', {
    max_clients: 10,
    redis: {
      host: '127.0.0.1',
      password: password,
      port: 6379,
      username: config.get('redis.user')
    }
  });
  pool.init();
  console.log(pool);
  pool.set('user_node:test','SUCCESS!');
  pool_connection = pool;
  if (callback && typeof(callback) == 'function') {
    callback(pool_connection);
  }
  return RedisPool;
}

function getInstance(callback) {
  if (! pool_connection) {
    initPool(callback)
  }
  else {
    if (callback && typeof(callback) == 'function')
      callback(pool_connection);
    else
      return pool_connection;
  }
}

RedisPool.initPool = initPool;
RedisPool.getInstance = getInstance;
module.exports = RedisPool;
