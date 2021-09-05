FROM public.ecr.aws/bitnami/golang:latest as build

WORKDIR /app

COPY .env.prod .env

COPY go.mod ./
COPY go.sum ./
RUN go mod download
COPY *.go ./

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o web .


FROM ubuntu:latest
RUN apt update && apt upgrade

RUN useradd -d /home/web -u 1000 web
USER web

WORKDIR /home/web
COPY --from=build /app/web ./web
COPY --from=build /app/.env ./.env

COPY ./index.html index.html

EXPOSE 8080
CMD ["./web"]
