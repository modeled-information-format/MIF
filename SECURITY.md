# Security Policy

## Reporting a Vulnerability

Report suspected vulnerabilities privately through GitHub's private
vulnerability reporting: open the repository's **Security** tab and choose
**Report a vulnerability** (Security Advisories). Please do not open a public
issue for an undisclosed vulnerability.

Include the affected version or commit, a description, and reproduction steps.
You will receive an acknowledgement, and a fix or mitigation will be coordinated
before public disclosure.

## Supported Versions

The specification and schemas are versioned by git tag (for example `v1.0.0`).
The newest released major line receives fixes. Each release publishes immutable,
version-pathed schema mirrors (see [public/schema/VERSIONING.md](public/schema/VERSIONING.md)
and [ADR-016](adr/ADR-016-versioned-schema-mirror-publication.md)).

## Verifying Release Artifacts

Every published release is attested (ADR-015): both artifacts carry SLSA build
provenance, signed keyless via Sigstore. The source tarball additionally carries
a CycloneDX SBOM attestation. The signer identity is this repository's release workflow, so verify
with `--signer-workflow` pinned to it.

Download and verify a release:

```sh
# Download the attested artifacts for a tag
gh release download v1.0.0 --repo modeled-information-format/MIF \
  --pattern 'mif-*.tar.gz'

# Verify SLSA build provenance for the source tarball
gh attestation verify mif-1.0.0.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml \
  --predicate-type https://slsa.dev/provenance/v1

# Verify the schema bundle the same way
gh attestation verify mif-schemas-1.0.0.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml \
  --predicate-type https://slsa.dev/provenance/v1

# Verify the CycloneDX SBOM bound to the source tarball
gh attestation verify mif-1.0.0.tar.gz \
  --repo modeled-information-format/MIF \
  --signer-workflow modeled-information-format/MIF/.github/workflows/release.yml \
  --predicate-type https://cyclonedx.org/bom
```

A non-zero exit from any of these commands means the artifact does not match a
trusted attestation; do not use it.

## Supply-Chain Controls

- Every GitHub Actions `uses:` is pinned to a 40-character commit SHA, enforced
  by the `pin-check` gate.
- Security gates run on every push and pull request: CodeQL and Semgrep (SAST),
  OSV (SCA), Trivy (IaC/license), Checkov (IaC policy), Gitleaks and TruffleHog
  (secrets), ShellCheck, and OpenSSF Scorecard (posture). DAST (OWASP ZAP)
  against the published site runs on demand and on a weekly schedule. See
  [ADR-015](adr/ADR-015-attested-release-orchestration.md).
