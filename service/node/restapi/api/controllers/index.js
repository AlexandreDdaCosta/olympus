const newIndex = (_req, res) => {
  console.log("/ index.js");
  res.json({
    message: "Olympus back-end API listening for requests via express/node.js.",
  });
};
module.exports = { newIndex };
