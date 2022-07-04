FROM migrate/migrate

COPY migrations migrations

ENTRYPOINT migrate -path=./migrations -database="mysql://$DB_USER:$DB_PASS@tcp(mariadb:3306)/sec-app" up
