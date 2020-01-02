package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"avi-api-proxy/session"
	"github.com/golang/glog"
	"github.com/julienschmidt/httprouter"
)

func proxyErrorResponse(w http.ResponseWriter, err *session.AviError) {
	w.Header().Set("Content-Type", "application/json")
	data := make(map[string]string)
	data["error"] = fmt.Sprintf("%v", err)
	if err.HttpStatusCode == 0 {
		err.HttpStatusCode = 504
		data["error"] = fmt.Sprintf("avi-api-proxy: %v", err)
	}
	w.WriteHeader(err.HttpStatusCode)
	json.NewEncoder(w).Encode(data)
}

func proxyRequest(aviSession *session.AviSession, w http.ResponseWriter, r *http.Request) {
	glog.Infof("[AVIPROXY]: Proxy request %s %s", r.Method, r.URL.RequestURI())
	var err error
	url := strings.TrimPrefix(r.URL.RequestURI(), "/")

	var payload interface{}
	if err = json.NewDecoder(r.Body).Decode(&payload); err != nil && err != io.EOF {
		glog.Errorf("[AVIPROXY]: Unable to decode payload - %v", err)
	}

	resp, avierror := aviSession.RestRequest(r.Method, url, payload, "admin")
	if resp == nil && avierror != nil {
		glog.Errorf("[AVIPROXY]: REST request error - %v", avierror)
		// capture timeout and unreachable errors
		proxyErrorResponse(w, avierror)
		return
	}

	// copy all response headers as is, ignore set-cookie headers
	for name, values := range resp.Header {
		if name != "Set-Cookie" {
			w.Header()[name] = values
		}
	}

	// copy status code from controller response
	w.WriteHeader(resp.StatusCode)

	// copy response body from controller response
	io.Copy(w, resp.Body)
	resp.Body.Close()
}

func main() {
	var (
		aviurl     = os.Getenv("AVI_CONTROLLER")
		username   = os.Getenv("AVI_USERNAME")
		password   = os.Getenv("AVI_PASSWORD")
		version    = os.Getenv("AVI_VERSION")
		tlsEnabled = os.Getenv("AVI_TLS_ENABLED")
		caCertFile = os.Getenv("AVI_CACERT_FILE")
		timeoutStr = os.Getenv("AVI_TIMEOUT")
		port       = "8080"
	)

	flag.Set("logtostderr", "true")
	flag.Parse()

	var err error
	_, err = url.Parse(aviurl)
	if err != nil {
		glog.Errorf("[AVIPROXY]: Invalid URL provided: %v", err)
		os.Exit(-1)
	}

	// Default timeout: 60 seconds
	if timeoutStr == "" {
		timeoutStr = "60s"
	}
	timeoutStr = fmt.Sprintf("%ss", timeoutStr)
	timeout, _ := time.ParseDuration(timeoutStr)

	var transport *http.Transport
	tlsClientConfig := &tls.Config{InsecureSkipVerify: true}

	if tlsEnabled == "true" {
		var caCert []byte
		caCertPath := fmt.Sprintf("/avi/cacert/%s", caCertFile)
		if caCert, err = ioutil.ReadFile(caCertPath); err != nil {
			glog.Errorf("[AVIPROXY]: Unable to read CA cert file - %v", err)
		}

		caCertPool := x509.NewCertPool()
		caCertPool.AppendCertsFromPEM(caCert)

		tlsClientConfig.InsecureSkipVerify = false
		tlsClientConfig.RootCAs = caCertPool
	}

	transport = &http.Transport{TLSClientConfig: tlsClientConfig}

	// initiate session with Avi controller
	var aviSession *session.AviSession
	aviSession, err = session.NewAviSession(aviurl, username,
		session.SetPassword(password),
		session.SetTransport(transport),
		session.SetVersion(version),
		session.SetTimeout(timeout))
	if err != nil {
		glog.Errorf("Unable to initiate AviSession - %v", err)
		os.Exit(-1)
	}

	defer aviSession.Logout()

	router := httprouter.New()
	path := "/api/*catchall"

	router.Handle("GET", path, func(w http.ResponseWriter, r *http.Request, p httprouter.Params) {
		proxyRequest(aviSession, w, r)
	})

	router.Handle("PUT", path, func(w http.ResponseWriter, r *http.Request, p httprouter.Params) {
		proxyRequest(aviSession, w, r)
	})

	router.Handle("POST", path, func(w http.ResponseWriter, r *http.Request, p httprouter.Params) {
		proxyRequest(aviSession, w, r)
	})

	router.Handle("PATCH", path, func(w http.ResponseWriter, r *http.Request, p httprouter.Params) {
		proxyRequest(aviSession, w, r)
	})

	router.Handle("DELETE", path, func(w http.ResponseWriter, r *http.Request, p httprouter.Params) {
		proxyRequest(aviSession, w, r)
	})

	addr := fmt.Sprintf(":%s", port)
	glog.Infof("[AVIPROXY]: Starting AVI proxy on port %s", port)

	glog.Exit(http.ListenAndServe(addr, router))
}
