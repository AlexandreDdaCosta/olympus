// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/token.test.js' node

const config = require("config");
const fs = require("fs");
const https = require("https");
const os = require("os");

describe("Access tokens for various data providers.", () => {
  let accessToken;
  let password;
  let refreshToken;
  let token;
  let url;

  const options = {
    ca: fs.readFileSync(config.get("ssl_server.ca_file")),
    cert: fs.readFileSync(config.get("ssl_server.client_cert_file")),
    hostname: config.get("ssl_server.host"),
    key: fs.readFileSync(config.get("ssl_server.client_key_file")),
    port: config.get("ssl_server.port"),
  };

  beforeAll(async () => {
    if (os.userInfo().username !== config.get("restapi.user")) {
      throw new Error(
        `Test must be run under run user ${config.get("restapi.user")}`
      );
    }
    try {
      password = fs.readFileSync(config.get("restapi.password_file"), "utf8");
    } catch (err) {
      throw new Error(err);
    }
  });

  it("Login, get access and refresh tokens.", async () => {
    const loginPromise = () => {
      return new Promise((resolve, reject) => {
        const loginData = JSON.stringify({
          username: config.get("restapi.user"),
          password,
        });
        options.headers = {
          "Content-Type": "application/json",
          "Content-Length": loginData.length,
        };
        options.method = "POST";
        options.path = "/auth/login";
        const req = https.request(options, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({
              statusCode: res.statusCode,
              headers: res.headers,
              body,
            });
          });
        });
        req.on("error", reject);
        req.write(loginData);
        req.end();
      });
    };

    const data = await loginPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual("Login successful.");
    accessToken = JSON.parse(data.body).access_token;
    refreshToken = JSON.parse(data.body).refresh_token;
  });

  it("Omit provider name.", async () => {
    const tokenPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/token/equities";
        const req = https.request(options, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({ statusCode: res.statusCode, body });
          });
        });
        req.on("error", reject);
        req.end();
      });
    };

    const data = await tokenPromise();
    expect(data.statusCode).toBe(404);
  });

  it("Get Alpha Vantage access key.", async () => {
    const tokenPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/token/equities/AlphaVantage";
        const req = https.request(options, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({ statusCode: res.statusCode, body });
          });
        });
        req.on("error", reject);
        req.end();
      });
    };

    const data = await tokenPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual("Request successful.");
    url = JSON.parse(data.body).url;
    token = JSON.parse(data.body).token;
  });

  it("Get TD Ameritrade access key.", async () => {
    const tokenPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/token/equities/TDAmeritrade";
        const req = https.request(options, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({ statusCode: res.statusCode, body });
          });
        });
        req.on("error", reject);
        req.end();
      });
    };

    const data = await tokenPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual("Request successful.");
    url = JSON.parse(data.body).url;
    token = JSON.parse(data.body).token;
  });

  it("Test TD Ameritrade access key with connection.", async () => {
    const dataPromise = () => {
      return new Promise((resolve, reject) => {
        const connectOptions = {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          hostname: url,
          method: "GET",
          path: "/v1/marketdata/$COMPX/movers?direction=up&change=percent",
          port: 443,
        };
        const req = https.request(connectOptions, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({ statusCode: res.statusCode, body });
          });
        });
        req.on("error", reject);
        req.end();
      });
    };

    const data = await dataPromise();
    expect(data.statusCode).toBe(200);
  });

  it("Logout.", async () => {
    const logoutPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${refreshToken}`,
          "Content-Type": "application/json",
        };
        options.method = "DELETE";
        options.path = "/auth/logout";
        const req = https.request(options, (res) => {
          let body = "";
          res.on("data", function readDataChunks(chunk) {
            body += chunk.toString();
          });
          res.on("error", reject);
          res.on("end", () => {
            resolve({
              statusCode: res.statusCode,
              headers: res.headers,
              body,
            });
          });
        });
        req.on("error", reject);
        req.end();
      });
    };

    const data = await logoutPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual("Logout successful.");
  });
});
