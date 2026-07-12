# Security policy

## Reporting a vulnerability

Please do not open a public issue for vulnerabilities involving secret exposure, unsafe config overwrite, command execution, path traversal, or deletion of unmanaged files.

Report privately through GitHub's **Report a vulnerability** feature for this repository. Include the affected command, manifest, target, expected behavior, observed behavior, and a minimal reproduction that contains no real credentials.

## Supported version

Security fixes target the latest release and the current default branch.

## Security boundaries

Agent Nexus manages executable MCP and hook configuration on the local machine. Its guarantees and limitations are documented in [docs/security-model.md](docs/security-model.md). The localhost dashboard is not designed for untrusted remote exposure.
