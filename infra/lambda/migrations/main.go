package main

import (
  "context"
  "fmt"
  "log"

  "github.com/aws/aws-lambda-go/lambda"
  // "github.com/aws/aws-sdk-go-v2/config"
  // "github.com/aws/aws-sdk-go-v2/feature/rds/auth"
  "github.com/golang-migrate/migrate/v4"
  _ "github.com/golang-migrate/migrate/v4/database/mysql"
  _ "github.com/golang-migrate/migrate/v4/source/file"
  "github.com/spf13/viper"
)

type DB struct {
  name string
  username string
  password string
  host string
  port string
}

func handler(ctx context.Context) {
  viper.SetConfigType("env")
  viper.SetConfigFile(".env")
  viper.AutomaticEnv()
  if err := viper.ReadInConfig(); err != nil {
    if _, ok := err.(viper.ConfigFileNotFoundError); ok {
      log.Println("Config file not found")
    } else {
      log.Println(err)
    }
  }

  // TODO: iam db auth currently using the default user
//   cfg, err := config.LoadDefaultConfig(ctx)
//   if err != nil {
//     panic("configuration error: " + err.Error())
//   }

//   authenticationToken, err := auth.BuildAuthToken(
//     ctx,
//     fmt.Sprintf("%s:%s", viper.Get("db_host").(string), "3306"),
//     "us-east-2",
//     "migrationsLambda",
//     cfg.Credentials,
//   )
//   if err != nil {
//     panic("failed to create authentication token: " + err.Error())
//   }

  db := DB {
    name: viper.GetString("db_name"),
    username: viper.GetString("db_user"),
    host: viper.GetString("db_host"),
    port: viper.GetString("db_port"),
    password: viper.GetString("db_pass"),
  }

  file_string := fmt.Sprintf("file://%s", viper.Get("MIGRATION_DIR"))
  dsn := fmt.Sprintf(
    "mysql://%s:%s@tcp(%s:%s)/%s",
    db.username, db.password, db.host, db.port, db.name,
  )

  m, err := migrate.New(file_string, dsn)
  if err != nil {
    log.Fatal(err)
  }

  if err := m.Up(); err != nil {
    if err.Error() == "no change" {
      log.Println(err)
    } else {
      log.Fatal(err)
    }
  }
}

func main() {
  lambda.Start(handler)
}
