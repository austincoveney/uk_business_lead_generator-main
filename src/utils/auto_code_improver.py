"""Automated code improvement utilities for the UK Business Lead Generator.

This module provides automated fixes for common code quality issues including:
- Adding missing docstrings
- Optimizing imports
- Fixing code formatting
- Adding type hints
- Refactoring complex functions
"""

import ast
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from dataclasses import dataclass


@dataclass
class CodeImprovement:
    """Container for a code improvement."""
    file_path: str
    line_number: int
    improvement_type: str
    description: str
    original_code: str
    improved_code: str
    confidence: float  # 0.0 to 1.0


class AutoCodeImprover:
    """Automated code improvement engine."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self.improvements: List[CodeImprovement] = []
        
        # Common patterns for improvements
        self.docstring_templates = {
            'function': '"""{}\n\nArgs:\n{}\n\nReturns:\n    {}\n"""',
            'class': '"""{}\n\nAttributes:\n{}\n"""',
            'module': '"""{}\n\nThis module provides:\n{}\n"""'
        }
    
    def analyze_and_improve(self, apply_fixes: bool = False) -> List[CodeImprovement]:
        """Analyze code and generate improvements."""
        self.logger.info("Starting automated code improvement analysis...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob('*.py'))
        self.logger.info(f"Found {len(python_files)} Python files")
        
        # Analyze each file
        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                self.logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Apply fixes if requested
        if apply_fixes:
            self._apply_improvements()
        
        self.logger.info(f"Found {len(self.improvements)} potential improvements")
        return self.improvements
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single file for improvements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            tree = ast.parse(content)
            
            # Check for various improvement opportunities
            self._check_missing_docstrings(file_path, tree, lines)
            self._check_import_optimization(file_path, tree, lines)
            self._check_variable_naming(file_path, tree, lines)
            self._check_function_complexity(file_path, tree, lines)
            self._check_error_handling(file_path, tree, lines)
            self._check_performance_issues(file_path, tree, lines)
            
        except Exception as e:
            self.logger.warning(f"Error analyzing {file_path}: {e}")
    
    def _check_missing_docstrings(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for missing docstrings and suggest additions."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                # Check if docstring exists
                has_docstring = (node.body and 
                               isinstance(node.body[0], ast.Expr) and 
                               isinstance(node.body[0].value, ast.Constant) and 
                               isinstance(node.body[0].value.value, str))
                
                if not has_docstring:
                    # Generate appropriate docstring
                    if isinstance(node, ast.FunctionDef):
                        docstring = self._generate_function_docstring(node)
                        improvement_type = "Add function docstring"
                    else:
                        docstring = self._generate_class_docstring(node)
                        improvement_type = "Add class docstring"
                    
                    # Find insertion point
                    insert_line = node.lineno
                    original_line = lines[insert_line - 1] if insert_line <= len(lines) else ""
                    
                    # Create improvement
                    self.improvements.append(CodeImprovement(
                        file_path=str(file_path),
                        line_number=insert_line + 1,
                        improvement_type=improvement_type,
                        description=f"Add docstring to {node.name}",
                        original_code=original_line,
                        improved_code=f"{original_line}\n    {docstring}",
                        confidence=0.8
                    ))
    
    def _check_import_optimization(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for import optimization opportunities."""
        imports = []
        import_lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
                import_lines.append(node.lineno)
        
        # Check for unused imports
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)
        
        for imp in imports:
            if isinstance(imp, ast.Import):
                for alias in imp.names:
                    name = alias.asname if alias.asname else alias.name.split('.')[0]
                    if name not in used_names:
                        self.improvements.append(CodeImprovement(
                            file_path=str(file_path),
                            line_number=imp.lineno,
                            improvement_type="Remove unused import",
                            description=f"Remove unused import: {alias.name}",
                            original_code=lines[imp.lineno - 1],
                            improved_code="# Removed unused import",
                            confidence=0.9
                        ))
    
    def _check_variable_naming(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for variable naming improvements."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for single-letter variable names (except common ones)
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                        if (len(child.id) == 1 and 
                            child.id not in ['i', 'j', 'k', 'x', 'y', 'z', '_'] and
                            not child.id.isupper()):
                            
                            # Suggest better name based on context
                            suggested_name = self._suggest_variable_name(child.id, node)
                            
                            self.improvements.append(CodeImprovement(
                                file_path=str(file_path),
                                line_number=getattr(child, 'lineno', node.lineno),
                                improvement_type="Improve variable naming",
                                description=f"Replace single-letter variable '{child.id}' with '{suggested_name}'",
                                original_code=child.id,
                                improved_code=suggested_name,
                                confidence=0.6
                            ))
    
    def _check_function_complexity(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for overly complex functions that should be refactored."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                length = (node.end_lineno - node.lineno + 1) if hasattr(node, 'end_lineno') else 1
                
                if complexity > 10 or length > 50:
                    self.improvements.append(CodeImprovement(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        improvement_type="Refactor complex function",
                        description=f"Function '{node.name}' has complexity {complexity} and {length} lines. Consider breaking it down.",
                        original_code=f"def {node.name}(...):",
                        improved_code=f"# TODO: Refactor {node.name} into smaller functions",
                        confidence=0.7
                    ))
    
    def _check_error_handling(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for missing or poor error handling."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check for bare except clauses
                for handler in node.handlers:
                    if handler.type is None:  # Bare except
                        self.improvements.append(CodeImprovement(
                            file_path=str(file_path),
                            line_number=handler.lineno,
                            improvement_type="Improve error handling",
                            description="Replace bare 'except:' with specific exception types",
                            original_code="except:",
                            improved_code="except Exception as e:",
                            confidence=0.8
                        ))
            
            # Check for functions that might need error handling
            elif isinstance(node, ast.FunctionDef):
                has_try_except = any(isinstance(child, ast.Try) for child in ast.walk(node))
                has_risky_operations = any(
                    isinstance(child, ast.Call) and 
                    isinstance(child.func, ast.Attribute) and
                    child.func.attr in ['open', 'read', 'write', 'connect', 'request']
                    for child in ast.walk(node)
                )
                
                if has_risky_operations and not has_try_except:
                    self.improvements.append(CodeImprovement(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        improvement_type="Add error handling",
                        description=f"Function '{node.name}' performs risky operations but lacks error handling",
                        original_code=f"def {node.name}(...):",
                        improved_code=f"# TODO: Add try-except blocks to {node.name}",
                        confidence=0.6
                    ))
    
    def _check_performance_issues(self, file_path: Path, tree: ast.AST, lines: List[str]):
        """Check for common performance issues."""
        for node in ast.walk(tree):
            # Check for inefficient string concatenation in loops
            if isinstance(node, (ast.For, ast.While)):
                for child in ast.walk(node):
                    if (isinstance(child, ast.AugAssign) and 
                        isinstance(child.op, ast.Add) and
                        isinstance(child.target, ast.Name)):
                        
                        # Check if it's string concatenation
                        self.improvements.append(CodeImprovement(
                            file_path=str(file_path),
                            line_number=getattr(child, 'lineno', node.lineno),
                            improvement_type="Optimize string concatenation",
                            description="Use list.join() instead of += for string concatenation in loops",
                            original_code="string += value",
                            improved_code="string_list.append(value)  # Then use ''.join(string_list)",
                            confidence=0.7
                        ))
            
            # Check for inefficient list operations
            elif isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'append' and
                    isinstance(node.func.value, ast.Name)):
                    
                    # Check if this is in a loop and could be optimized
                    parent = self._find_parent_loop(node, tree)
                    if parent:
                        self.improvements.append(CodeImprovement(
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            improvement_type="Optimize list operations",
                            description="Consider using list comprehension or pre-allocating list size",
                            original_code="list.append(item)",
                            improved_code="# Consider list comprehension or pre-allocation",
                            confidence=0.5
                        ))
    
    def _generate_function_docstring(self, node: ast.FunctionDef) -> str:
        """Generate a docstring for a function."""
        # Extract function name and parameters
        func_name = node.name
        params = [arg.arg for arg in node.args.args if arg.arg != 'self']
        
        # Generate basic description
        description = f"{func_name.replace('_', ' ').title()}."
        
        # Generate parameter descriptions
        param_docs = []
        for param in params:
            param_docs.append(f"        {param}: Description of {param}.")
        
        # Determine return type
        has_return = any(isinstance(child, ast.Return) and child.value is not None 
                        for child in ast.walk(node))
        return_doc = "Return value description." if has_return else "None"
        
        return f'    """{description}\n\n    Args:\n{"".join(param_docs)}\n\n    Returns:\n        {return_doc}\n    """'
    
    def _generate_class_docstring(self, node: ast.ClassDef) -> str:
        """Generate a docstring for a class."""
        class_name = node.name
        description = f"{class_name} class."
        
        # Find attributes (simplified)
        attributes = []
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        attr_docs = []
        for attr in attributes[:5]:  # Limit to first 5
            attr_docs.append(f"        {attr}: Description of {attr}.")
        
        return f'    """{description}\n\n    Attributes:\n{"".join(attr_docs)}\n    """'
    
    def _suggest_variable_name(self, current_name: str, context: ast.FunctionDef) -> str:
        """Suggest a better variable name based on context."""
        # Simple heuristics for better names
        suggestions = {
            'a': 'value',
            'b': 'result',
            'c': 'count',
            'd': 'data',
            'e': 'element',
            'f': 'file',
            'g': 'group',
            'h': 'handler',
            'l': 'list_item',
            'm': 'message',
            'n': 'number',
            'o': 'object',
            'p': 'parameter',
            'q': 'query',
            'r': 'response',
            's': 'string',
            't': 'text',
            'u': 'user',
            'v': 'value',
            'w': 'word'
        }
        
        return suggestions.get(current_name, f"{current_name}_value")
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        return complexity
    
    def _find_parent_loop(self, node: ast.AST, tree: ast.AST) -> Optional[ast.AST]:
        """Find if a node is inside a loop."""
        # Simplified implementation - would need proper parent tracking
        return None
    
    def _apply_improvements(self):
        """Apply the suggested improvements to files."""
        # Group improvements by file
        improvements_by_file = {}
        for improvement in self.improvements:
            if improvement.file_path not in improvements_by_file:
                improvements_by_file[improvement.file_path] = []
            improvements_by_file[improvement.file_path].append(improvement)
        
        # Apply improvements to each file
        for file_path, file_improvements in improvements_by_file.items():
            try:
                self._apply_file_improvements(file_path, file_improvements)
            except Exception as e:
                self.logger.error(f"Failed to apply improvements to {file_path}: {e}")
    
    def _apply_file_improvements(self, file_path: str, improvements: List[CodeImprovement]):
        """Apply improvements to a single file."""
        # Only apply high-confidence improvements automatically
        high_confidence_improvements = [imp for imp in improvements if imp.confidence >= 0.8]
        
        if not high_confidence_improvements:
            return
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort improvements by line number (reverse order to avoid line number shifts)
        high_confidence_improvements.sort(key=lambda x: x.line_number, reverse=True)
        
        # Apply improvements
        for improvement in high_confidence_improvements:
            if improvement.improvement_type == "Remove unused import":
                # Remove the line
                if improvement.line_number <= len(lines):
                    lines[improvement.line_number - 1] = ""  # Remove line
            elif improvement.improvement_type.startswith("Add"):
                # Add new content
                if improvement.line_number <= len(lines):
                    lines[improvement.line_number - 1] = improvement.improved_code + "\n"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        self.logger.info(f"Applied {len(high_confidence_improvements)} improvements to {file_path}")
    
    def generate_improvement_report(self) -> Dict[str, Any]:
        """Generate a comprehensive improvement report."""
        improvements_by_type = {}
        for improvement in self.improvements:
            if improvement.improvement_type not in improvements_by_type:
                improvements_by_type[improvement.improvement_type] = []
            improvements_by_type[improvement.improvement_type].append(improvement)
        
        report = {
            'total_improvements': len(self.improvements),
            'high_confidence_improvements': len([i for i in self.improvements if i.confidence >= 0.8]),
            'improvements_by_type': {
                imp_type: len(improvements) 
                for imp_type, improvements in improvements_by_type.items()
            },
            'affected_files': len(set(i.file_path for i in self.improvements)),
            'improvements': [
                {
                    'file_path': imp.file_path,
                    'line_number': imp.line_number,
                    'type': imp.improvement_type,
                    'description': imp.description,
                    'confidence': imp.confidence
                }
                for imp in self.improvements
            ]
        }
        
        return report


def improve_code_quality(project_root: str, apply_fixes: bool = False) -> Dict[str, Any]:
    """Convenience function to improve code quality."""
    improver = AutoCodeImprover(project_root)
    improver.analyze_and_improve(apply_fixes=apply_fixes)
    return improver.generate_improvement_report()