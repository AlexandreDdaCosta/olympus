var mongoConnection = require("mongo_connect");

async function findByUsername(username) {
  const connection = await mongoConnection.getInstance();
  let db = connection.db('user_node');
  return await db.collection('auth_users').findOne({ 'Username': username });
}

module.exports = { findByUsername }
