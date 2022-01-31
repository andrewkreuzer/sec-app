package main

import (
  // "context"
  "database/sql"
  "encoding/json"
  "fmt"
  "io/ioutil"
  "log"
  "net/http"
  "os"
  "time"

  "sec-app/middleware"

  // "github.com/aws/aws-sdk-go-v2/config"
  // "github.com/aws/aws-sdk-go-v2/feature/rds/auth"
  "github.com/golang-jwt/jwt"
  "github.com/gin-gonic/gin"
  _ "github.com/go-sql-driver/mysql"
  "github.com/joho/godotenv"
  "github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/cookie"
)


type User struct {
  Id int
  Name string
  Password string
}

type DB struct {
  name string
  username string
  password string
  host string
  port string
  opts string
}

type ginGroups struct {
  auth *gin.RouterGroup
}

type Site struct {
  gin *gin.Engine
  db  *sql.DB
  store cookie.Store
  ginGroups ginGroups
}

func (s *Site) Init() {
  if err:= godotenv.Load(); err != nil {
    log.Fatal("Environment loading failed")
  }

  s.store = cookie.NewStore([]byte("secret"))
  auth := middleware.NewAuth(
    "sec-app_xBIKJlsidfHguohHHAkajsfagjcSlgWhrkqNmJXU",
    os.Getenv("JWT_SECRET"),
  )
  s.gin.Use(
    gin.LoggerWithWriter(gin.DefaultWriter, "/health"),
    gin.Recovery(),
    sessions.Sessions("default", s.store),
  )
  s.gin.LoadHTMLFiles("index.html", "home.html")

  s.ginGroups.auth = s.gin.Group("/")
  s.ginGroups.auth.Use(
    auth.Middleware(s.store),
  )

  s.db = s.dbConnection()
}

func (s *Site) home(c *gin.Context) {
  c.HTML(http.StatusOK, "home.html", nil)
}

func (s *Site) signup(c *gin.Context) {
  body, _ := ioutil.ReadAll(c.Request.Body)
  var user User
  err := json.Unmarshal(body, &user)
  if err != nil {
    fmt.Println("error:", err)
  }

  var dbUser User
  err = s.db.QueryRow("select ID, Username from Users where Username=?", user.Name).Scan(&dbUser.Id, &dbUser.Name)
  if err != nil {
    log.Println(err)
  }

  if dbUser.Name == user.Name {
    c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
      "failed": "Username taken",
    })

    return
  }

  stmt, err := s.db.Prepare("insert into Users values (NUll, ?, ?)")
  if err != nil {
    fmt.Println("error:", err)
  }

  stmt.Exec(user.Name, user.Password)
  defer stmt.Close()

  c.JSON(http.StatusOK, gin.H{
    "body": user.Name,
  })
}

func (s *Site) loginPage(c *gin.Context) {
  // TODO: could this infinite loop? between this as the auth middleware?
  if sessions.Default(c).Get("Authorization") != nil {
    c.Redirect(http.StatusTemporaryRedirect, "/home")
    return
  }
  c.HTML(http.StatusOK, "index.html", nil)
}

