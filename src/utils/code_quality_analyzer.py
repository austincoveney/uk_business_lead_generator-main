"""Code quality analyzer for the UK Business Lead Generator.

This module provides comprehensive code quality analysis including:
- Complexity analysis
- Code smell detection
- Security vulnerability scanning
- Performance bottleneck identification
- Maintainability metrics
"""

import ast
import os
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from collections import defaultdict, Counter


@dataclass
class QualityMetric:
    """Container for a single quality metric."""
    name: str
    value: float
    threshold: float
    status: str  # 'good', 'warning', 'critical'
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    file_path: str
    line_number: int
    cyclomatic_complexity: int
    lines_of_code: int
    parameters_count: int
    return_statements: int
    nested_depth: int
    docstring_present: bool
    type_hints_present: bool


@dataclass
class ClassMetrics:
    """Metrics for a single class."""
    name: str
    file_path: str
    line_number: int
    methods_count: int
    lines_of_code: int
    inheritance_depth: int
    public_methods: int
    private_methods: int
    properties_count: int
    docstring_present: bool


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    file_path: str
    lines_of_code: int
    blank_lines: int
    comment_lines: int
    functions_count: int
    classes_count: int
    imports_count: int
    complexity_score: float
    maintainability_index: float


@dataclass
class SecurityIssue:
    """Container for security issues."""
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str


