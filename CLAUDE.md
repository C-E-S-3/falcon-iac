# Project Context for Claude

## Project Overview
This is an Ansible role for managing CrowdStrike Falcon Data Protection (DLP) configurations as Infrastructure as Code.

## Key Architecture Decisions

### API Integration
- Uses Ansible `uri` module (not Python SDK) for portability
- OAuth2 authentication with token caching per play
- Supports all CrowdStrike cloud regions (us-1, us-2, eu-1, us-gov-1, us-gov-2)
- API endpoints derived from FalconPy source: https://github.com/CrowdStrike/falconpy

### State Management
Three modes controlled by `falcon_dlp_state_mode`:
- `report` (default): Drift detection only, no changes
- `ignore`: Additive only, create/update but never delete
- `delete`: Full IaC reconciliation, includes deletions

### Resource Processing Order
Resources are processed in dependency order:
1. Content Patterns (no deps)
2. Sensitivity Labels, Web Locations, Cloud Apps, Local Apps (no deps)
3. Local Application Groups (depends on local apps)
4. Enterprise Accounts (no deps)
5. Classifications (depends on patterns, file types, labels, web locations)
6. Policies (depends on classifications)
7. Policy Precedence (depends on policies)

### Name-Based References
Users define policies using human-readable names. The role resolves names to CrowdStrike IDs automatically via lookup maps built during execution.

### JSON Report Output
Set `falcon_dlp_report_file` to generate structured JSON for CI/CD and SIEM integration. Report includes timestamp, event_type, drift status, and full change details.

## File Structure
```
roles/falcon_dlp/
├── defaults/main.yml     # User-configurable variables
├── vars/main.yml         # Internal variables (API endpoints, cloud URLs)
├── tasks/
│   ├── main.yml          # Entry point, orchestrates all tasks
│   ├── auth.yml          # OAuth2 token acquisition
│   ├── load_definitions.yml  # Loads YAML from dlp_policies/
│   ├── report.yml        # Summary report + JSON output
│   └── [resource].yml    # One file per resource type
```

## CI/CD Integration
- `.github/workflows/dlp-report.yml`: PR drift detection, fails on drift
- `.github/workflows/dlp-deploy.yml`: Manual deployment with environment selection
- JSON report uploaded as artifact, can be sent to SIEM

## MSSP Support
Multi-tenant via `falcon_member_cid` variable. Can loop over `falcon_tenants` list for bulk operations.

## Credentials
- Ansible Vault: `falcon_client_id`, `falcon_client_secret`
- Environment fallback: `FALCON_CLIENT_ID`, `FALCON_CLIENT_SECRET`
- GitHub Secrets for CI/CD

## Common Tasks
- Add new resource type: Copy existing task file, update endpoints in vars/main.yml
- Add SIEM integration: Uncomment workflow step, add SIEM_ENDPOINT and SIEM_TOKEN secrets
- Test locally: `ansible-playbook playbooks/dlp_report.yml -e falcon_dlp_debug=true`
