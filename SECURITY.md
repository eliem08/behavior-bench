# Security Policy

## Supported versions
Security fixes are currently applied to the latest code on the `main` branch. There are no formal commercial SLAs or supported release branches yet.

## Reporting a vulnerability
Please do not publish exploit details in a public issue. Use GitHub's private vulnerability reporting feature for this repository if available. Include affected commit/version, reproduction steps, impact, and any suggested mitigation. If private reporting is unavailable, contact the maintainer through a private channel listed on their GitHub profile.

## Deployment and data handling
- The Streamlit dashboard is a local research interface, not an authenticated multi-user service.
- Do not expose it directly to the public internet or place sensitive prompts, customer data, secrets, or personal information in test cases.
- Treat model output and imported result JSON as untrusted data.
- Use trusted model repositories and review model licenses before commercial use.
- This project does not currently provide tenant isolation, access control, audit-log retention guarantees, or a security certification.

## Scope
Substring-based evaluation can miss semantic failures and produce false positives. A passing report is not a security or safety certification.
