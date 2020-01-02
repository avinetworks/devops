FROM golang:latest AS build
ENV BUILD_PATH="avi-api-proxy"
RUN mkdir -p $GOPATH/src/$BUILD_PATH
COPY . $GOPATH/src/$BUILD_PATH
WORKDIR $GOPATH/src/$BUILD_PATH
RUN go mod download
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -tags netgo -ldflags '-w' -o $GOPATH/avi-api-proxy

FROM alpine:latest
COPY --from=build /go/avi-api-proxy .
EXPOSE 8080
ENTRYPOINT ["/avi-api-proxy"]
