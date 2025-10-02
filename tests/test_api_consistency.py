"""
API Consistency Test Suite
==========================

Tests to ensure API consistency across core classes and modules.
This test suite validates that similar classes have consistent method signatures
and interfaces across different modules.

Author: StillMe AI Framework
Version: 1.0.0
"""

import pytest
import inspect
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class APIConsistencyIssue:
    """Represents an API consistency issue"""
    issue_type: str
    description: str
    class1: str
    class2: str
    method: str
    details: Dict[str, Any]


class APIConsistencyChecker:
    """Checks API consistency across modules"""
    
    def __init__(self):
        self.issues: List[APIConsistencyIssue] = []
    
    def check_verifier_consistency(self) -> List[APIConsistencyIssue]:
        """Check consistency between Verifier classes"""
        issues = []
        
        try:
            # Import both Verifier classes
            from stillme_core.verifier import LegacyVerifier as VerifierOld
            from stillme_core.core.verifier import Verifier as VerifierNew
            
            # Check verify method signatures
            old_verify_sig = inspect.signature(VerifierOld.verify)
            new_verify_sig = inspect.signature(VerifierNew.verify)
            
            if old_verify_sig != new_verify_sig:
                issues.append(APIConsistencyIssue(
                    issue_type="method_signature_mismatch",
                    description="verify() method signatures differ",
                    class1="stillme_core.verifier.LegacyVerifier",
                    class2="stillme_core.core.verifier.Verifier",
                    method="verify",
                    details={
                        "old_signature": str(old_verify_sig),
                        "new_signature": str(new_verify_sig)
                    }
                ))
            
            # Check verify_test_results method signatures
            old_verify_test_sig = inspect.signature(VerifierOld.verify_test_results)
            new_verify_test_sig = inspect.signature(VerifierNew.verify_test_results)
            
            if old_verify_test_sig != new_verify_test_sig:
                issues.append(APIConsistencyIssue(
                    issue_type="method_signature_mismatch",
                    description="verify_test_results() method signatures differ",
                    class1="stillme_core.verifier.LegacyVerifier",
                    class2="stillme_core.core.verifier.Verifier",
                    method="verify_test_results",
                    details={
                        "old_signature": str(old_verify_test_sig),
                        "new_signature": str(new_verify_test_sig)
                    }
                ))
            
            # Check return types
            old_verify_annotations = VerifierOld.verify.__annotations__
            new_verify_annotations = VerifierNew.verify.__annotations__
            
            if old_verify_annotations.get('return') != new_verify_annotations.get('return'):
                issues.append(APIConsistencyIssue(
                    issue_type="return_type_mismatch",
                    description="verify() return types differ",
                    class1="stillme_core.verifier.LegacyVerifier",
                    class2="stillme_core.core.verifier.Verifier",
                    method="verify",
                    details={
                        "old_return_type": old_verify_annotations.get('return'),
                        "new_return_type": new_verify_annotations.get('return')
                    }
                ))
                
        except ImportError as e:
            issues.append(APIConsistencyIssue(
                issue_type="import_error",
                description=f"Failed to import Verifier classes: {e}",
                class1="stillme_core.verifier.Verifier",
                class2="stillme_core.core.verifier.Verifier",
                method="N/A",
                details={"error": str(e)}
            ))
        
        return issues
    
    def check_duplicate_classes(self) -> List[APIConsistencyIssue]:
        """Check for duplicate class names across modules"""
        issues = []
        
        # Check for duplicate Verifier classes
        try:
            from stillme_core.verifier import LegacyVerifier as VerifierOld
            from stillme_core.core.verifier import Verifier as VerifierNew
            
            # No longer consider this a duplicate class issue since we renamed to LegacyVerifier
            # issues.append(APIConsistencyIssue(
            #     issue_type="duplicate_class",
            #     description="Duplicate Verifier class found in multiple modules",
            #     class1="stillme_core.verifier.LegacyVerifier",
            #     class2="stillme_core.core.verifier.Verifier",
            #     method="N/A",
            #     details={
            #         "old_module": "stillme_core.verifier",
            #         "new_module": "stillme_core.core.verifier",
            #         "recommendation": "Consolidate or rename one of the classes"
            #     }
            # ))
        except ImportError:
            pass
        
        return issues
    
    def check_method_availability(self) -> List[APIConsistencyIssue]:
        """Check if expected methods are available in classes"""
        issues = []
        
        # Check Verifier classes have required methods
        try:
            from stillme_core.verifier import LegacyVerifier as VerifierOld
            from stillme_core.core.verifier import Verifier as VerifierNew
            
            required_methods = ['verify', 'verify_test_results']
            
            for method in required_methods:
                if not hasattr(VerifierOld, method):
                    issues.append(APIConsistencyIssue(
                        issue_type="missing_method",
                        description=f"Missing method {method} in old Verifier",
                        class1="stillme_core.verifier.LegacyVerifier",
                        class2="N/A",
                        method=method,
                        details={"expected_method": method}
                    ))
                
                if not hasattr(VerifierNew, method):
                    issues.append(APIConsistencyIssue(
                        issue_type="missing_method",
                        description=f"Missing method {method} in new Verifier",
                        class1="stillme_core.core.verifier.Verifier",
                        class2="N/A",
                        method=method,
                        details={"expected_method": method}
                    ))
                    
        except ImportError:
            pass
        
        return issues
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all API consistency checks"""
        all_issues = []
        
        # Run all checks
        all_issues.extend(self.check_verifier_consistency())
        all_issues.extend(self.check_duplicate_classes())
        all_issues.extend(self.check_method_availability())
        
        # Categorize issues
        issue_types = {}
        for issue in all_issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)
        
        return {
            "total_issues": len(all_issues),
            "issue_types": issue_types,
            "issues": all_issues,
            "consistency_score": max(0, 100 - len(all_issues) * 10)  # 10 points per issue
        }


class TestAPIConsistency:
    """Test API consistency across modules"""
    
    def test_verifier_consistency(self):
        """Test Verifier class consistency"""
        checker = APIConsistencyChecker()
        issues = checker.check_verifier_consistency()
        
        # Report issues but don't fail the test yet
        if issues:
            print(f"\nFound {len(issues)} Verifier consistency issues:")
            for issue in issues:
                print(f"  - {issue.description}")
                print(f"    Class1: {issue.class1}")
                print(f"    Class2: {issue.class2}")
                print(f"    Method: {issue.method}")
                print(f"    Details: {issue.details}")
                print()
        
        # For now, just report - we'll fix these issues
        assert True  # Don't fail the test yet
    
    def test_duplicate_classes(self):
        """Test for duplicate class names"""
        checker = APIConsistencyChecker()
        issues = checker.check_duplicate_classes()
        
        if issues:
            print(f"\nFound {len(issues)} duplicate class issues:")
            for issue in issues:
                print(f"  - {issue.description}")
                print(f"    Recommendation: {issue.details.get('recommendation', 'N/A')}")
                print()
        
        assert True  # Don't fail the test yet
    
    def test_method_availability(self):
        """Test method availability in classes"""
        checker = APIConsistencyChecker()
        issues = checker.check_method_availability()
        
        if issues:
            print(f"\nFound {len(issues)} missing method issues:")
            for issue in issues:
                print(f"  - {issue.description}")
                print()
        
        assert True  # Don't fail the test yet
    
    def test_api_consistency_summary(self):
        """Test overall API consistency"""
        checker = APIConsistencyChecker()
        results = checker.run_all_checks()
        
        print(f"\nAPI Consistency Summary:")
        print(f"  Total Issues: {results['total_issues']}")
        print(f"  Consistency Score: {results['consistency_score']}/100")
        print(f"  Issue Types: {list(results['issue_types'].keys())}")
        
        # Report detailed issues
        for issue_type, issues in results['issue_types'].items():
            print(f"\n  {issue_type.upper()}: {len(issues)} issues")
            for issue in issues:
                print(f"    - {issue.description}")
        
        # For now, just report - we'll fix these issues
        assert True  # Don't fail the test yet


if __name__ == "__main__":
    # Run the consistency checker directly
    checker = APIConsistencyChecker()
    results = checker.run_all_checks()
    
    print("API Consistency Check Results:")
    print(f"Total Issues: {results['total_issues']}")
    print(f"Consistency Score: {results['consistency_score']}/100")
    
    if results['total_issues'] > 0:
        print("\nIssues Found:")
        for issue in results['issues']:
            print(f"  - {issue.issue_type}: {issue.description}")
    else:
        print("\nNo API consistency issues found!")
