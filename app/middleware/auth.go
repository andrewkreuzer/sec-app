package middleware

import (
	"fmt"
	"log"
	"net/http"
	"os"
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
  Name string
  Kind string
}

type JWTClaims struct {
  *jwt.StandardClaims
  JWTUserInfo
}

func NewAuth(cookieName string, secretkey string) Auth {
  auth := Auth{}
  auth.cookieName = cookieName
  auth.secretkey = secretkey
  return auth
}

func (a *Auth) Middleware(cookieStore cookie.Store) gin.HandlerFunc {
  return func(c *gin.Context) {
    authHeader, ok := sessions.Default(c).Get("Authorization").(string)
    if !ok {
      log.Println("Authorization Header not found")
      c.Redirect(http.StatusTemporaryRedirect, "/")
    }
    token, err := jwt.ParseWithClaims(
      authHeader,
      &JWTClaims{},
      func(token *jwt.Token) (interface{}, error) {
        return []byte(os.Getenv("JWT_TOKEN")), nil
    })
    if err != nil {
      fmt.Println("error:", err)
    }

    claims, ok := token.Claims.(*JWTClaims)
    if !ok {
      fmt.Println("couldn't parse claims")
    }
    if claims.ExpiresAt < time.Now().UTC().Unix() {
      fmt.Println("jwt is expired")
    }

    // username := claims.Username

    c.Next()
  }
}
