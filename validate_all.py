import os
import sys
import subprocess
import importlib
import ast
from pathlib import Path
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor

class ProjectValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, int] = {
            "files_checked": 0,
            "tests_run": 0,
            "lines_of_code": 0,
            "test_coverage": 0
        }

    def validate_structure(self) -> bool:
        print("\n1. Checking project structure...")
        required_files = [
            "setup.py",
            "requirements.txt",
            "grammar/matangi_grammar.g4",
            "src/__init__.py",
            "src/main.py",
            "src/parser.py",
            "src/interpreter.py",
            "src/semantic_analyzer.py",
            "src/cli.py",
            "src/matangi_ast.py",
            "test/__init__.py",
            "test/conftest.py",
            "test/test_parser.py",
            "test/test_semantic.py",
            "test/test_interpreter.py"
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
            else:
                self.stats["files_checked"] += 1

        if missing_files:
            self.errors.append(f"Missing files: {', '.join(missing_files)}")
            return False
        
        print("✓ Project structure is valid")
        return True

    def validate_code_style(self) -> bool:
        print("\n2. Checking code style...")
        try:
            # Check with black
            black_result = subprocess.run(
                ["black", "--check", "src", "test"],
                capture_output=True,
                text=True
            )
            if black_result.returncode != 0:
                self.warnings.append("Code formatting doesn't match black style")

            # Check with flake8
            flake8_result = subprocess.run(
                ["flake8", "src", "test"],
                capture_output=True,
                text=True
            )
            if flake8_result.returncode != 0:
                self.warnings.append("Code has style issues (flake8)")

            # Check with mypy
            mypy_result = subprocess.run(
                ["mypy", "src"],
                capture_output=True,
                text=True
            )
            if mypy_result.returncode != 0:
                self.warnings.append("Type checking issues found (mypy)")

            print("✓ Code style checks completed")
            return True
        except FileNotFoundError:
            self.warnings.append("Style checking tools not installed (black/flake8/mypy)")
            return True

    def validate_dependencies(self) -> bool:
        print("\n3. Checking dependencies...")
        required_packages = [
            "antlr4-python3-runtime==4.13.2",
            "pytest>=7.0.0",
            "black",
            "flake8",
            "mypy",
            "pytest-cov"
        ]

        missing_packages = []
        for package in required_packages:
            name = package.split('==')[0].split('>=')[0]
            try:
                importlib.import_module(name.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self.errors.append(f"Missing packages: {', '.join(missing_packages)}")
            return False

        print("✓ All dependencies are installed")
        return True

    def validate_grammar(self) -> bool:
        print("\n4. Validating grammar...")
        grammar_file = self.project_root / "grammar" / "matangi_grammar.g4"
        
        try:
            # Check grammar syntax
            result = subprocess.run(
                ["java", "-jar", "antlr.jar", str(grammar_file)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.errors.append("Grammar validation failed")
                return False

            print("✓ Grammar is valid")
            return True
        except Exception as e:
            self.errors.append(f"Grammar validation error: {str(e)}")
            return False

    def run_tests_with_coverage(self) -> bool:
        print("\n5. Running tests with coverage...")
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "-v",
                    "--cov=src",
                    "--cov-report=term-missing",
                    "--no-header"
                ],
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            
            # Extract coverage percentage
            for line in result.stdout.split('\n'):
                if "TOTAL" in line:
                    try:
                        self.stats["test_coverage"] = int(line.split()[-1].rstrip('%'))
                    except (IndexError, ValueError):
                        pass

            if result.returncode != 0:
                self.errors.append("Some tests failed")
                return False
                
            if self.stats["test_coverage"] < 80:
                self.warnings.append(f"Low test coverage: {self.stats['test_coverage']}%")
                
            print("✓ All tests passed")
            return True
        except Exception as e:
            self.errors.append(f"Error running tests: {str(e)}")
            return False

    def count_lines_of_code(self) -> None:
        print("\n6. Counting lines of code...")
        total_lines = 0
        python_files = []
        
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                total_lines += sum(1 for line in f if line.strip() and not line.strip().startswith('#'))
        
        self.stats["lines_of_code"] = total_lines
        print(f"✓ Project has {total_lines} lines of code")

    def validate_imports(self) -> bool:
        print("\n7. Validating imports...")
        python_files = []
        for root, _, files in os.walk(self.project_root / "src"):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        invalid_imports = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=file_path)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                        # Check for absolute imports that should be relative
                        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('src'):
                            invalid_imports.append(f"{file_path}: Should use relative import for {node.module}")
            except Exception as e:
                self.errors.append(f"Error parsing {file_path}: {str(e)}")

        if invalid_imports:
            self.warnings.extend(invalid_imports)
            
        print("✓ Import validation completed")
        return True

    def run_all_validations(self) -> bool:
        print("Starting comprehensive validation...\n")
        
        validations = [
            self.validate_structure,
            self.validate_code_style,
            self.validate_dependencies,
            self.validate_grammar,
            self.run_tests_with_coverage,
            self.validate_imports
        ]

        all_passed = True
        for validation in validations:
            if not validation():
                all_passed = False

        # Count lines of code (doesn't affect pass/fail)
        self.count_lines_of_code()

        print("\nValidation Summary:")
        print(f"\nProject Statistics:")
        print(f"- Files checked: {self.stats['files_checked']}")
        print(f"- Lines of code: {self.stats['lines_of_code']}")
        print(f"- Test coverage: {self.stats['test_coverage']}%")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"❌ {error}")

        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"⚠️  {warning}")

        if all_passed:
            print("\n✅ All validations passed successfully!")
        else:
            print("\n❌ Some validations failed")

        return all_passed

def main():
    validator = ProjectValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 