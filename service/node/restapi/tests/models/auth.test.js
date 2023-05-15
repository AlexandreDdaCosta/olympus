// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/models/auth.test.js' node

const { MongoClient } = require("mongodb");
const argon2 = require("argon2");
const config = require("config");
const fs = require("fs");
const os = require("os");

const hashingConfig = {
  parallelism: config.get("argon2.parallelism"),
  memoryCost: config.get("argon2.memory_cost"),
  timeCost: config.get("argon2.time_cost"),
};
const testCollection = config.get("mongodb.collection_auth_users");

describe("check_password", () => {
  let connection;
  let db;
  let password;
  let restapiPassword;

  if (os.userInfo().username !== config.get("mongodb.user")) {
    throw new Error(
      `Test must be run under run user ${config.get("mongodb.user")}`
    );
  }
  try {
    password = fs.readFileSync(config.get("mongodb.password_file"), "utf8");
  } catch (err) {
    throw new Error(err);
  }
  try {
    restapiPassword = fs.readFileSync(
      config.get("restapi.password_file"),
      "utf8"
    );
  } catch (err) {
    throw new Error(err);
  }

  beforeAll(async () => {
    const uri = `mongodb://${config.get(
      "mongodb.user"
    )}:${password}@${config.get("mongodb.host")}:${config.get(
      "mongodb.port"
    )}/${config.get("mongodb.database_auth")}`;
    connection = await MongoClient.connect(uri, {});
    db = connection.db(config.get("mongodb.database_default"));
  });

  afterAll(async () => {
    await connection.close();
  });

  it("Verify hashed node password in mongodb versus clear text on disk", async () => {
    const collection = db.collection(testCollection);
    const searchedItem = await collection.findOne({
      Username: config.get("mongodb.user"),
    });
    const hashedPassword = searchedItem.Password;
    const result = await argon2.verify(
      hashedPassword,
      restapiPassword,
      hashingConfig
    );
    expect(result).toEqual(true);
  });
});
