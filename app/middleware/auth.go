package middleware

import (
	"log"
	"net/http"
	"time"

	"github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/cookie"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt"
)

type Auth struct {
  cookieName string
  secretkey string
}

type JWTUserInfo struct {
  Name string `json:"name"`
  Kind string `json:"kind"`
}

type JWTClaims struct {
  UserInfo *JWTUserInfo `json:"userInfo"`
  *jwt.StandardClaims
}

func NewAuth(cookieName string, secretkey string) Auth {
  auth := Auth{}
  auth.cookieName = cookieName
  auth.secretkey = secretkey
  return auth
}

func (a *Auth) Middleware(cookieStore cookie.Store) gin.HandlerFunc {
  return func(c *gin.Context) {
    authCookie, ok := sessions.Default(c).Get("Authorization").(string)
    if !ok {
      log.Println("Authorization cookie not found")
      c.Redirect(http.StatusTemporaryRedirect, "/")
      c.Abort()
      return
    }
    token, err := jwt.ParseWithClaims(
      authCookie,
      &JWTClaims{},
      func(token *jwt.Token) (interface{}, error) {
        return []byte(a.secretkey), nil
    })
    if err != nil {
      log.Println("token parsing error:", err)
    }

    claims, ok := token.Claims.(*JWTClaims)
    if !ok {
      log.Println("couldn't parse claims")
    }
    if claims.ExpiresAt < time.Now().UTC().Unix() {
      log.Println("jwt is expired")
    }

    c.Next()
  }
}
