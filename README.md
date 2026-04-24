# Falcon DLP Infrastructure as Code

Ansible role and playbooks for managing CrowdStrike Falcon Data Protection (DLP) configurations as Infrastructure as Code.

## Features

- **Full DLP Resource Coverage**: Manage policies, classifications, content patterns, sensitivity labels, web locations, cloud applications, local applications, and more
- **Three State Modes**:
  - `report` (default) - Drift detection only, no changes made
  - `ignore` - Additive only, create/update but never delete
  - `delete` - Full IaC reconciliation, includes deletions
- **MSSP Support**: Multi-tenant management via `member_cid`
- **Name-Based References**: Define policies using human-readable names, role resolves to IDs automatically
- **Flexible Authentication**: Ansible Vault or environment variables

## Requirements

- Ansible 2.14+
- CrowdStrike Falcon API credentials with `data-protection:read` and `data-protection:write` scopes

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/falcon-iac.git
cd falcon-iac

# Set up credentials (choose one method)

# Method A: Ansible Vault
cp inventories/dev/group_vars/all/vault.yml.example inventories/dev/group_vars/all/vault.yml
ansible-vault encrypt inventories/dev/group_vars/all/vault.yml

# Method B: Environment variables
export FALCON_CLIENT_ID="your-client-id"
export FALCON_CLIENT_SECRET="your-client-secret"
```

### 2. Define Your DLP Policies

Edit files in `dlp_policies/` directory:

```yaml
# dlp_policies/content_patterns/ssn.yml
falcon_dlp_content_patterns:
  - name: "SSN Pattern"
    description: "Detects US Social Security Numbers"
    category: "pii"
    region: "us"
    min_match_threshold: 1
    regexes:
      - '\b\d{3}-\d{2}-\d{4}\b'

# dlp_policies/classifications/pii.yml
falcon_dlp_classifications:
  - name: "PII - SSN"
    description: "Documents containing SSNs"
    enabled: true
    content_patterns:
      - "SSN Pattern"  # Reference by name
    file_types:
      - "pdf"
      - "docx"

# dlp_policies/policies/endpoint.yml
falcon_dlp_policies:
  - name: "Endpoint PII Protection"
    enabled: true
    platform: "win"
    classifications:
      - "PII - SSN"  # Reference by name
```

### 3. Run Playbooks

```bash
# Report mode - see what would change (safe, read-only)
ansible-playbook playbooks/dlp_deploy.yml

# Apply changes - additive only
ansible-playbook playbooks/dlp_deploy.yml -e falcon_dlp_state_mode=ignore

# Full reconciliation - includes deletions (use with caution)
ansible-playbook playbooks/dlp_deploy.yml -e falcon_dlp_state_mode=delete
```

## Directory Structure

```
falcon-iac/
├── roles/falcon_dlp/        # Main Ansible role
│   ├── defaults/main.yml    # Default variables
│   ├── vars/main.yml        # Internal variables (API endpoints)
│   └── tasks/               # Task files for each resource type
├── playbooks/
│   ├── dlp_deploy.yml       # Main deployment playbook
│   ├── dlp_report.yml       # Drift detection only
│   └── dlp_destroy.yml      # Remove all custom resources
├── inventories/
│   ├── dev/                 # Development environment
│   └── prod/                # Production environment
└── dlp_policies/            # Your DLP policy definitions
    ├── content_patterns/
    ├── classifications/
    ├── policies/
    ├── web_locations/
    ├── sensitivity_labels/
    └── cloud_applications/
```

## Configuration

### Cloud Regions

Set `falcon_cloud` in your inventory:

| Region | Value |
|--------|-------|
| US-1 | `us-1` (default) |
| US-2 | `us-2` |
| EU-1 | `eu-1` |
| US-GOV-1 | `us-gov-1` |
| US-GOV-2 | `us-gov-2` |

### MSSP Multi-Tenant

For managing multiple child CIDs:

```yaml
# inventories/prod/group_vars/all/falcon.yml
falcon_tenants:
  - name: "customer_a"
    member_cid: "abc123..."
    dlp_policies_dir: "dlp_policies/customer_a"
  - name: "customer_b"
    member_cid: "def456..."
    dlp_policies_dir: "dlp_policies/customer_b"
```

### Resource Type Toggles

Disable specific resource types:

```yaml
falcon_dlp_manage_content_patterns: true
falcon_dlp_manage_classifications: true
falcon_dlp_manage_policies: true
falcon_dlp_manage_sensitivity_labels: false  # Skip labels
falcon_dlp_manage_web_locations: true
# ... etc
```

## State Modes

| Mode | Create | Update | Delete | Use Case |
|------|--------|--------|--------|----------|
| `report` | No | No | No | Drift detection, CI/CD validation |
| `ignore` | Yes | Yes | No | Safe deployments, additive only |
| `delete` | Yes | Yes | Yes | Full IaC, remove orphaned resources |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please open an issue or pull request.

## Disclaimer

This project is not affiliated with or endorsed by CrowdStrike. Use at your own risk.
