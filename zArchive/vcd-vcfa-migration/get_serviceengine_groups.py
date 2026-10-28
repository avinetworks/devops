#!/usr/bin/env python3
"""
Script to retrieve all Service Engine Groups from an Avi Controller using the Avi SDK.
"""

from avi.sdk.avi_api import ApiSession
import json
import sys
import getpass
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_api_version(controller_ip, username, password, tenant='admin'):
    """
    Auto-detect API version from Avi Controller.
    
    Args:
        controller_ip: Controller IP
        username: Username for authentication
        password: Password for authentication
        tenant: Tenant name (default: admin)
        
    Returns:
        API version string if successful, None otherwise
    """
    try:
        # # Try to get version from source controller
        version_url = f'https://{controller_ip}/api/cluster/version'
        login_url = f'https://{controller_ip}/login'
        session = requests.Session()
        login_response = session.post(
            login_url,
            json={'username': username, 'password': password},
            verify=False,
            timeout=10
        )
        if login_response.status_code == 200:
            version_response = session.get(version_url, verify=False, timeout=5)
            if version_response.status_code == 200:
                data = version_response.json()
                version = data.get('Version', None)
                if version:
                    api_version = version.split('-')[0]
                    return api_version
        
    except Exception:
        pass
    
    return None

def get_all_serviceengine_groups(session, cloud_name=None):
    """
    Retrieve Service Engine Groups from the Avi Controller.
    If cloud_name is provided, filters by that cloud.
    
    Args:
        session: An authenticated ApiSession object
        cloud_name: Optional cloud name to filter by
        
    Returns:
        List of Service Engine Group objects
    """
    try:
        # Use get_objects_iter for pagination support
        # This ensures we get all service engine groups even if there are many
        seg_iter = session.get_objects_iter('serviceenginegroup')
        
        serviceengine_groups = list(seg_iter)
        
        # Filter by cloud if cloud_name is provided
        if cloud_name:
            # Get cloud UUID for matching
            cloud_uuid = None
            try:
                cloud_response = session.get('cloud', params={'name': cloud_name})
                if cloud_response.status_code == 200:
                    cloud_data = cloud_response.json()
                    if cloud_data.get('count', 0) > 0:
                        cloud_uuid = cloud_data['results'][0].get('uuid')
            except Exception:
                pass
            
            filtered_groups = []
            for seg in serviceengine_groups:
                seg_cloud_ref = seg.get('cloud_ref', '')
                if not seg_cloud_ref:
                    continue
                
                # Match by UUID or name
                matches = False
                if cloud_uuid and cloud_uuid in seg_cloud_ref:
                    matches = True
                elif f"?name={cloud_name}" in seg_cloud_ref or f"?name={cloud_name}/" in seg_cloud_ref:
                    matches = True
                else:
                    # Extract cloud name from cloud_ref
                    try:
                        if '?name=' in seg_cloud_ref:
                            name_part = seg_cloud_ref.split('?name=')[1]
                            ref_cloud_name = name_part.split('&')[0].split('/')[0]
                            if ref_cloud_name.lower() == cloud_name.lower():
                                matches = True
                    except Exception:
                        pass
                
                if matches:
                    filtered_groups.append(seg)
            
            return filtered_groups
        
        return serviceengine_groups
    except Exception as e:
        print(f"Error retrieving Service Engine Groups: {e}", file=sys.stderr)
        raise

def print_serviceengine_groups(serviceengine_groups):
    """
    Print Service Engine Groups in a formatted way.
    
    Args:
        serviceengine_groups: List of Service Engine Group objects
    """
    if not serviceengine_groups:
        print("No Service Engine Groups found.")
        return
    
    print(f"\nFound {len(serviceengine_groups)} Service Engine Group(s):\n")
    print("-" * 80)
    
    for seg in serviceengine_groups:
        print(f"Name: {seg.get('name', 'N/A')}")
        print(f"UUID: {seg.get('uuid', 'N/A')}")
        print(f"HA Mode: {seg.get('ha_mode', 'N/A')}")
        print(f"Max SEs: {seg.get('max_se', 'N/A')}")
        print(f"Min SEs: {seg.get('min_se', 'N/A')}")
        print(f"Buffer SEs: {seg.get('buffer_se', 'N/A')}")
        print(f"Min Scaleout per VS: {seg.get('min_scaleout_per_vs', 'N/A')}")
        print("-" * 80)

