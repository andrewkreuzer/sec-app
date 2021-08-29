package main

import (
  "net/http"
  "os"
  "log"
  "strings"

  "github.com/gin-gonic/gin"
  "github.com/joho/godotenv"
)

func main() {
  err := godotenv.Load()
  if err != nil {
    log.Fatal("Error loading .env file")
  }

  r := gin.Default()
  r.LoadHTMLFiles("index.html")

  r.GET("/", func(c *gin.Context) {
    c.HTML(http.StatusOK, "index.html", nil)
  })

  r.GET("/health", func(c *gin.Context) {
    c.Status(http.StatusOK)
  })

  r.GET("/ping", func(c *gin.Context) {
    c.JSON(200, gin.H{
      "message": "pong",
    })
  })

  r.Run(strings.Join([]string{":", os.Getenv("PORT")}, ""))
}
