const { MongoClient } = require("mongodb");
const config = require("config");
const fs = require("fs");

const password = fs.readFileSync(config.get("mongodb.password_file"), "utf8");
const uri = `mongodb://${config.get("mongodb.user")}:${password}@${config.get(
  "mongodb.host"
)}:${config.get("mongodb.port")}/${config.get("mongodb.database_auth")}`;

const option = {
  appname: "node_restapi",
  maxPoolSize: 100,
};

function MongoPool() {}
let poolConnection;

async function initPool(callback) {
  let connection;
  try {
    connection = await MongoClient.connect(uri, option);
  } catch (err) {
    throw new Error(err);
  }
  if (!connection) {
    throw new Error("MongoDB connection failure.");
  }
  // await connection.db("admin").command({ ping: 1 });
  poolConnection = connection;
  if (callback && typeof callback === "function") callback(poolConnection);
  return MongoPool;
}

async function getInstance(callback) {
  if (!poolConnection) {
    await initPool(callback);
  } else if (callback && typeof callback === "function")
    callback(poolConnection);
  else return poolConnection;
  return false;
}

MongoPool.initPool = initPool;
MongoPool.getInstance = getInstance;
module.exports = MongoPool;
