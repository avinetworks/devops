package avicleanupwcp

import (
	"fmt"
	"strings"

	"github.com/avi-cleanup-wcp/third_party/github.com/vmware/alb-sdk/go/clients"
	"github.com/avi-cleanup-wcp/third_party/github.com/vmware/alb-sdk/go/session"

	"github.com/vmware/alb-sdk/go/models"
)

var (
	SidecarProxyEndpoint = "http://localhost:1080"
	UseExternalCert      = "external-cert"
	ServerCertHeader     = "x-vmware-server-tls-cert"
	AviMinVersion        = "30.1.1"
	NamePrefix           = ""
	AKOuser              = ""
	AdminTenant          = "admin"
	Cloud                = ""
	SEGroupUUID          = ""
)

type aviControllerConfig struct {
	host      string
	user      string
	password  string
	authToken string
	caCert    string
}

type AKOCleanupConfig struct {
	aviControllerConfig
	clusterID string
	useEnvoy  bool
}

func NewAKOCleanupConfig(host, user, password, authToken, caCert, clusterID string, useEnvoy bool) *AKOCleanupConfig {
	return &AKOCleanupConfig{
		aviControllerConfig: aviControllerConfig{
			host:      host,
			user:      user,
			password:  password,
			authToken: authToken,
			caCert:    caCert,
		},
		clusterID: clusterID,
		useEnvoy:  useEnvoy,
	}
}

func setCloudName(client *clients.AviClient, clusterID string) error {
	uri := "/api/serviceenginegroup/?name=" + clusterID + "&include_name=True"
	response := models.ServiceEngineGroupAPIResponse{}
	err := client.AviSession.Get(uri, &response)
	if err != nil {
		return err
	}
	if len(response.Results) == 0 {
		return fmt.Errorf("segroup not found")
	}
	Cloud = strings.Split(*response.Results[0].CloudRef, "#")[1]
	SEGroupUUID = *response.Results[0].UUID
	return nil
}

func CleanupAviResources(cfg *AKOCleanupConfig) error {
	err := validate(cfg)
	if err != nil {
		return err
	}
	NamePrefix = strings.Split(cfg.clusterID, ":")[0] + "--"
	AKOuser = "ako-" + strings.Split(cfg.clusterID, ":")[0]
	if cfg.useEnvoy {
		cfg.host = fmt.Sprintf("%s/%s/http1/%s/443", SidecarProxyEndpoint, UseExternalCert, cfg.host)
	} else {
		cfg.host = "https://" + cfg.host
	}

	client, err := newAviClient(cfg)
	if err != nil {
		return err
	}
	setCloudName(client, cfg.clusterID)
	tenants := make(map[string]struct{})
	err = getAllTenants(client, tenants)
	if err != nil {
		return err
	}

	for tenant := range tenants {
		setTenant := session.SetTenant(tenant)
		setTenant(client.AviSession)
		fmt.Printf("Cleaning up resources in %s tenant\n", tenant)

		err = cleanupVirtualServices(client)
		if err != nil {
			return err
		}

		err = cleanupVsVips(client)
		if err != nil {
			return err
		}

		err = cleanupVSDatascripts(client)
		if err != nil {
			return err
		}

		err = cleanupHTTPPolicySets(client)
		if err != nil {
			return err
		}

		err = cleanupL4PolicySets(client)
		if err != nil {
			return err
		}

		err = cleanupPoolGroups(client)
		if err != nil {
			return err
		}

		err = cleanupPools(client)
		if err != nil {
			return err
		}
	}

	setTenant := session.SetTenant(AdminTenant)
	setTenant(client.AviSession)
	return cleanupSEsAndSEGroup(cfg.clusterID, client)
}

func validate(cfg *AKOCleanupConfig) error {
	if cfg.host == "" || cfg.user == "" {
		return fmt.Errorf("invalid config: host/user is required")
	}
	if cfg.password == "" && cfg.authToken == "" {
		return fmt.Errorf("invalid config: one of password or authtoken is required")
	}
	if cfg.clusterID == "" {
		return fmt.Errorf("invalid config: cluster id is required")
	}
	return nil
}

func convertPemToDer(cert string) string {
	cert = strings.TrimPrefix(cert, "-----BEGIN CERTIFICATE-----")
	cert = strings.TrimSuffix(cert, "-----END CERTIFICATE-----")
	return strings.ReplaceAll(cert, "\n", "")
}
