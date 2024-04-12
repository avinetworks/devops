package avicleanupwcp

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/avi-cleanup-wcp/third_party/github.com/vmware/alb-sdk/go/clients"
	"github.com/avi-cleanup-wcp/third_party/github.com/vmware/alb-sdk/go/session"

	"github.com/vmware/alb-sdk/go/models"
)

func newAviClient(cfg *AKOCleanupConfig) (*clients.AviClient, error) {
	var transport *http.Transport
	if !cfg.useEnvoy && cfg.caCert != "" {
		caCertPool := x509.NewCertPool()
		caCertPool.AppendCertsFromPEM([]byte(cfg.caCert))

		transport = &http.Transport{
			TLSClientConfig: &tls.Config{
				RootCAs: caCertPool,
			},
		}
	}

	options := []func(*session.AviSession) error{
		session.SetNoControllerStatusCheck,
		session.SetTransport(transport),
		session.SetTenant(AdminTenant),
		session.SetVersion(AviMinVersion),
	}

	if cfg.useEnvoy || cfg.caCert == "" {
		options = append(options, session.SetInsecure)
	}

	if cfg.useEnvoy {
		headers := map[string]string{
			ServerCertHeader: convertPemToDer(cfg.caCert),
		}
		options = append(options, session.SetHeaders(headers))
	}

	if cfg.authToken == "" {
		options = append(options, session.SetPassword(cfg.password))
	} else {
		options = append(options, session.SetAuthToken(cfg.authToken))
	}

	return clients.NewAviClient(cfg.host, cfg.user, options...)
}

func getAllTenants(c *clients.AviClient, tenants map[string]struct{}, nextPage ...string) error {
	uri := "/api/tenant"
	if len(nextPage) > 0 {
		uri = nextPage[0]
	}
	result, err := c.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {

		return err
	}
	for i := 0; i < len(elems); i++ {
		tenant := models.Tenant{}
		err = json.Unmarshal(elems[i], &tenant)
		if err != nil {

			return err
		}
		tenants[*tenant.Name] = struct{}{}
	}
	if result.Next != "" {
		next_uri := strings.Split(result.Next, "/api/tenant")
		if len(next_uri) > 1 {
			nextPage := "/api/tenant" + next_uri[1]
			err = getAllTenants(c, tenants, nextPage)
			if err != nil {
				return err
			}
		}
	}
	return nil
}

func getAllVsVips(c *clients.AviClient, vsvips map[string]struct{}, nextPage ...string) error {
	var uri string

	if len(nextPage) == 1 {
		uri = nextPage[0]
	} else {
		uri = "/api/vsvip/?" + "name.contains=" + NamePrefix + "&include_name=true" + "&cloud_ref.name=" + Cloud + "&page_size=100"
	}

	result, err := c.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		vsvip := models.VsVip{}
		err = json.Unmarshal(elems[i], &vsvip)
		if err != nil {
			continue
		}

		if vsvip.Name == nil || vsvip.UUID == nil {
			continue
		}

		vsvips[*vsvip.UUID] = struct{}{}

	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/vsvip")
		if len(next_uri) > 1 {
			overrideUri := "/api/vsvip" + next_uri[1]
			return getAllVsVips(c, vsvips, overrideUri)
		}
	}
	return nil
}

func getAllDatascripts(client *clients.AviClient, datascripts map[string]struct{}, nextPage ...string) error {
	var uri string

	if len(nextPage) == 1 {
		uri = nextPage[0]
	} else {
		uri = "/api/vsdatascriptset/?" + "&include_name=true&created_by=" + AKOuser
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		ds := models.VSDataScriptSet{}
		err = json.Unmarshal(elems[i], &ds)
		if err != nil {
			continue
		}
		if ds.Name == nil || ds.UUID == nil {
			continue
		}

		datascripts[*ds.UUID] = struct{}{}
	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/vsdatascriptset")
		if len(next_uri) > 1 {
			overrideUri := "/api/vsdatascriptset" + next_uri[1]
			return getAllDatascripts(client, datascripts, overrideUri)
		}
	}
	return nil
}

