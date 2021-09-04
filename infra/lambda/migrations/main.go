package main

import (
    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/github"
)

func main() {
    m, err := migrate.New(
        "file://migrations",
        "mysql://root:foobarbaz@tcp(localhost:3307)/sec-app")
    m.Steps(2)
}
