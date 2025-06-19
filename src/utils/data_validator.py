"""Advanced data validation system for business lead data."""

import re
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse
import phonenumbers
from phonenumbers import NumberParseException


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Categories of validation issues."""
    FORMAT = "format"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    BUSINESS_LOGIC = "business_logic"
    DATA_QUALITY = "data_quality"


@dataclass
class ValidationIssue:
    """Individual validation issue."""
    field_name: str
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    current_value: Any = None
    suggested_value: Any = None
    rule_name: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'field_name': self.field_name,
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'current_value': str(self.current_value) if self.current_value is not None else None,
            'suggested_value': str(self.suggested_value) if self.suggested_value is not None else None,
            'rule_name': self.rule_name
        }


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    corrected_data: Optional[Dict] = None
    validation_score: float = 0.0
    
    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue."""
        self.issues.append(issue)
        if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
            self.is_valid = False
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """Get issues by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: ValidationCategory) -> List[ValidationIssue]:
        """Get issues by category."""
        return [issue for issue in self.issues if issue.category == category]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'validation_score': self.validation_score,
            'issues': [issue.to_dict() for issue in self.issues],
            'corrected_data': self.corrected_data,
            'summary': {
                'total_issues': len(self.issues),
                'critical_issues': len(self.get_issues_by_severity(ValidationSeverity.CRITICAL)),
                'error_issues': len(self.get_issues_by_severity(ValidationSeverity.ERROR)),
                'warning_issues': len(self.get_issues_by_severity(ValidationSeverity.WARNING)),
                'info_issues': len(self.get_issues_by_severity(ValidationSeverity.INFO))
            }
        }


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, name: str, severity: ValidationSeverity = ValidationSeverity.ERROR,
                 category: ValidationCategory = ValidationCategory.FORMAT):
        self.name = name
        self.severity = severity
        self.category = category
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        """Validate a field value. Override in subclasses."""
        raise NotImplementedError


class RequiredFieldRule(ValidationRule):
    """Rule to check if required fields are present and not empty."""
    
    def __init__(self):
        super().__init__("required_field", ValidationSeverity.ERROR, ValidationCategory.COMPLETENESS)
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if value is None or (isinstance(value, str) and not value.strip()):
            return [ValidationIssue(
                field_name=field_name,
                severity=self.severity,
                category=self.category,
                message=f"Required field '{field_name}' is missing or empty",
                current_value=value,
                rule_name=self.name
            )]
        return []


class EmailValidationRule(ValidationRule):
    """Rule to validate email addresses."""
    
    def __init__(self):
        super().__init__("email_format", ValidationSeverity.ERROR, ValidationCategory.FORMAT)
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not isinstance(value, str) or not value:
            return []
        
        issues = []
        
        # Basic format check
        if not self.email_pattern.match(value):
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=self.severity,
                category=self.category,
                message=f"Invalid email format: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        # Additional checks
        if '..' in value:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=ValidationSeverity.WARNING,
                category=self.category,
                message=f"Email contains consecutive dots: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        return issues


class PhoneValidationRule(ValidationRule):
    """Rule to validate phone numbers."""
    
    def __init__(self, default_region: str = "GB"):
        super().__init__("phone_format", ValidationSeverity.ERROR, ValidationCategory.FORMAT)
        self.default_region = default_region
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not isinstance(value, str) or not value:
            return []
        
        issues = []
        
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(value, self.default_region)
            
            # Check if valid
            if not phonenumbers.is_valid_number(parsed_number):
                issues.append(ValidationIssue(
                    field_name=field_name,
                    severity=self.severity,
                    category=self.category,
                    message=f"Invalid phone number: {value}",
                    current_value=value,
                    rule_name=self.name
                ))
            else:
                # Suggest formatted version
                formatted = phonenumbers.format_number(
                    parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                if formatted != value:
                    issues.append(ValidationIssue(
                        field_name=field_name,
                        severity=ValidationSeverity.INFO,
                        category=ValidationCategory.DATA_QUALITY,
                        message=f"Phone number can be formatted better",
                        current_value=value,
                        suggested_value=formatted,
                        rule_name=self.name
                    ))
        
        except NumberParseException:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=self.severity,
                category=self.category,
                message=f"Cannot parse phone number: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        return issues


class URLValidationRule(ValidationRule):
    """Rule to validate URLs."""
    
    def __init__(self):
        super().__init__("url_format", ValidationSeverity.ERROR, ValidationCategory.FORMAT)
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not isinstance(value, str) or not value:
            return []
        
        issues = []
        
        try:
            parsed = urlparse(value)
            
            # Check if scheme is present
            if not parsed.scheme:
                suggested_value = f"https://{value}"
                issues.append(ValidationIssue(
                    field_name=field_name,
                    severity=ValidationSeverity.WARNING,
                    category=self.category,
                    message=f"URL missing scheme: {value}",
                    current_value=value,
                    suggested_value=suggested_value,
                    rule_name=self.name
                ))
            
            # Check if netloc is present
            if not parsed.netloc:
                issues.append(ValidationIssue(
                    field_name=field_name,
                    severity=self.severity,
                    category=self.category,
                    message=f"Invalid URL format: {value}",
                    current_value=value,
                    rule_name=self.name
                ))
        
        except Exception:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=self.severity,
                category=self.category,
                message=f"Cannot parse URL: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        return issues


class PostcodeValidationRule(ValidationRule):
    """Rule to validate UK postcodes."""
    
    def __init__(self):
        super().__init__("postcode_format", ValidationSeverity.ERROR, ValidationCategory.FORMAT)
        # UK postcode pattern
        self.postcode_pattern = re.compile(
            r'^[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}$'
        )
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not isinstance(value, str) or not value:
            return []
        
        issues = []
        
        # Normalize postcode
        normalized = value.upper().strip()
        
        # Check format
        if not self.postcode_pattern.match(normalized):
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=self.severity,
                category=self.category,
                message=f"Invalid UK postcode format: {value}",
                current_value=value,
                rule_name=self.name
            ))
        elif normalized != value:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.DATA_QUALITY,
                message=f"Postcode can be normalized",
                current_value=value,
                suggested_value=normalized,
                rule_name=self.name
            ))
        
        return issues


class BusinessNameValidationRule(ValidationRule):
    """Rule to validate business names."""
    
    def __init__(self):
        super().__init__("business_name", ValidationSeverity.WARNING, ValidationCategory.DATA_QUALITY)
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not isinstance(value, str) or not value:
            return []
        
        issues = []
        
        # Check for common issues
        if len(value) < 2:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=ValidationSeverity.WARNING,
                category=self.category,
                message=f"Business name too short: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        if len(value) > 100:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=ValidationSeverity.WARNING,
                category=self.category,
                message=f"Business name too long: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        # Check for suspicious patterns
        if value.lower() in ['test', 'example', 'sample', 'dummy']:
            issues.append(ValidationIssue(
                field_name=field_name,
                severity=ValidationSeverity.WARNING,
                category=self.category,
                message=f"Business name appears to be test data: {value}",
                current_value=value,
                rule_name=self.name
            ))
        
        return issues


class DataConsistencyRule(ValidationRule):
    """Rule to check data consistency across fields."""
    
    def __init__(self):
        super().__init__("data_consistency", ValidationSeverity.WARNING, ValidationCategory.CONSISTENCY)
    
    def validate(self, field_name: str, value: Any, context: Dict = None) -> List[ValidationIssue]:
        if not context:
            return []
        
        issues = []
        
        # Check email domain vs website domain
        if field_name == 'email' and 'website' in context:
            email_domain = self._extract_domain_from_email(value)
            website_domain = self._extract_domain_from_url(context['website'])
            
            if email_domain and website_domain and email_domain != website_domain:
                issues.append(ValidationIssue(
                    field_name=field_name,
                    severity=self.severity,
                    category=self.category,
                    message=f"Email domain ({email_domain}) doesn't match website domain ({website_domain})",
                    current_value=value,
                    rule_name=self.name
                ))
        
        return issues
    
    def _extract_domain_from_email(self, email: str) -> Optional[str]:
        """Extract domain from email address."""
        if not isinstance(email, str) or '@' not in email:
            return None
        return email.split('@')[1].lower()
    
    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        if not isinstance(url, str):
            return None
        try:
            parsed = urlparse(url if '://' in url else f'https://{url}')
            return parsed.netloc.lower().replace('www.', '')
        except Exception:
            return None


class DataValidator:
    """Main data validation engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, List[ValidationRule]] = {
            'global': [],  # Rules applied to all fields
            'field_specific': {}  # Rules for specific fields
        }
        
        # Initialize default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Set up default validation rules."""
        # Field-specific rules
        self.add_field_rule('email', EmailValidationRule())
        self.add_field_rule('phone', PhoneValidationRule())
        self.add_field_rule('website', URLValidationRule())
        self.add_field_rule('postcode', PostcodeValidationRule())
        self.add_field_rule('business_name', BusinessNameValidationRule())
        
        # Global rules
        self.add_global_rule(DataConsistencyRule())
    
    def add_field_rule(self, field_name: str, rule: ValidationRule) -> None:
        """Add a validation rule for a specific field."""
        if field_name not in self.rules['field_specific']:
            self.rules['field_specific'][field_name] = []
        self.rules['field_specific'][field_name].append(rule)
    
    def add_global_rule(self, rule: ValidationRule) -> None:
        """Add a global validation rule."""
        self.rules['global'].append(rule)
    
    def set_required_fields(self, fields: List[str]) -> None:
        """Set required fields."""
        required_rule = RequiredFieldRule()
        for field in fields:
            self.add_field_rule(field, required_rule)
    
    def validate_business_data(self, data: Dict, auto_correct: bool = False) -> ValidationResult:
        """Validate business lead data."""
        result = ValidationResult(is_valid=True)
        corrected_data = data.copy() if auto_correct else None
        
        # Validate each field
        for field_name, value in data.items():
            # Apply field-specific rules
            if field_name in self.rules['field_specific']:
                for rule in self.rules['field_specific'][field_name]:
                    issues = rule.validate(field_name, value, data)
                    for issue in issues:
                        result.add_issue(issue)
                        
                        # Auto-correct if possible and requested
                        if auto_correct and issue.suggested_value is not None:
                            corrected_data[field_name] = issue.suggested_value
        
        # Apply global rules
        for field_name, value in data.items():
            for rule in self.rules['global']:
                issues = rule.validate(field_name, value, data)
                for issue in issues:
                    result.add_issue(issue)
        
        # Calculate validation score
        result.validation_score = self._calculate_validation_score(result)
        
        if auto_correct:
            result.corrected_data = corrected_data
        
        return result
    
    def validate_batch(self, data_list: List[Dict], auto_correct: bool = False) -> List[ValidationResult]:
        """Validate a batch of business data."""
        results = []
        for data in data_list:
            result = self.validate_business_data(data, auto_correct)
            results.append(result)
        return results
    
    def _calculate_validation_score(self, result: ValidationResult) -> float:
        """Calculate a validation score (0-100) based on issues."""
        if not result.issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            ValidationSeverity.INFO: 1,
            ValidationSeverity.WARNING: 3,
            ValidationSeverity.ERROR: 7,
            ValidationSeverity.CRITICAL: 15
        }
        
        total_weight = sum(severity_weights[issue.severity] for issue in result.issues)
        max_possible_weight = len(result.issues) * severity_weights[ValidationSeverity.CRITICAL]
        
        if max_possible_weight == 0:
            return 100.0
        
        score = max(0, 100 - (total_weight / max_possible_weight * 100))
        return round(score, 2)
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict:
        """Get summary statistics for validation results."""
        if not results:
            return {}
        
        total_records = len(results)
        valid_records = sum(1 for r in results if r.is_valid)
        
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        severity_counts = {
            severity.value: len([i for i in all_issues if i.severity == severity])
            for severity in ValidationSeverity
        }
        
        category_counts = {
            category.value: len([i for i in all_issues if i.category == category])
            for category in ValidationCategory
        }
        
        avg_score = sum(r.validation_score for r in results) / total_records
        
        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'validation_rate': valid_records / total_records * 100,
            'average_score': round(avg_score, 2),
            'total_issues': len(all_issues),
            'issues_by_severity': severity_counts,
            'issues_by_category': category_counts,
            'most_common_issues': self._get_most_common_issues(all_issues)
        }
    
    def _get_most_common_issues(self, issues: List[ValidationIssue], top_n: int = 5) -> List[Dict]:
        """Get most common validation issues."""
        issue_counts = {}
        for issue in issues:
            key = f"{issue.field_name}:{issue.rule_name}"
            if key not in issue_counts:
                issue_counts[key] = {
                    'field_name': issue.field_name,
                    'rule_name': issue.rule_name,
                    'severity': issue.severity.value,
                    'count': 0
                }
            issue_counts[key]['count'] += 1
        
        # Sort by count and return top N
        sorted_issues = sorted(issue_counts.values(), key=lambda x: x['count'], reverse=True)
        return sorted_issues[:top_n]


# Global validator instance
_data_validator: Optional[DataValidator] = None


def get_data_validator() -> DataValidator:
    """Get the global data validator instance."""
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator


def validate_business_data(data: Dict, auto_correct: bool = False) -> ValidationResult:
    """Convenience function to validate business data."""
    validator = get_data_validator()
    return validator.validate_business_data(data, auto_correct)