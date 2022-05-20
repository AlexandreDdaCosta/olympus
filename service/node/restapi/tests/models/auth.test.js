const {MongoClient} = require('mongodb');
const argon2 = require('argon2');
const config = require('config');
const crypto = require('crypto');
const fs = require('fs');
 
const hashingConfig = { parallelism: config.get('argon2.parallelism'), memoryCost: config.get('argon2.memory_cost'), timeCost: config.get('argon2.time_cost') }
 
async function hashPassword(password) {
    let salt = crypto.randomBytes(config.get('argon2.salt_bytes'));
    return await argon2.hash(password, { ...hashingConfig, salt })
}
 
async function verifyPasswordWithHash(clear_password, hash) {
    password = fs.readFileSync(config.get('mongodb.password_file'), 'utf8');
    const uri = 'mongodb://'+config.get('mongodb.user')+':'+password+'@'+config.get('mongodb.host')+':'+config.get('mongodb.port')+'/'+config.get('mongodb.database_auth');
    connection = await MongoClient.connect(uri, {});
    db = await connection.db(config.get('mongodb.database_default'));
    var collection = db.collection('auth_users');
    searchedItem = await collection.findOne({Username : "olympus"});
    console.log(searchedItem);
    hashed_password = searchedItem['Password'];
    await connection.close();
    // await argon2.verify(hash, clear_password, hashingConfig);
    return await argon2.verify(hashed_password, clear_password, hashingConfig);
}
 
hashPassword("foobar").then(async (hash) => {
    console.log("Hash + salt of the password:", hash)
    console.log("Password verification success:", await verifyPasswordWithHash("foobar", hash));
});
