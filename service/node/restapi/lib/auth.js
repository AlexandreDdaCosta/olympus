const jwt = require("jsonwebtoken");

let refreshTokens = []

function generateAccessToken(user) {
    return jwt.sign(user, process.env.ACCESS_TOKEN_SECRET, {expiresIn: "15m"})
}

function generateRefreshToken(user) {
    const refreshToken = jwt.sign(user, process.env.REFRESH_TOKEN_SECRET, {expiresIn: "20m"})
    refreshTokens.push(refreshToken)
    return refreshToken
}

function validateToken(req, res, next) {
    const authHeader = req.headers["authorization"];
    const [identifier, token] = authHeader.split(' ');
    // The authorization header should contain the structure "Bearer <token>"
    if (identifier != 'Bearer') {
        res.sendStatus(400).send("Bad authorization header");
    }
    elsif (token == null) {
        res.sendStatus(400).send("Token not present");
    }
    else {
        jwt.verify(token, process.env.ACCESS_TOKEN_SECRET, (err, user) => {
            if (err) { 
                res.status(403).send("Token invalid");
            }
            else {
                req.user = user;
                next();
            }
        })
    }
}
