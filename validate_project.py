import os
import sys
import importlib
import unittest
from antlr4 import *

def validate_imports():
    required_packages = [
        'antlr4-python3-runtime',
        'pytest'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def validate_grammar():
    grammar_file = "grammar/matangi_grammar.g4"
    try:
        # Check if generated files exist
        required_files = [
            'src/generated/matangi_grammarLexer.py',
            'src/generated/matangi_grammarParser.py',
            'src/generated/matangi_grammarVisitor.py',
            'src/generated/matangi_grammarListener.py'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            print("Missing generated files:", missing_files)
            return False
            
        return True
    except Exception as e:
        print(f"Grammar validation failed: {str(e)}")
        return False

def validate_ast():
    try:
        from src.matangi_ast import (
            Program, Assignment, Expression, Term, Factor,
            IfStatement, WhileStatement, ForStatement, 
            DoWhileStatement, SwitchStatement
        )
        return True
    except ImportError as e:
        print(f"AST validation failed: {str(e)}")
        return False

def validate_semantic_analyzer():
    try:
        from src.semantic import SemanticAnalyzer
        analyzer = SemanticAnalyzer()
        return True
    except Exception as e:
        print(f"Semantic analyzer validation failed: {str(e)}")
        return False

def run_tests():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('test')
    test_runner = unittest.TextTestRunner()
    return test_runner.run(test_suite).wasSuccessful()

def fix_import_paths():
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.join(project_root, 'src')
    grammar_path = os.path.join(project_root, 'grammar')
    
    if src_path not in sys.path:
        sys.path.append(src_path)
    if grammar_path not in sys.path:
        sys.path.append(grammar_path)

def main():
    print("Starting Matangi project validation...")
    
    # Fix import paths
    fix_import_paths()
    
    # Check required packages
    missing_packages = validate_imports()
    if missing_packages:
        print("Missing required packages:", missing_packages)
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    # Validate grammar
    if not validate_grammar():
        print("Grammar validation failed")
        return False
    
    # Validate AST
    if not validate_ast():
        print("AST validation failed")
        return False
    
    # Validate semantic analyzer
    if not validate_semantic_analyzer():
        print("Semantic analyzer validation failed")
        return False
    
    # Run all tests
    print("Running tests...")
    if not run_tests():
        print("Some tests failed")
        return False
    
    print("All validations passed successfully!")
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)