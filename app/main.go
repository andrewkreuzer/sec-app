package main

import (
	"database/sql"
	"io/ioutil"
	"log"
	"net/http"
	"time"
  "encoding/json"
  "fmt"

	"github.com/gin-gonic/gin"
	_ "github.com/go-sql-driver/mysql"
	"github.com/joho/godotenv"
)

type User struct {
  Id int
  Name string
  Password string
}

func main() {
  err := godotenv.Load()
  if err != nil {
    log.Fatal("Error loading .env file")
  }

  db, err := sql.Open("mysql", "root:foobarbaz@tcp(localhost:3307)/sec-app")
  if err != nil {
    panic(err)
  }

  db.SetConnMaxLifetime(time.Minute * 3)
  db.SetMaxOpenConns(10)
  db.SetMaxIdleConns(10)

  r := gin.Default()
  r.LoadHTMLFiles("index.html")

  r.GET("/", func(c *gin.Context) {
    c.HTML(http.StatusOK, "index.html", nil)
  })

  r.GET("/health", func(c *gin.Context) {
    c.Status(http.StatusOK)
  })

  r.POST("/login", func(c *gin.Context) {
    body, _ := ioutil.ReadAll(c.Request.Body)
    var requestedUser User
    err = json.Unmarshal(body, &requestedUser)
    if err != nil {
        fmt.Println("error:", err)
    }

    var dbUser User
    err = db.QueryRow("select ID, Username, Password from Users where Username=?", requestedUser.Name).Scan(&dbUser.Id, &dbUser.Name, &dbUser.Password)

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
    err = json.Unmarshal(body, &user)
    if err != nil {
        fmt.Println("error:", err)
    }

    stmt, err := db.Prepare("insert into Users values (NUll, ?, ?)")
    if err != nil {
        fmt.Println("error:", err)
    }

    // log.Println(user.Name, user.Password)
    stmt.Exec(user.Name, user.Password)
    defer stmt.Close()

    c.JSON(http.StatusOK, gin.H{
      "body": user.Name,
    })
  })

  r.GET("/ping", func(c *gin.Context) {
    c.JSON(http.StatusOK, gin.H{
      "message": "pong",
    })
  })

  r.Run()
}
