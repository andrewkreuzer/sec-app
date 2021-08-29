FROM public.ecr.aws/bitnami/golang:latest

WORKDIR /app

COPY go.mod ./
COPY go.sum ./
RUN go mod download
COPY *.go ./

RUN go build -o web

COPY ./index.html /usr/share/nginx/html/index.html

EXPOSE 80
CMD ["./web"]
