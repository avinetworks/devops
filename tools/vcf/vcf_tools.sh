#!/bin/bash

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    local LOG_FILE="/tmp/vcftools.log"
    echo -e "${timestamp} [${level}] ${message}" >> "${LOG_FILE}"
    
    case $level in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} ${message}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} ${message}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} ${message}"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${message}"
            ;;
        *)
            echo -e "[${level}] ${message}"
            ;;
    esac
}

# Function to upload Avi bundle to SDDC Manager
uploadbundle() {
    echo -e "${BLUE}=== Upload Avi binary to SDDCm ===${NC}\n"
    echo -e "${BLUE}=== You will be prompted for SDDC manager vcf user password ===${NC}\n"
    read -p "Enter SDDC Manager FQDN: " sddcm
    read -p "Enter SDDC Manager administrator username (typically administrator@vsphere.local): " sddcmuser
    read -s -p "Enter the SDDC Manager administrator password: " sddcmpass
    echo
    read -p "Enter location of PVC file (pvc.json): " pvcfile
    read -p "Enter location of PVC signature file (pvc.sig): " sigfile
    echo -e "${BLUE}=== Enter location of Avi OVA (must be named as expected by PVC file) ===${NC}\n"
    read -p "for 31.1.1, this is controller-31.1.1-9122.ova : " ovapath
    read -p "Enter the Avi product version, this can be found in pvc.json file (VCF9 GA is 31.1.1-24544104): " avi_product_version

    log "INFO" "Creating folder to store pvc files and Avi binary"
    ssh -o StrictHostKeyChecking=no vcf@$sddcm 'mkdir -p /home/vcf/avi'

    log "INFO" "Copying pvc files and Avi binary to SDDC manager"
    scp -o StrictHostKeyChecking=no $pvcfile $sigfile $ovapath vcf@$sddcm:/home/vcf/avi

    loginpayload=$(printf '{"username" : "%s","password": "%s"}' $sddcmuser $sddcmpass)
    response=$(curl -s -H 'Content-Type:application/json' https://$sddcm/v1/tokens -d "$loginpayload" -k)
    TOKEN=$(echo $response | grep -o '"accessToken": *"[^"]*' | sed 's/"accessToken":"//')

    response=$(curl -s -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X PATCH "https://$sddcm/v1/product-version-catalogs" \
    --header 'X-Allow-Overwrite: True' \
    --header 'Content-Type: application/json' \
    --data '{
                "productVersionCatalogFilePath": "/home/vcf/avi/pvc.json",
                "signatureFilePath": "/home/vcf/avi/pvc.sig"
            }')
    task_id=$(echo $response | grep -o '"taskId": *"[^"]*' | sed 's/"taskId":"//')

    # Poll on the task using /v1/product-version-catalogs/upload-tasks/{task_id} API
    while true; do
        response=$(curl -s -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X GET "https://$sddcm/v1/product-version-catalogs/upload-tasks/$task_id")
        log "$response"
        status=$(echo $response | grep -o '"status": *"[^"]*' | sed 's/"status":"//')
        # Check if the status is success/failure/in-progress
        if [[ "$status" == "SUCCEEDED" ]]; then
            log "SUCCESS" "Product version catalogs successfully updated for AVI"
            break
        elif [[ "$status" == "FAILED" ]]; then
            log "ERROR" "$response"
            exit 1
        fi

        echo "Checking Product version catalogs update status in 5 seconds..."
        sleep 5
    done

    # Upload Avi bundle to SDDC manager
    # POST /v1/product-binaries
    ova_upload_payload=$(printf '{"productType": "NSX_ALB", "productVersion": %s, "imageType": "INSTALL", "folderPath": "/home/vcf/avi"}' "$avi_product_version")
    response=$(curl -s -k -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -X POST "https://$sddcm/v1/product-binaries" \
    --header 'Content-Type: application/json' \
    --data "$ova_upload_payload")
    TASK_ID=$(echo $response | grep -o '"id": *"[^"]*' | sed 's/"id":"//')
    if [[ "$TASK_ID" != "" ]]; then
        log "SUCCESS" "AVI OVA UPLOAD STARTED: $response"
    else
        ERROR_MSG=$(echo $response | grep -o '"errorCode": *"[^"]*' | sed 's/"errorCode":"//')
        if [[ "$ERROR_MSG" != "" ]]; then
            log "ERROR" "AVI OVA UPLOAD FAILED: $response"
        fi
        exit 1
    fi
}

# Function to register Avi controller with NSX Manager
enforcementpoint() {
    echo -e "${BLUE}=== Register Avi controller with NSX Manager ===${NC}\n"
    read -p "Enter NSX manager cluster FQDN or IP: " nsx_manager
    read -s -p "Enter NSX manager admin password: " nsx_pass
    echo
    read -p "Enter Avi cluster IP: " avi_cluster
    read -s -p "Enter Avi admin password: " avi_pass
    echo

    # login to Avi controller
    log "INFO" "Login to Avi Controller"
    HEADER_COOKIES=$(curl -s -k -H "Content-Type: application/json" -D - -X POST "https://$avi_cluster/login" --data '{"username": "admin", "password":"'$avi_pass'"}' -o /dev/null | grep -i "^set-cookie:" | sed 's/^set-cookie: //i')

    # Get the session and csrf cookie
    COOKIES=$(echo "$HEADER_COOKIES" | sed -E 's/^([^;]+).*/\1/g')
    COOKIE_STRING=""
    while IFS= read -r line; do
        # Only add `;` if it's not the first entry
        [ -n "$COOKIE_STRING" ] && COOKIE_STRING="$COOKIE_STRING;"
        COOKIE_STRING="$COOKIE_STRING$line"
    done <<< "$COOKIES"

    # Get portal_configuration-> sslkeyandcertificate_refs from system configuration api call
    log "INFO" "Fetching system configuration from Avi Controller"
    response=$(curl -s -k -H "Content-Type: application/json" --cookie "$COOKIE_STRING" -X GET "https://$avi_cluster/api/systemconfiguration")
    PORTAL_CONFIG=$(echo "$response" | 
      grep -A 1000 '"portal_configuration": {' | 
      sed -n '/"portal_configuration": {/,/^[[:space:]]*},$/p' | 
      sed '$ s/},$/}/')

    if [[ "$PORTAL_CONFIG" == "" ]]; then
        log "ERROR" "Couldn't fetch portal certificate from Avi controller: $response"
        return
    fi

    SSL_CERT_REFS=$(echo "$PORTAL_CONFIG" | grep -A 10 '"sslkeyandcertificate_refs": \[' | sed -n '/sslkeyandcertificate_refs/,/\]/p' | grep -v 'sslkeyandcertificate_refs' | grep -o '"[^"]*"' |  sed 's/"//g' | grep -v '^[[:space:]]*$')

    read -r SSL_CERT_REF1 SSL_CERT_REF2 <<< "$SSL_CERT_REFS"
    # Get ssl cert using api/sslkeyandcertificate/{uuid} call
    log "INFO" "Fetching Portal Certificate from Avi Controller"
    response=$(curl -s -k -H "Content-Type: application/json" --cookie "$COOKIE_STRING" -X GET "$SSL_CERT_REF1")

    # Search for ca_certs in the response, if found then portal cert is CA signed
    CA_CERTS=$(echo "$response" | grep -A 20 '"ca_certs": \[' | sed -n '/"ca_certs": \[/,/\],/p')

    default_cert=true
    if [[ "$CA_CERTS" == "" ]]; then
        log "INFO" "Self signed certificate is being used as portal certificate in Avi Controller"
    else
        log "INFO" "CA signed certificate is being used as portal certificate in Avi Controller"
        echo
        log "WARNING" "Make sure CA chain is added in NSX trust store, otherwise registration of Avi Controller will fail"
        echo
        log "INFO" "CA certificate ref from Avi Controller :\n$CA_CERTS"
        default_cert=false
    fi

    echo
    log "INFO" "Initiating Avi onboarding in NSX Manager"
    echo
    response=$(curl --connect-timeout 180 -sS -k -u "admin:$nsx_pass" -w "%{http_code}" -o - -X PUT "https://$nsx_manager/policy/api/v1/infra/alb-onboarding-workflow" \
    --header 'X-Allow-Overwrite: True' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "owned_by": "VCF",
        "cluster_ip": "'$avi_cluster'",
        "infra_admin_username" : "admin",
        "infra_admin_password" : "'$avi_pass'",
        "default_cert": '$default_cert'
        }')

    STATUS_CODE=${response: -3}
    RESPONSE_BODY=${response:0:${#response}-3}
    if [[ "$STATUS_CODE" -ge 400 ]]; then
        log "ERROR" "Avi Onboarding failed:\n$RESPONSE_BODY"
        exit 1
    else
        log "SUCCESS" "Registration of Avi controller with NSX Manager is successful:\n$RESPONSE_BODY"
    fi
}

# Function to upload certifi
uploadcertificate() {
    echo "=== Upload CA certificate to NSX ==="
    echo "=== This function requires the root certificate to be exported ... ==="
    echo "=== ... to the filesystem in PEM format as root.crt  ==="
    read -s -p "Enter your NSX admin password: " nsx_pass
    echo
    read -p "Enter NSX manager hostname or IP: " nsx_manager
    rawcert=$(cat ./root.crt)
    cert="{\"pem_encoded\": \"${rawcert//$'\n'/\\n}\"}"
    response=$(curl -k -sS -u "admin:$nsx_pass" -w "%{http_code}" --location -X POST -o - "https://$nsx_manager/policy/api/v1/trust-management/certificates/sddcm_root?action=import_trusted_ca" \
    --header 'Content-Type: application/json' \
    -d "$cert")
    STATUS_CODE=${response: -3}
    RESPONSE_BODY=${response:0:${#response}-3}
    if [[ "$STATUS_CODE" -ge 400 ]]; then
        log "ERROR" "Certificate upload failed:\n$RESPONSE_BODY"
        exit 1
    else
        log "SUCCESS" "Upload of certificate into NSX Manager is successful:\n$RESPONSE_BODY"
    fi    
}


cleanup() {
    log "INFO" "User requested to exit"
    echo -e "\nThank you for using this tool!"
    unset nsx_pass
    unset sddcm_pass
    unset avi_pass
    exit 0
}

# Menu function
show_menu() {
    echo "Choose an option:"
    echo "1) Upload Avi bundle to SDDCm"
    echo "2) Upload SDDC manager root CA certificate to NSX manager" 
    echo "3) Register Avi enforcement point with NSX manager"
    echo "4) Quit"
    read -p "Enter your choice [1-4]: " choice

    case $choice in
        1) uploadbundle ;;
        2) uploadcertificate ;;
        3) enforcementpoint ;;
        4) cleanup ;;
        *) log "WARNING" "Invalid menu choice: $choice"
            echo -e "\n${YELLOW}Invalid choice. Please select a number between 1-4.${NC}"
            sleep 0.5 ;;
    esac
}

# Main loop
while true; do\
    show_menu
    echo ""
done