def create_serviceengine_group_on_target(session, seg_data, cloud_name, tenant_name):
    """
    Create or update a Service Engine Group on the target controller.
    If the Service Engine Group already exists, it will be overwritten.
    
    Args:
        session: An authenticated ApiSession object for the target controller
        seg_data: Service Engine Group data dictionary
        cloud_name: Name of the cloud on the target controller
        tenant_name: Name of the tenant on the target controller
        
    Returns:
        True if successful, False otherwise
    """
    try:
        seg_name = seg_data.get('name', 'Unknown')
        
        # Verify cloud exists
        try:
            cloud_response = session.get('cloud', params={'name': cloud_name})
            if cloud_response.status_code != 200:
                print(f"  ✗ Cloud '{cloud_name}' not found on target controller")
                return False
            cloud_data = cloud_response.json()
            if cloud_data.get('count', 0) == 0:
                print(f"  ✗ Cloud '{cloud_name}' not found on target controller")
                return False
        except Exception as e:
            print(f"  ✗ Error verifying cloud '{cloud_name}': {e}")
            return False
        
        # Check if Service Engine Group already exists
        seg_uuid = None
        try:
            response = session.get('serviceenginegroup', params={'name': seg_name})
            if response.status_code == 200:
                data = response.json()
                if data.get('count', 0) > 0:
                    existing_seg = data['results'][0]
                    seg_uuid = existing_seg.get('uuid')
                    # Verify existing SEG is in the correct cloud
                    existing_cloud_ref = existing_seg.get('cloud_ref', '')
                    expected_cloud_ref = f"/api/cloud/?name={cloud_name}"
                    if expected_cloud_ref not in existing_cloud_ref:
                        print(f"  ✗ Service Engine Group '{seg_name}' exists but is in a different cloud")
                        return False
        except Exception:
            pass
        
        # Create a clean copy of the Service Engine Group data
        new_seg = {}
        
        # Copy fields, excluding metadata and deprecated fields
        exclude_fields = {'uuid', 'url', '_last_modified', 'tenant_ref', 'cloud_ref', 'use_objsync'}
        for key, value in seg_data.items():
            if key not in exclude_fields and not key.endswith('_ref') and not key.endswith('_refs'):
                new_seg[key] = value
        
        # Update if exists, create if not (cloud_ref is immutable on updates)
        if seg_uuid:
            response = session.put(f'serviceenginegroup/{seg_uuid}', data=new_seg)
        else:
            new_seg['cloud_ref'] = f"/api/cloud/?name={cloud_name}"
            response = session.post('serviceenginegroup', data=new_seg)
        
        if response.status_code in [200, 201]:
            action = "updated" if seg_uuid else "created"
            print(f"  ✓ Successfully {action} Service Engine Group '{seg_name}'")
            return True
        else:
            action = "update" if seg_uuid else "create"
            print(f"  ✗ Failed to {action} Service Engine Group '{seg_name}': {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def copy_serviceengine_groups_to_target(source_groups, target_session, cloud_name, tenant_name):
    """Copy Service Engine Groups to target controller."""
    print(f"\nCopying {len(source_groups)} Service Engine Group(s)...")
    success_count = 0
    for seg in source_groups:
        if create_serviceengine_group_on_target(target_session, seg, cloud_name, tenant_name):
            success_count += 1
    print(f"\nSummary: {success_count}/{len(source_groups)} Service Engine Group(s) completed.")

def main():
    """
    Main function to connect to Avi Controller and retrieve all Service Engine Groups.
    """
    # Prompt for cloud name first
    cloud_name = input("Enter cloud name: ").strip()
    if not cloud_name:
        print("Error: Cloud name is required.", file=sys.stderr)
        sys.exit(1)
    
    # Prompt for Avi Controller credentials and configuration
    controller_ip = input("Enter Avi Controller IP: ").strip()
    if not controller_ip:
        print("Error: Controller IP is required.", file=sys.stderr)
        sys.exit(1)
    
    username = input("Enter username (default: admin): ").strip() or 'admin'
    password = getpass.getpass("Enter password: ")
    if not password:
        print("Error: Password is required.", file=sys.stderr)
        sys.exit(1)
    
    avi_tenant = input("Enter tenant (default: admin): ").strip() or 'admin'
    
    # Auto-detect API version
    print("Auto-detecting API version...")
    api_version = get_api_version(controller_ip, username, password, avi_tenant)
    if api_version:
        print(f"Detected API version: {api_version}")
    else:
        print("Could not auto-detect API version.")
        api_version = input("Enter API version: ").strip()
        if not api_version:
            print("Error: API version is required.", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Establish session with Avi Controller
        print(f"\nConnecting to Avi Controller at {controller_ip}...")
        session = ApiSession.get_session(
            controller_ip,
            username,
            password,
            tenant=avi_tenant,
            api_version=api_version
        )
        print("Successfully connected to Avi Controller.\n")
        
        # Retrieve Service Engine Groups
        serviceengine_groups = get_all_serviceengine_groups(session, cloud_name=cloud_name)
        
        # Print the results
        print_serviceengine_groups(serviceengine_groups)
        
        # Optionally, output as JSON
        # Uncomment the following lines if you want JSON output
        # print("\n\nJSON Output:")
        # print(json.dumps(serviceengine_groups, indent=2))
        
        # Ask if user wants to create the same Service Engine Groups on a new VCF A controller
        print("\n" + "=" * 80)
        create_on_new = input("\nDo you want to create the same Service Engine Groups on a new VCF A controller? (yes/no): ").strip().lower()
        
        if create_on_new in ['yes', 'y']:
            # Prompt for target VCF A controller credentials
            print("\n--- Target VCF A Controller Configuration ---")
            target_controller_ip = input("Enter target Avi Controller IP: ").strip()
            if not target_controller_ip:
                print("Error: Target Controller IP is required.", file=sys.stderr)
                sys.exit(1)
            
            target_username = input("Enter username (default: admin): ").strip() or 'admin'
            target_password = getpass.getpass("Enter password: ")
            if not target_password:
                print("Error: Password is required.", file=sys.stderr)
                sys.exit(1)
            
            target_tenant = input("Enter tenant (default: admin): ").strip() or 'admin'
            
            # Auto-detect API version for target controller
            print("Auto-detecting API version for target controller...")
            target_api_version = get_api_version(target_controller_ip, target_username, target_password, target_tenant)
            if target_api_version:
                print(f"Detected API version: {target_api_version}")
            else:
                print("Could not auto-detect API version.")
                target_api_version = input("Enter API version: ").strip()
                if not target_api_version:
                    print("Error: API version is required.", file=sys.stderr)
                    sys.exit(1)
            
            target_cloud_name = input("Enter cloud name: ").strip()
            if not target_cloud_name:
                print("Error: Cloud name is required.", file=sys.stderr)
                sys.exit(1)
            
            try:
                # Establish session with target Avi Controller
                print(f"\nConnecting to target Avi Controller at {target_controller_ip}...")
                target_session = ApiSession.get_session(
                    target_controller_ip,
                    target_username,
                    target_password,
                    tenant=target_tenant,
                    api_version=target_api_version
                )
                print("Successfully connected to target Avi Controller.\n")
                
                # Copy Service Engine Groups to target controller
                copy_serviceengine_groups_to_target(serviceengine_groups, target_session, target_cloud_name, target_tenant)
                
            except Exception as e:
                print(f"Error connecting to target controller: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print("\nExiting. No Service Engine Groups created on target controller.")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
