# Avi Service Engine Groups Management Script

A Python script to retrieve Service Engine Groups from an Avi Controller and optionally copy them to a target VCF A controller.

## Features

- **Retrieve Service Engine Groups**: Fetches all Service Engine Groups from a specified cloud on the source Avi Controller
- **Filter by Cloud**: Retrieves only Service Engine Groups belonging to a specific cloud
- **Copy to Target Controller**: Optionally copies Service Engine Groups to a new VCF A controller
- **Overwrite Protection**: Automatically detects existing Service Engine Groups and updates them instead of failing
- **Immutable Field Handling**: Properly handles immutable fields like `cloud_ref` during updates

## Prerequisites

- Python 3.6 or higher
- Avi SDK (`avisdk`)
- Access to Avi Controller(s)
- Network connectivity to Avi Controller(s)

## Installation

1. Install the Avi SDK:
   ```bash
   pip3 install avisdk
   ```

2. Download the ```get_serviceengine_groups.py``` script from this repo.


3. Make the script executable (optional):
   ```bash
   chmod +x get_serviceengine_groups.py
   ```

## Usage

### Basic Usage

Run the script:
```bash
python3 get_serviceengine_groups.py
```

### Interactive Prompts

The script will prompt you for the following information:

#### Initial Setup (Source Controller)
1. **Cloud name** (required) - The cloud to filter Service Engine Groups from
2. **Avi Controller IP** (required) - Source controller address
3. **Username** (default: admin) - Avi Controller username
4. **Password** (required) - Avi Controller password (hidden input)
5. **API version** (auto-detected) - Avi API version is automatically detected from the controller. If auto-detection fails, you'll be prompted to enter it manually.
6. **Tenant** (default: admin) - Avi tenant name

#### Target Controller (Optional)
If you choose to copy Service Engine Groups to a target controller, you'll be prompted for:
1. **Target Avi Controller IP** (required)
2. **Username** (default: admin)
3. **Password** (required)
4. **API version** (auto-detected) - API version is automatically detected from the target controller. If auto-detection fails, you'll be prompted to enter it manually.
5. **Tenant** (default: admin)
6. **Cloud name** (required) - Target cloud name where Service Engine Groups will be created

### Example Workflow

```
Enter cloud name: Default-Cloud
Enter Avi Controller IP: 10.0.0.1
Enter username (default: admin): admin
Enter password: ********
Auto-detecting API version...
Detected API version: 31.2.1
Enter tenant (default: admin): admin

Connecting to Avi Controller at 10.0.0.1...
Successfully connected to Avi Controller.

Retrieving Service Engine Groups...
Found 2 Service Engine Group(s):

--------------------------------------------------------------------------------
Name: Default-Group
UUID: serviceenginegroup-xxx-xxx-xxx
HA Mode: HA_MODE_SHARED
Max SEs: 10
Min SEs: 1
Buffer SEs: 1
Min Scaleout per VS: 1
--------------------------------------------------------------------------------

Do you want to create the same Service Engine Groups on a new VCF A controller? (yes/no): yes

--- Target VCF A Controller Configuration ---
Enter target Avi Controller IP: 10.0.0.2
Enter username (default: admin): admin
Enter password: ********
Auto-detecting API version for target controller...
Detected API version: 31.2.1
Enter tenant (default: admin): admin
Enter cloud name: Target-Cloud

Connecting to target Avi Controller at 10.0.0.2...
Successfully connected to target Avi Controller.

Copying 2 Service Engine Group(s)...
  ✓ Successfully created Service Engine Group 'Default-Group'
  ✓ Successfully updated Service Engine Group 'Default-Group'

Summary: 2/2 Service Engine Group(s) completed.
```

## How It Works

1. **API Version Detection**: Automatically detects the API version from the Avi Controller by querying the `/api/cluster/version` endpoint
2. **Connection**: Establishes an authenticated session with the source Avi Controller using the detected API version
3. **Retrieval**: Fetches all Service Engine Groups and filters by the specified cloud
4. **Display**: Shows Service Engine Group details (name, UUID, HA mode, SE counts, etc.)
5. **Copy (Optional)**: 
   - Auto-detects API version from target controller
   - Connects to target controller
   - Verifies cloud exists on target
   - For each Service Engine Group:
     - Checks if it already exists
     - If exists: Updates it (excluding immutable fields like `cloud_ref`)
     - If not exists: Creates it with the specified cloud reference

## Important Notes

### Immutable Fields
- **`cloud_ref`**: Cannot be changed after a Service Engine Group is created. If updating an existing Service Engine Group, it must already be in the correct cloud.

### Cloud Validation
- The script validates that the target cloud exists before attempting to create/update Service Engine Groups
- If an existing Service Engine Group is in a different cloud than specified, the operation will fail with an error message

### Deprecated Fields
- The script automatically filters out deprecated fields (e.g., `use_objsync` which was deprecated in API version 31.2.1)

### Error Handling
- Clear error messages are displayed for common issues:
  - Cloud not found
  - Service Engine Group exists in wrong cloud
  - Connection failures
  - Authentication errors

## Troubleshooting

### Common Issues

1. **"Cloud 'X' not found on target controller"**
   - Verify the cloud name exists on the target controller
   - Check for typos in the cloud name

2. **"Service Engine Group 'X' exists but is in a different cloud"**
   - The Service Engine Group already exists on the target but belongs to a different cloud
   - Either delete the existing Service Engine Group or use the correct cloud name

3. **"Failed to create Service Engine Group"**
   - Check API version compatibility
   - Verify all required fields are present
   - Check controller logs for detailed error messages

4. **Connection Errors**
   - Verify network connectivity to the Avi Controller
   - Check firewall rules (port 443)
   - Confirm the controller IP/FQDN is correct

## Requirements

### Python Packages
- `avisdk` - Avi Python SDK
- Standard library modules: `json`, `sys`, `getpass`

## License

This script is provided as-is for automation purposes.

## Support

For Avi Controller API documentation, see:
- [VMware Avi Load Balancer Documentation](https://techdocs.broadcom.com/us/en/vmware-security-load-balancing/avi-load-balancer.html)

## Version History

- **1.1** - Added API version auto-detection
  - Automatically detects API version from controllers
  - Removes need to manually specify API version
  - Falls back to manual entry if auto-detection fails

- **1.0** - Initial release
  - Retrieve Service Engine Groups by cloud
  - Copy Service Engine Groups to target controller
  - Automatic update/create detection
  - Immutable field handling