func getAllPools(client *clients.AviClient, pools map[string]struct{}, overrideUri ...string) error {
	var uri string

	if len(overrideUri) == 1 {
		uri = overrideUri[0]
	} else {
		uri = "/api/pool/?" + "&include_name=true&cloud_ref.name=" + Cloud + "&created_by=" + AKOuser + "&page_size=100"
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		pool := models.Pool{}
		err = json.Unmarshal(elems[i], &pool)
		if err != nil {
			continue
		}

		if pool.Name == nil || pool.UUID == nil {
			continue
		}
		pools[*pool.UUID] = struct{}{}
	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/pool")
		if len(next_uri) > 1 {
			overrideUri := "/api/pool" + next_uri[1]
			return getAllPools(client, pools, overrideUri)
		}
	}

	return nil
}

func getAllPoolGroups(client *clients.AviClient, poolGroups map[string]struct{}, overrideUri ...string) error {
	var uri string

	if len(overrideUri) == 1 {
		uri = overrideUri[0]
	} else {
		uri = "/api/poolgroup/?" + "include_name=true&cloud_ref.name=" + Cloud + "&created_by=" + AKOuser + "&page_size=100"
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		pg := models.PoolGroup{}
		err = json.Unmarshal(elems[i], &pg)
		if err != nil {

			continue
		}

		if pg.Name == nil || pg.UUID == nil {

			continue
		}

		poolGroups[*pg.UUID] = struct{}{}
	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/poolgroup")
		if len(next_uri) > 1 {
			overrideUri := "/api/poolgroup" + next_uri[1]

			return getAllPoolGroups(client, poolGroups, overrideUri)
		}
	}
	return nil
}

func getAllHttpPolicySets(client *clients.AviClient, httpPolicySets map[string]struct{}, nextPage ...string) error {
	var uri string

	if len(nextPage) == 1 {
		uri = nextPage[0]
	} else {
		uri = "/api/httppolicyset/?" + "&include_name=true" + "&created_by=" + AKOuser + "&page_size=100"
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		httppol := models.HTTPPolicySet{}
		err = json.Unmarshal(elems[i], &httppol)
		if err != nil {
			continue
		}
		if httppol.Name == nil || httppol.UUID == nil {
			continue
		}

		httpPolicySets[*httppol.UUID] = struct{}{}
	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/httppolicyset")
		if len(next_uri) > 1 {
			overrideUri := "/api/httppolicyset" + next_uri[1]

			return getAllHttpPolicySets(client, httpPolicySets, overrideUri)

		}
	}
	return nil
}

func getAllL4PolicySets(client *clients.AviClient, l4PolicySet map[string]struct{}, nextPage ...string) error {
	var uri string

	if len(nextPage) == 1 {
		uri = nextPage[0]
	} else {
		uri = "/api/l4policyset/?" + "&include_name=true" + "&created_by=" + AKOuser + "&page_size=100"
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		l4pol := models.L4PolicySet{}
		err = json.Unmarshal(elems[i], &l4pol)
		if err != nil {
			continue
		}
		if l4pol.Name == nil || l4pol.UUID == nil {
			continue
		}

		l4PolicySet[*l4pol.UUID] = struct{}{}
	}

	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/l4policyset")
		if len(next_uri) > 1 {
			overrideUri := "/api/l4policyset" + next_uri[1]
			return getAllL4PolicySets(client, l4PolicySet, overrideUri)
		}
	}
	return nil
}

func getAllVirtualServices(client *clients.AviClient, parentVS, otherVS map[string]struct{}, overrideUri ...string) error {
	var uri string
	if len(overrideUri) == 1 {
		uri = overrideUri[0]
	} else {
		uri = "/api/virtualservice/?" + "include_name=true" + "&cloud_ref.name=" + Cloud + "&created_by=" + AKOuser + "&page_size=100"
	}

	result, err := client.AviSession.GetCollectionRaw(uri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}
	for i := 0; i < len(elems); i++ {
		vs := models.VirtualService{}
		err = json.Unmarshal(elems[i], &vs)
		if err != nil {
			continue
		}
		if vs.Name == nil || vs.UUID == nil {
			continue
		}
		if *vs.Type == "VS_TYPE_VH_PARENT" {
			parentVS[*vs.UUID] = struct{}{}
		} else {
			otherVS[*vs.UUID] = struct{}{}
		}
	}
	if result.Next != "" {
		// It has a next page, let's recursively call the same method.
		next_uri := strings.Split(result.Next, "/api/virtualservice")
		if len(next_uri) > 1 {
			overrideUri := "/api/virtualservice" + next_uri[1]

			return getAllVirtualServices(client, parentVS, otherVS, overrideUri)
		}
	}
	return nil
}