func (s *Site) login(c *gin.Context) {
    body, _ := ioutil.ReadAll(c.Request.Body)
    var requestedUser User
    err := json.Unmarshal(body, &requestedUser)
    if err != nil {
      fmt.Println("error:", err)
    }

    var dbUser User
    err = s.db.QueryRow("select ID, Username, Password from Users where Username=?", requestedUser.Name).Scan(&dbUser.Id, &dbUser.Name, &dbUser.Password)

    if (dbUser.Password == requestedUser.Password) {
      // TODO: I don't know go well enough to remove the unkeyed fields warning
      //       it's due to the JWTClaims struct not being able to state a key
      //       for the jwt.StandardClaims type and jwt's inability to convert
      //       JWTCLaims to a Claims type, could implement Valid() but I
      //       don't want to handle validation
      claims := middleware.JWTClaims{
        &middleware.JWTUserInfo{
          Name: dbUser.Name,
          Kind: "basic",
        },
        &jwt.StandardClaims{
          ExpiresAt: time.Now().Add(time.Minute * 30).Unix(),
          Issuer:    "sec-app.andrewkreuzer.com",
        },
      }
      token := jwt.NewWithClaims(jwt.SigningMethodHS256, &claims)
      tokenString, err := token.SignedString([]byte(os.Getenv("JWT_SECRET")))
      if err != nil {
        fmt.Println("error: ", err)
      }

      c.Header("Authorization", fmt.Sprintf("Bearer %v", tokenString))
      s := sessions.Default(c)
      s.Options(sessions.Options{
          Path:     "/",
          Domain:   os.Getenv("APP_URL"),
          MaxAge:   0,
          Secure:   true,
          HttpOnly: true,
      })
      s.Set("Authorization", tokenString)
      s.Save()
      c.JSON(http.StatusOK, gin.H{
        "result": "success",
      })
    } else {
      c.JSON(http.StatusNotFound, gin.H{
        "result": "failed",
      })
    }
}

func (s *Site) health(c *gin.Context) {
  c.Status(http.StatusOK)
}

 func (s *Site) users(c *gin.Context) {
  rows, err := s.db.Query("select * from Users")
  if err != nil {
    fmt.Println("error:", err)
  }

  users := []string{}
  for rows.Next() {
    var (
      id   int64
      name string
      password string
    )
    if err := rows.Scan(&id, &name, &password); err != nil {
      log.Fatal(err)
    }
    users = append(users, name)
  }

  c.JSON(http.StatusOK, gin.H{
    "users": users,
  })
}

func (s *Site) Routes() {
  s.gin.GET("/", s.loginPage)
  s.gin.Static("/assets", "./assets")
  s.gin.GET("/health", s.health)
  s.gin.POST("/signup", s.signup)
  s.gin.GET("/login", s.loginPage)
  s.gin.POST("/login", s.login)
  s.ginGroups.auth.GET("/home", s.home)
  s.ginGroups.auth.GET("/users", s.users)
}

func (s *Site) dbConnection() (*sql.DB) {
  db := DB {
    name: os.Getenv("DB_NAME"),
    username: os.Getenv("DB_USER"),
    host: os.Getenv("DB_HOST"),
    port: os.Getenv("DB_PORT"),

    password: os.Getenv("DB_PASS"),
  }

  // if os.Getenv("ENVIRONMENT") != "dev" {
  //   db_ctx := context.Background()
  //   cfg, err := config.LoadDefaultConfig(db_ctx)
  //   if err != nil {
  //     panic("configuration error: " + err.Error())
  //   }

  //   authenticationToken, err := auth.BuildAuthToken(
  //     db_ctx,
  //     fmt.Sprintf("%s:%s", db.host, "3306"),
  //     "us-east-2",
  //     db.username,
  //     cfg.Credentials,
  //   )
  //   if err != nil {
  //     panic("failed to create authentication token: " + err.Error())
  //   }

  //   db.opts = "?tls=true&allowCleartextPasswords=true" 
  //   db.password = authenticationToken
  // } else {
  //   db.password = os.Getenv("DB_PASS")
  // }

  dsn := fmt.Sprintf(
    "%s:%s@tcp(%s:%s)/%s%s",
    db.username, db.password, db.host, db.port, db.name, db.opts,
  )

  conn, err := sql.Open("mysql", dsn)
  if err != nil {
    panic(err)
  }
  conn.SetConnMaxLifetime(time.Minute * 3)
  conn.SetMaxOpenConns(10)
  conn.SetMaxIdleConns(10)

  return conn
}

func main() {
  site := Site{
    gin: gin.New(),
  }

  site.Init()
  site.Routes()
  site.gin.Run()
}
