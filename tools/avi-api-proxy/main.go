package main

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/avinetworks/sdk/go/session"
	"github.com/golang/glog"
	"github.com/julienschmidt/httprouter"
)

func proxyRequest(aviSession *session.AviSession, w http.ResponseWriter, r *http.Request) {
	glog.Infof("[AVIPROXY]: Proxy request %s %s", r.Method, r.URL.Path)
	var err error
	url := strings.TrimPrefix(r.URL.RequestURI(), "/")

	// exported restRequest from goSDK, to get *http.Response as the response and not just []byte.
	// Modified goSDK code in vendors/ dir
	var payload interface{}
	if err = json.NewDecoder(r.Body).Decode(&payload); err != nil {
		glog.Errorf("[AVIPROXY]: %v", err)
	}

	var resp *http.Response
	if resp, err = aviSession.RestRequest(r.Method, url, payload, "admin"); resp == nil && err != nil {
		glog.Errorf("[AVIPROXY]: %v", err)
	}

	data, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		glog.Errorf("[AVIPROXY]: %v", err)
	}
	resp.Body.Close()

	contentTypeHeader := resp.Header.Get("Content-Type")
	w.Header().Set("Content-Type", contentTypeHeader)
	if _, err = w.Write(data); err != nil {
		glog.Errorf("[AVIPROXY]: Couldn't write to response writer - %v", err)
	}
}

func main() {
	var (
		aviurl     = os.Getenv("AVI_CONTROLLER")
		username   = os.Getenv("AVI_USERNAME")
		password   = os.Getenv("AVI_PASSWORD")
		version    = os.Getenv("AVI_VERSION")
		tlsEnabled = os.Getenv("AVI_TLS_ENABLED")
		caCertFile = os.Getenv("AVI_CACERT_FILE")
		port       = "8080"
	)

	flag.Set("logtostderr", "true")
	flag.Parse()

	var err error
	_, err = url.Parse(aviurl)
	if err != nil {
		glog.Errorf("[AVIPROXY]: Invalid URL provided: %s", err.Error())
		os.Exit(-1)
	}

	var transport *http.Transport
	tlsClientConfig := &tls.Config{InsecureSkipVerify: true}

	if tlsEnabled == "true" {
		var caCert []byte
		caCertPath := fmt.Sprintf("/avi/cacert/%s", caCertFile)
		if caCert, err = ioutil.ReadFile(caCertPath); err != nil {
			glog.Errorf("[AVIPROXY]: %v", err)
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
		session.SetInsecure,
		session.SetTransport(transport),
		session.SetVersion(version))
	if err != nil {
		glog.Errorf("%v", err)
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
