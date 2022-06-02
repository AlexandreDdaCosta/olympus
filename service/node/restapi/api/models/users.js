ALEX
var mongoConnection = require("mongo_connect");

exports.findByUsername = (username) => {
  mongoConnection.getInstance(function (db){
    // Query your MongoDB database.
  });
};



MongoClient.connect(url, function(err, db) {
  if (err) throw err;
  const data = { name: "Company Inc", description: "..." };

  db.collection("datas").insertOne(data, function(err, res) {
    if (err) throw err;
    console.log("1 document inserted");
    db.close();
  });
});
User.find({ name: 'Punit'}, function (err, docs) {
    if (err){
        console.log(err);
    }
    else{
        console.log("First function call : ", docs);
    }
})
exports.findByUsername = (username) => {
  return User.find(id).then((result) => {
    result = result.toJSON();
      delete result._id;
      return result;
  });
};
