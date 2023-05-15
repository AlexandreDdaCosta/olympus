// sudo su -s /bin/bash -c 'source /srv/www/node/restapi/tests/test_source.sh; cd /srv/www/node/restapi; npm test ./tests/routes/auth.test.js' node

const config = require("config");
const fs = require("fs");
const https = require("https");
const os = require("os");

describe("Login, refresh token, and logout from node restapi.", () => {
  let accessToken;
  let oldAccessToken;
  let oldRefreshToken;
  let password;
  let refreshToken;

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

  it("Missing user name.", async () => {
    const loginPromise = () => {
      return new Promise((resolve, reject) => {
        const loginData = JSON.stringify({
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
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual("Login failed.");
  });

  it("Invalid user name.", async () => {
    const loginPromise = () => {
      return new Promise((resolve, reject) => {
        const loginData = JSON.stringify({
          username: "foobar",
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Bad password.", async () => {
    const loginPromise = () => {
      return new Promise((resolve, reject) => {
        const loginData = JSON.stringify({
          username: config.get("restapi.user"),
          password: "foobar",
        });
        options.headers = {
          "Content-Type": "application/json",
          "Content-Length": loginData.length,
        };
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
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual("Login failed.");
  });

  it("Invalid password.", async () => {
    const loginPromise = () => {
      return new Promise((resolve, reject) => {
        const loginData = JSON.stringify({
          username: config.get("restapi.user"),
          password:
            "1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
        });
        options.headers = {
          "Content-Type": "application/json",
          "Content-Length": loginData.length,
        };
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
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

  it("Access with missing authorization header.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/auth/ping";
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Access with bad authorization header.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: "Bearing gifts",
          "Content-Type": "application/json",
        };
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Access with invalid access token.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: "Bearer 1234567890",
          "Content-Type": "application/json",
        };
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Access with valid access token.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual(
      "Give me a ping, Vasili. One ping only, please."
    );
  });

  it("Access with valid refresh token.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${refreshToken}`,
          "Content-Type": "application/json",
        };
        options.path = "/auth/pingr";
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual(
      "Give me a ping, Vasili. One ping only, please."
    );
  });

  it("Refresh tokens, missing user name.", async () => {
    const refreshPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${refreshToken}`,
          "Content-Type": "application/json",
        };
        options.method = "POST";
        options.path = "/auth/refresh";
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

    const data = await refreshPromise();
    expect(data.statusCode).toBe(400);
    expect(JSON.parse(data.body).message).toEqual("Refresh failed.");
  });

  it("Refresh tokens, missing token.", async () => {
    const refreshPromise = () => {
      return new Promise((resolve, reject) => {
        const refreshData = JSON.stringify({
          username: config.get("restapi.user"),
        });
        options.headers = {
          "Content-Type": "application/json",
          "Content-Length": refreshData.length,
        };
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
        req.write(refreshData);
        req.end();
      });
    };

    const data = await refreshPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Refresh tokens, token/username mismatch.", async () => {
    const refreshPromise = () => {
      return new Promise((resolve, reject) => {
        const refreshData = JSON.stringify({
          username: "foobar",
        });
        options.headers = {
          Authorization: `Bearer ${refreshToken}`,
          "Content-Type": "application/json",
          "Content-Length": refreshData.length,
        };
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
        req.write(refreshData);
        req.end();
      });
    };

    const data = await refreshPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Refresh tokens, mixed up token.", async () => {
    const refreshPromise = () => {
      return new Promise((resolve, reject) => {
        const refreshData = JSON.stringify({
          username: config.get("restapi.user"),
        });
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
          "Content-Length": refreshData.length,
        };
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
        req.write(refreshData);
        req.end();
      });
    };

    const data = await refreshPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Refresh tokens.", async () => {
    const refreshPromise = () => {
      return new Promise((resolve, reject) => {
        const refreshData = JSON.stringify({
          username: config.get("restapi.user"),
        });
        options.headers = {
          Authorization: `Bearer ${refreshToken}`,
          "Content-Type": "application/json",
          "Content-Length": refreshData.length,
        };
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
        req.write(refreshData);
        req.end();
      });
    };

    // Here we pause execution for a second which is the time resolution for all tokens.
    // Without a pause, the new tokens may be identical to the old ones!
    function freeze(time) {
      const stop = new Date().getTime() + time;
      while (new Date().getTime() < stop);
    }
    freeze(1000);
    const data = await refreshPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual("Refresh successful.");
    oldAccessToken = accessToken;
    oldRefreshToken = refreshToken;
    accessToken = JSON.parse(data.body).access_token;
    refreshToken = JSON.parse(data.body).refresh_token;
  });

  it("Access with old access token (after refresh).", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${oldAccessToken}`,
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/auth/ping";
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Access with valid new access token.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(200);
    expect(JSON.parse(data.body).message).toEqual(
      "Give me a ping, Vasili. One ping only, please."
    );
  });

  it("Logout with invalid token (old refresh token).", async () => {
    const logoutPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${oldRefreshToken}`,
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
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

  it("Access after logout with invalidated access token.", async () => {
    const pingPromise = () => {
      return new Promise((resolve, reject) => {
        options.headers = {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        };
        options.method = "GET";
        options.path = "/auth/ping";
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

    const data = await pingPromise();
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });

  it("Logout with invalid token (refresh token).", async () => {
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
    expect(data.statusCode).toBe(401);
    expect(JSON.parse(data.body).message).toEqual("Access denied.");
  });
});
