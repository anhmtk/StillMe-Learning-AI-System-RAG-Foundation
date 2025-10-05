---
name: Security Report
about: Report a security vulnerability
title: '[SECURITY] '
labels: ['security', 'needs-triage', 'high-priority']
assignees: ''
---

## Security Vulnerability Description
A clear and concise description of the security vulnerability.

## Vulnerability Type
- [ ] **Authentication/Authorization**: Issues with user authentication or access control
- [ ] **Input Validation**: Problems with input sanitization or validation
- [ ] **Injection**: SQL injection, command injection, etc.
- [ ] **Cross-Site Scripting (XSS)**: Client-side script injection
- [ ] **Cross-Site Request Forgery (CSRF)**: Unauthorized actions
- [ ] **Information Disclosure**: Sensitive data exposure
- [ ] **Denial of Service**: System availability issues
- [ ] **Cryptographic**: Weak encryption or hashing
- [ ] **Dependency**: Vulnerable third-party libraries
- [ ] **Other**: Please specify

## Severity Assessment
- **CVSS Score**: [If applicable, provide CVSS score]
- **Severity**: [Low, Medium, High, Critical]
- **Exploitability**: [Low, Medium, High]
- **Impact**: [Low, Medium, High]

## Affected Components
- **Files/Modules**: List specific files or modules affected
- **Versions**: Which versions are affected?
- **Dependencies**: Any affected third-party libraries?

## Vulnerability Details
### Description
Detailed description of the vulnerability.

### Attack Vector
How could this vulnerability be exploited?

### Proof of Concept
```python
# Example of how the vulnerability could be exploited
# (Only include if it's safe to do so)
```

### Impact
What are the potential consequences of this vulnerability?

## Reproduction Steps
1. Step 1
2. Step 2
3. Step 3
4. See vulnerability

## Environment
- **OS**: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- **Python Version**: [e.g. 3.9.7]
- **StillMe Version**: [e.g. 1.0.0]
- **Dependencies**: List relevant dependency versions

## Mitigation
### Immediate Actions
- [ ] **Workaround**: Temporary fix to reduce risk
- [ ] **Disable Feature**: If applicable, disable affected feature
- [ ] **Access Control**: Restrict access to affected components

### Long-term Fix
Describe the proper fix for this vulnerability.

## Disclosure
- **Responsible Disclosure**: [Yes/No] - Will you allow time for us to fix before public disclosure?
- **Public Disclosure Date**: [If applicable]
- **Embargo Requested**: [Yes/No] - Do you request an embargo period?

## Contact Information
- **Email**: [Your email for security communications]
- **PGP Key**: [If you have one for encrypted communications]
- **Preferred Contact Method**: [Email, GitHub, etc.]

## Additional Context
Add any other context about the security vulnerability here.

## Checklist
- [ ] I have provided a clear description of the vulnerability
- [ ] I have assessed the severity and impact
- [ ] I have provided reproduction steps
- [ ] I have considered responsible disclosure
- [ ] I have provided contact information
- [ ] I have not included sensitive information in this report

## Security Team Response
*This section will be filled by the security team*

- **Status**: [New, Investigating, Confirmed, Fixed, Disputed]
- **Assigned To**: [Security team member]
- **Target Fix Date**: [Date]
- **CVE**: [If applicable]
- **Notes**: [Internal notes]
