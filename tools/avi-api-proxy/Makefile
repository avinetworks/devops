OUT = avi-api-proxy

default:
	$(MAKE) clean
	$(MAKE) build
clean:
	rm -f $(OUT)
build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -tags netgo -ldflags '-w' -o $(OUT)
all:
	$(MAKE) clean
	$(MAKE) build