func waitTillDeletion(uri string, client *clients.AviClient, retry int) error {
	if retry == 0 {
		return fmt.Errorf("resource not deleted under expected time")
	}
	var response interface{}
	err := client.AviSession.Get(uri, &response)
	if err != nil {
		if aviError, ok := err.(session.AviError); ok && aviError.HttpStatusCode == 404 {
			return nil
		}
	}
	time.Sleep(1 * time.Second)
	return waitTillDeletion(uri, client, retry-1)
}

func deleteAviResource(client *clients.AviClient, prefix string, res map[string]struct{}) error {
	for uuid := range res {
		uri := prefix + "/" + uuid
		fmt.Printf("Deleting %s\n", uri)
		err := client.AviSession.Delete(uri)
		if err != nil {
			return err
		}
		waitTillDeletion(uri, client, 10)
	}
	return nil
}

func cleanupVirtualServices(client *clients.AviClient) error {
	parentVS := make(map[string]struct{})
	otherVS := make(map[string]struct{})
	err := getAllVirtualServices(client, parentVS, otherVS)
	if err != nil {
		return err
	}
	err = deleteAviResource(client, "/api/virtualservice", otherVS)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/virtualservice", parentVS)

}

func cleanupVsVips(client *clients.AviClient) error {
	vsvips := make(map[string]struct{})
	err := getAllVsVips(client, vsvips)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/vsvip", vsvips)
}

func cleanupVSDatascripts(client *clients.AviClient) error {
	dscripts := make(map[string]struct{})
	err := getAllDatascripts(client, dscripts)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/vsdatascriptset", dscripts)
}

func cleanupHTTPPolicySets(client *clients.AviClient) error {
	httpSets := make(map[string]struct{})
	err := getAllHttpPolicySets(client, httpSets)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/httppolicyset", httpSets)
}

func cleanupL4PolicySets(client *clients.AviClient) error {
	l4sets := make(map[string]struct{})
	err := getAllL4PolicySets(client, l4sets)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/l4policyset", l4sets)
}

func cleanupPoolGroups(client *clients.AviClient) error {
	pgroups := make(map[string]struct{})
	err := getAllPoolGroups(client, pgroups)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/poolgroup", pgroups)
}

func cleanupPools(client *clients.AviClient) error {
	pools := make(map[string]struct{})
	err := getAllPools(client, pools)
	if err != nil {
		return err
	}
	return deleteAviResource(client, "/api/pool", pools)
}

func getAllServiceEngines(client *clients.AviClient, segName string, seUuids map[string]struct{}, nextURI ...string) error {
	seListUri := "/api/serviceengine/?page_size=100&include_name&se_group_ref.name=" + segName + "&cloud_ref.name=" + Cloud
	if len(nextURI) > 0 {
		seListUri = nextURI[0]
	}

	result, err := client.AviSession.GetCollectionRaw(seListUri)
	if err != nil {
		return err
	}
	elems := make([]json.RawMessage, result.Count)
	err = json.Unmarshal(result.Results, &elems)
	if err != nil {
		return err
	}

	for i := 0; i < len(elems); i++ {
		se := models.ServiceEngine{}
		err = json.Unmarshal(elems[i], &se)
		if err != nil {
			continue
		}
		if se.UUID == nil {
			continue
		}
		seUuids[*se.UUID] = struct{}{}
	}
	return nil
}

func cleanupSEsAndSEGroup(segName string, client *clients.AviClient) error {
	seUuids := make(map[string]struct{})
	err := getAllServiceEngines(client, segName, seUuids)
	if err != nil {
		return err
	}
	err = deleteAviResource(client, "/api/serviceengine", seUuids)
	if err != nil {
		return err
	}

	return deleteAviResource(client, "/api/serviceenginegroup", map[string]struct{}{SEGroupUUID: {}})
}
