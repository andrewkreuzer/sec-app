FROM golang:alpine as build

WORKDIR /app

COPY .env.prod .env

COPY go.mod ./
COPY go.sum ./
RUN go mod download
COPY *.go ./
COPY ./middleware/*.go ./middleware/

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o web .


FROM ubuntu:latest
RUN apt update && apt upgrade

RUN useradd -d /home/web -u 1000 web
# USER web

WORKDIR /home/web
COPY --from=build /app/web ./web
COPY --from=build /app/.env ./.env

COPY ./index.html index.html
COPY ./home.html home.html
COPY ./assets/ assets/

EXPOSE 80
CMD ["./web"]
