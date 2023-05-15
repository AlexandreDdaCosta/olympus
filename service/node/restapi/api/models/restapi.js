const mongoConnection = require("../../lib/mongo_connect");

async function findByUsername(username) {
  const connection = await mongoConnection.getInstance();
  const db = connection.db("restapi");
  return db.collection("auth_users").findOne({ Username: username });
}

module.exports = { findByUsername };
