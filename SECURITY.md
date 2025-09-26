# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**IMPORTANT**: Do NOT open public issues for security vulnerabilities.

### How to Report

1. **Email**: Send details to [INSERT_SECURITY_EMAIL]
2. **Private Message**: Contact maintainers privately
3. **Encrypted**: Use PGP if available

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution**: Depends on severity and complexity

## Security Best Practices

### For Contributors

- **Never commit secrets**: API keys, passwords, tokens
- **Use environment variables**: Store sensitive data in `.env` files
- **Follow secure coding practices**: Input validation, output encoding
- **Run security scans**: Use `bandit`, `semgrep`, `detect-secrets`

### For Users

- **Keep dependencies updated**: Regularly update packages
- **Use secure configurations**: Enable security features
- **Monitor logs**: Watch for suspicious activity
- **Report issues**: Don't hesitate to report security concerns

## Security Features

StillMe includes several security features:

- **PII Redaction**: Automatic detection and redaction of sensitive data
- **Content Filtering**: Protection against harmful content
- **Input Validation**: Comprehensive input sanitization
- **Audit Logging**: Complete audit trail for security events
- **Access Controls**: Role-based access control (RBAC)

## Security Testing

We run automated security tests:

- **Bandit**: Python security linter
- **Semgrep**: Static analysis for security issues
- **Dependency Scanning**: Check for vulnerable dependencies
- **Secret Detection**: Prevent accidental secret commits

## Disclosure Policy

- **Responsible Disclosure**: We follow responsible disclosure practices
- **Credit**: Security researchers will be credited (if desired)
- **Timeline**: We work with researchers to coordinate disclosure
- **Communication**: Clear communication throughout the process

## Contact

For security-related questions or concerns:

- **Email**: [INSERT_SECURITY_EMAIL]
- **GitHub**: Open a private issue (not public)
- **Discord**: [INSERT_DISCORD_CHANNEL] (if available)

Thank you for helping keep StillMe secure!
