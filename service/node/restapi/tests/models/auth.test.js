// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/models/auth.test.js' node

const {MongoClient} = require('mongodb');
const argon2 = require('argon2');
const config = require('config');
const fs = require('fs');
const os = require('os');
 
const hashing_config = { parallelism: config.get('argon2.parallelism'), memoryCost: config.get('argon2.memory_cost'), timeCost: config.get('argon2.time_cost') }
const test_collection = config.get('mongodb.collection_auth_users');

describe('check_password', () => {
  let connection;
  let db;
  let password;
  let restapi_password;

  if (os.userInfo().username != config.get('mongodb.user')) {
    throw new Error('Test must be run under run user '+config.get('mongodb.user'));
    process.exit(1);
  }
  try {
    password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
  } catch (err) {
    throw new Error(err);
    process.exit(1);
  }
  try {
    restapi_password = fs.readFileSync(config.get('restapi.password_file'), 'utf8');
  } catch (err) {
    throw new Error(err);
    process.exit(1);
  }

  beforeAll(async () => {
    const uri = 'mongodb://'+config.get('mongodb.user')+':'+password+'@'+config.get('mongodb.host')+':'+config.get('mongodb.port')+'/'+config.get('mongodb.database_auth');
    connection = await MongoClient.connect(uri, {});
    db = await connection.db(config.get('mongodb.database_default'));
  });

  afterAll(async () => {
    var collection = db.collection(test_collection);
    await connection.close();
  });

  it('Verify hashed node password in mongodb versus clear text on disk', async () => {
    var collection = db.collection(test_collection);
    var searchedItem = await collection.findOne({Username : config.get('mongodb.user')});
    var hashed_password = searchedItem['Password'];
    var result = await argon2.verify(hashed_password, restapi_password, hashing_config);
    expect(result).toEqual(true);
  });
});
