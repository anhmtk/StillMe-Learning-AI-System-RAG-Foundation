---
name: Technical Debt
about: Report technical debt or code quality issues
title: '[TECH-DEBT] '
labels: ['technical-debt', 'needs-triage']
assignees: ''
---

## Technical Debt Description
A clear and concise description of the technical debt or code quality issue.

## Location
- **File(s)**: List specific files or modules affected
- **Line Numbers**: If applicable, specify line numbers
- **Module/Component**: Which part of the system is affected

## Problem Description
Describe the technical debt issue:
- **Type**: [Code Quality, Performance, Security, Maintainability, Documentation, etc.]
- **Severity**: [Low, Medium, High, Critical]
- **Impact**: How does this affect the system or developers?

## Current State
Describe the current problematic implementation:
```python
# Example of problematic code
def bad_function():
    # Hardcoded values, no error handling, etc.
    pass
```

## Proposed Solution
Describe how this should be improved:
```python
# Example of improved code
def good_function():
    # Proper implementation with error handling, configuration, etc.
    pass
```

## Priority Assessment
- **Effort Required**: [Small (S), Medium (M), Large (L)]
- **Risk Level**: [Low, Medium, High, Critical]
- **Business Impact**: [Low, Medium, High]
- **Developer Impact**: [Low, Medium, High]

## Dependencies
List any dependencies or prerequisites for addressing this technical debt:
- **Other Issues**: Related issues or PRs
- **External Dependencies**: Third-party libraries or services
- **Internal Dependencies**: Other modules or components

## Acceptance Criteria
Define what "done" looks like for this technical debt:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Additional Context
Add any other context about the technical debt here:
- **Root Cause**: Why did this technical debt accumulate?
- **Prevention**: How can we prevent similar issues in the future?
- **Related Documentation**: Links to relevant docs or standards

## Checklist
- [ ] I have identified the specific location of the technical debt
- [ ] I have assessed the severity and impact
- [ ] I have provided a clear problem description
- [ ] I have proposed a solution
- [ ] I have considered dependencies and prerequisites
- [ ] I have defined acceptance criteria