class CodeQualityAnalyzer:
    """Comprehensive code quality analyzer."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self.quality_metrics: List[QualityMetric] = []
        self.function_metrics: List[FunctionMetrics] = []
        self.class_metrics: List[ClassMetrics] = []
        self.file_metrics: List[FileMetrics] = []
        self.security_issues: List[SecurityIssue] = []
        
        # Quality thresholds
        self.thresholds = {
            'cyclomatic_complexity': 10,
            'function_length': 50,
            'class_length': 300,
            'file_length': 500,
            'parameter_count': 5,
            'nested_depth': 4,
            'maintainability_index': 20
        }
    
    def analyze_project(self) -> Dict[str, Any]:
        """Perform comprehensive project analysis."""
        self.logger.info("Starting code quality analysis...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob('*.py'))
        self.logger.info(f"Found {len(python_files)} Python files")
        
        # Analyze each file
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Generate overall metrics
        overall_metrics = self._calculate_overall_metrics()
        
        # Generate report
        report = {
            'summary': overall_metrics,
            'quality_metrics': [asdict(m) for m in self.quality_metrics],
            'function_metrics': [asdict(m) for m in self.function_metrics],
            'class_metrics': [asdict(m) for m in self.class_metrics],
            'file_metrics': [asdict(m) for m in self.file_metrics],
            'security_issues': [asdict(s) for s in self.security_issues],
            'recommendations': self._generate_recommendations()
        }
        
        self.logger.info("Code quality analysis completed")
        return report
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Analyze file metrics
            file_metrics = self._analyze_file_metrics(file_path, content, tree)
            self.file_metrics.append(file_metrics)
            
            # Analyze functions and classes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_metrics = self._analyze_function(file_path, node, content)
                    self.function_metrics.append(func_metrics)
                elif isinstance(node, ast.ClassDef):
                    class_metrics = self._analyze_class(file_path, node, content)
                    self.class_metrics.append(class_metrics)
            
            # Security analysis
            self._analyze_security(file_path, content, tree)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing {file_path}: {e}")
    
    def _analyze_file_metrics(self, file_path: Path, content: str, tree: ast.AST) -> FileMetrics:
        """Analyze metrics for a file."""
        lines = content.split('\n')
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        blank_lines = len([line for line in lines if not line.strip()])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        
        functions_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        classes_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        imports_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
        
        # Calculate complexity score (simplified)
        complexity_score = self._calculate_file_complexity(tree)
        
        # Calculate maintainability index (simplified Halstead-based)
        maintainability_index = max(0, 171 - 5.2 * complexity_score - 0.23 * functions_count - 16.2 * (lines_of_code / 100))
        
        return FileMetrics(
            file_path=str(file_path),
            lines_of_code=lines_of_code,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            functions_count=functions_count,
            classes_count=classes_count,
            imports_count=imports_count,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index
        )
    
    def _analyze_function(self, file_path: Path, node: ast.FunctionDef, content: str) -> FunctionMetrics:
        """Analyze metrics for a function."""
        # Calculate cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        
        # Count lines of code
        lines_of_code = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
        
        # Count parameters
        parameters_count = len(node.args.args)
        
        # Count return statements
        return_statements = len([n for n in ast.walk(node) if isinstance(n, ast.Return)])
        
        # Calculate nested depth
        nested_depth = self._calculate_nested_depth(node)
        
        # Check for docstring
        docstring_present = (isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and 
                           isinstance(node.body[0].value.value, str)) if node.body else False
        
        # Check for type hints
        type_hints_present = (node.returns is not None or 
                            any(arg.annotation is not None for arg in node.args.args))
        
        return FunctionMetrics(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            cyclomatic_complexity=complexity,
            lines_of_code=lines_of_code,
            parameters_count=parameters_count,
            return_statements=return_statements,
            nested_depth=nested_depth,
            docstring_present=docstring_present,
            type_hints_present=type_hints_present
        )
    
    def _analyze_class(self, file_path: Path, node: ast.ClassDef, content: str) -> ClassMetrics:
        """Analyze metrics for a class."""
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        methods_count = len(methods)
        
        # Count public/private methods
        public_methods = len([m for m in methods if not m.name.startswith('_')])
        private_methods = methods_count - public_methods
        
        # Count properties
        properties_count = len([n for n in node.body if isinstance(n, ast.FunctionDef) and 
                              any(isinstance(d, ast.Name) and d.id == 'property' 
                                  for d in n.decorator_list)])
        
        # Calculate lines of code
        lines_of_code = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
        
        # Calculate inheritance depth (simplified)
        inheritance_depth = len(node.bases)
        
        # Check for docstring
        docstring_present = (isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant) and 
                           isinstance(node.body[0].value.value, str)) if node.body else False
        
        return ClassMetrics(
            name=node.name,
            file_path=str(file_path),
            line_number=node.lineno,
            methods_count=methods_count,
            lines_of_code=lines_of_code,
            inheritance_depth=inheritance_depth,
            public_methods=public_methods,
            private_methods=private_methods,
            properties_count=properties_count,
            docstring_present=docstring_present
        )
    
    def _analyze_security(self, file_path: Path, content: str, tree: ast.AST):
        """Analyze security issues in the file."""
        lines = content.split('\n')
        
        # Check for common security issues
        security_patterns = {
            'hardcoded_password': {
                'pattern': r'(password|pwd|pass)\s*=\s*["\'][^"\'\n]+["\']',
                'severity': 'high',
                'category': 'Hardcoded Credentials',
                'description': 'Hardcoded password detected',
                'recommendation': 'Use environment variables or secure configuration files'
            },
            'sql_injection': {
                'pattern': r'(execute|query)\s*\([^)]*%[^)]*\)',
                'severity': 'critical',
                'category': 'SQL Injection',
                'description': 'Potential SQL injection vulnerability',
                'recommendation': 'Use parameterized queries or ORM'
            },
            'eval_usage': {
                'pattern': r'\beval\s*\(',
                'severity': 'high',
                'category': 'Code Injection',
                'description': 'Use of eval() function detected',
                'recommendation': 'Avoid eval() and use safer alternatives'
            },
            'shell_injection': {
                'pattern': r'(os\.system|subprocess\.call)\s*\([^)]*\+[^)]*\)',
                'severity': 'high',
                'category': 'Command Injection',
                'description': 'Potential shell injection vulnerability',
                'recommendation': 'Use subprocess with shell=False and validate inputs'
            },
            'weak_random': {
                'pattern': r'random\.(random|randint|choice)',
                'severity': 'medium',
                'category': 'Weak Cryptography',
                'description': 'Use of weak random number generator',
                'recommendation': 'Use secrets module for cryptographic purposes'
            }
        }
        
        for line_num, line in enumerate(lines, 1):
            for issue_type, pattern_info in security_patterns.items():
                if re.search(pattern_info['pattern'], line, re.IGNORECASE):
                    self.security_issues.append(SecurityIssue(
                        severity=pattern_info['severity'],
                        category=pattern_info['category'],
                        description=pattern_info['description'],
                        file_path=str(file_path),
                        line_number=line_num,
                        code_snippet=line.strip(),
                        recommendation=pattern_info['recommendation']
                    ))
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_nested_depth(self, node: ast.AST) -> int:
        """Calculate maximum nested depth in a function."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return get_depth(node)
    
    def _calculate_file_complexity(self, tree: ast.AST) -> float:
        """Calculate overall complexity score for a file."""
        total_complexity = 0
        function_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_complexity += self._calculate_cyclomatic_complexity(node)
                function_count += 1
        
        return total_complexity / max(function_count, 1)
    
    def _calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate overall project metrics."""
        total_files = len(self.file_metrics)
        total_functions = len(self.function_metrics)
        total_classes = len(self.class_metrics)
        total_loc = sum(f.lines_of_code for f in self.file_metrics)
        
        # Calculate averages
        avg_complexity = sum(f.cyclomatic_complexity for f in self.function_metrics) / max(total_functions, 1)
        avg_function_length = sum(f.lines_of_code for f in self.function_metrics) / max(total_functions, 1)
        avg_maintainability = sum(f.maintainability_index for f in self.file_metrics) / max(total_files, 1)
        
        # Count quality issues
        complex_functions = len([f for f in self.function_metrics if f.cyclomatic_complexity > self.thresholds['cyclomatic_complexity']])
        long_functions = len([f for f in self.function_metrics if f.lines_of_code > self.thresholds['function_length']])
        functions_without_docstrings = len([f for f in self.function_metrics if not f.docstring_present])
        functions_without_type_hints = len([f for f in self.function_metrics if not f.type_hints_present])
        
        # Security issues by severity
        security_by_severity = Counter(s.severity for s in self.security_issues)
        
        return {
            'total_files': total_files,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'total_lines_of_code': total_loc,
            'average_complexity': round(avg_complexity, 2),
            'average_function_length': round(avg_function_length, 2),
            'average_maintainability_index': round(avg_maintainability, 2),
            'quality_issues': {
                'complex_functions': complex_functions,
                'long_functions': long_functions,
                'functions_without_docstrings': functions_without_docstrings,
                'functions_without_type_hints': functions_without_type_hints
            },
            'security_issues': dict(security_by_severity),
            'total_security_issues': len(self.security_issues)
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # Complexity recommendations
        complex_functions = [f for f in self.function_metrics if f.cyclomatic_complexity > self.thresholds['cyclomatic_complexity']]
        if complex_functions:
            recommendations.append({
                'category': 'Complexity',
                'priority': 'high',
                'title': f'Reduce complexity in {len(complex_functions)} functions',
                'description': 'Functions with high cyclomatic complexity are harder to test and maintain',
                'affected_files': list(set(f.file_path for f in complex_functions)),
                'action': 'Break down complex functions into smaller, more focused functions'
            })
        
        # Documentation recommendations
        functions_without_docs = [f for f in self.function_metrics if not f.docstring_present]
        if len(functions_without_docs) > len(self.function_metrics) * 0.3:  # More than 30% missing docs
            recommendations.append({
                'category': 'Documentation',
                'priority': 'medium',
                'title': f'Add docstrings to {len(functions_without_docs)} functions',
                'description': 'Proper documentation improves code maintainability',
                'affected_files': list(set(f.file_path for f in functions_without_docs)),
                'action': 'Add comprehensive docstrings following PEP 257 conventions'
            })
        
        # Type hints recommendations
        functions_without_hints = [f for f in self.function_metrics if not f.type_hints_present]
        if len(functions_without_hints) > len(self.function_metrics) * 0.5:  # More than 50% missing type hints
            recommendations.append({
                'category': 'Type Safety',
                'priority': 'medium',
                'title': f'Add type hints to {len(functions_without_hints)} functions',
                'description': 'Type hints improve code clarity and enable better IDE support',
                'affected_files': list(set(f.file_path for f in functions_without_hints)),
                'action': 'Add type hints for parameters and return values'
            })
        
        # Security recommendations
        critical_security = [s for s in self.security_issues if s.severity == 'critical']
        if critical_security:
            recommendations.append({
                'category': 'Security',
                'priority': 'critical',
                'title': f'Fix {len(critical_security)} critical security issues',
                'description': 'Critical security vulnerabilities need immediate attention',
                'affected_files': list(set(s.file_path for s in critical_security)),
                'action': 'Review and fix all critical security vulnerabilities'
            })
        
        return recommendations
    
    def save_report(self, output_path: str):
        """Save the analysis report to a JSON file."""
        report = self.analyze_project()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Code quality report saved to {output_path}")
        return report


def analyze_code_quality(project_root: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to analyze code quality."""
    analyzer = CodeQualityAnalyzer(project_root)
    
    if output_path:
        return analyzer.save_report(output_path)
    else:
        return analyzer.analyze_project()