package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	avicleanupwcp "github.com/avi-cleanup-wcp/clean"
)

var (
	ctrlIP                            = ""
	username                          = ""
	authToken                         = ""
	password                          = ""
	albCtrlCert                       = ""
	clusterID                         = ""
	useEnvoy                          = false
	ExitCodeRequiredArgsMissing       = 1
	ExitCodeCleanupALBResourcesFailed = 2
)

func main() {
	flag.StringVar(&ctrlIP, "ctrl-ip", "", "NSX ALB Controller IP")
	flag.StringVar(&username, "username", "nsxt-alb", "NSX ALB Controller username")
	flag.StringVar(&authToken, "token", "", "NSX ALB Controller authentication token")
	flag.StringVar(&password, "password", "", "NSX ALB Controller authentication password")
	flag.StringVar(&albCtrlCert, "cacert", "", "NSX ALB Controller authentication certificate")
	flag.StringVar(&clusterID, "cluster-id", "", "AKO cluster name")
	flag.BoolVar(&useEnvoy, "use-envoy", false, "Use Envoy sidecar proxy in VCSA")
	flag.Parse()

	cfg := avicleanupwcp.NewAKOCleanupConfig(ctrlIP, username, password, authToken, albCtrlCert, clusterID, useEnvoy)

	err := avicleanupwcp.CleanupAviResources(cfg)
	if err != nil {
		fmt.Printf("Failed to cleanup Avi resources, err: %s\n", err.Error())
		exitCode := ExitCodeCleanupALBResourcesFailed
		if strings.Contains(err.Error(), "invalid config") {
			exitCode = ExitCodeRequiredArgsMissing
		}
		os.Exit(exitCode)
	}
}
