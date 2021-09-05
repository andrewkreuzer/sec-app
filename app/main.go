package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/aws/aws-sdk-go-v2/config"
  "github.com/aws/aws-sdk-go/aws"
  "github.com/aws/aws-sdk-go/aws/session"
  "github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go-v2/feature/rds/auth"
	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
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

func db() (*sql.DB) {
  db := DB {
    name: os.Getenv("DB_NAME"),
    username: os.Getenv("DB_USER"),
    host: os.Getenv("DB_HOST"),
    port: os.Getenv("DB_PORT"),
  }

  if os.Getenv("ENVIRONMENT") != "dev" {
    db_ctx := context.Background()
    cfg, err := config.LoadDefaultConfig(db_ctx)
    if err != nil {
      panic("configuration error: " + err.Error())
    }

    sess := session.Must(session.NewSessionWithOptions(session.Options{
    SharedConfigState: session.SharedConfigEnable,
    }))
    svc := s3.New(sess, &aws.Config{
      Region: aws.String("us-east-2"),
    })

    result, err := svc.ListBuckets(nil)

    if err != nil {
      log.Default("Unable to list buckets, %v", err)
    }

    fmt.Println("My buckets now are:\n")

    for _, b := range result.Buckets {
      fmt.Printf(aws.StringValue(b.Name) + "\n")
    }

    authenticationToken, err := auth.BuildAuthToken(
      db_ctx,
      fmt.Sprintf("%s:%s", db.host, "3306"),
      "us-east-2",
      db.username,
      cfg.Credentials,
    )
    if err != nil {
      panic("failed to create authentication token: " + err.Error())
    }

    db.opts = "?tls=true&allowCleartextPasswords=true" 
    db.password = authenticationToken
  } else {
    db.password = os.Getenv("DB_PASS")
  }

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
  err := godotenv.Load()
  if err != nil {
    log.Fatal("Environment loading failed")
  }

  conn := db()

  r := gin.Default()
  r.LoadHTMLFiles("index.html")

  r.GET("/", func(c *gin.Context) {
    c.HTML(http.StatusOK, "index.html", nil)
  })

  r.GET("/health", func(c *gin.Context) {
    c.Status(http.StatusOK)
  })

  r.GET("/users", func(c *gin.Context) {
    rows, err := conn.Query("select * from Users")
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
  })

  r.POST("/login", func(c *gin.Context) {
    body, _ := ioutil.ReadAll(c.Request.Body)
    var requestedUser User
    err := json.Unmarshal(body, &requestedUser)
    if err != nil {
        fmt.Println("error:", err)
    }

    var dbUser User
    err = conn.QueryRow("select ID, Username, Password from Users where Username=?", requestedUser.Name).Scan(&dbUser.Id, &dbUser.Name, &dbUser.Password)

    log.Println(dbUser.Password, requestedUser.Password)
    if (dbUser.Password == requestedUser.Password) {
      c.JSON(http.StatusOK, gin.H{
        "result": "logged in",
      })
    } else {
      c.JSON(http.StatusNotFound, gin.H{
        "result": "failed",
      })
    }

  })

  r.POST("/signup", func(c *gin.Context) {
    body, _ := ioutil.ReadAll(c.Request.Body)
    var user User
    err := json.Unmarshal(body, &user)
    if err != nil {
        fmt.Println("error:", err)
    }

    var dbUser User
    err = conn.QueryRow("select ID, Username from Users where Username=?", user.Name).Scan(&dbUser.Id, &dbUser.Name)
    if err != nil {
      log.Println(err)
    }

    if dbUser.Name == user.Name {
      c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
        "failed": "Username taken",
      })

      return
    }

    stmt, err := conn.Prepare("insert into Users values (NUll, ?, ?)")
    if err != nil {
      fmt.Println("error:", err)
    }

    stmt.Exec(user.Name, user.Password)
    defer stmt.Close()

    c.JSON(http.StatusOK, gin.H{
      "body": user.Name,
    })
  })

  r.Run()
}
