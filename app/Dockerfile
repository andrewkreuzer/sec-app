FROM public.ecr.aws/bitnami/golang:latest as build

WORKDIR /app

COPY .env.prod .env

COPY go.mod ./
COPY go.sum ./
RUN go mod download
COPY *.go ./

RUN go build -o web

COPY ./index.html /usr/share/nginx/html/index.html


FROM alpine:latest
WORKDIR /app
COPY --from=build /app/web web

EXPOSE 80
CMD ["./web"]
