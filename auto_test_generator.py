import ast
import sys
import re
import os

FILES_TO_SCAN = ['app.py', 'data_fixer.py', 'power_bi_exporter.py']
TEST_FILE = 'master_test.py'

def get_defined_functions(filepath):
    try:
        if not os.path.exists(filepath):
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read())
        
        functions = []
        for n in node.body:
            if isinstance(n, ast.FunctionDef):
                functions.append(n.name)
        return functions
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

def get_existing_tests(test_filepath):
    try:
        if not os.path.exists(test_filepath):
            return []
        with open(test_filepath, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read())
        
        tests = []
        for n in node.body:
            if isinstance(n, ast.ClassDef):
                for sub in n.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name.startswith('test_'):
                        tests.append(sub.name)
        return tests
    except Exception as e:
        print(f"Error parsing {test_filepath}: {e}")
        return []

def append_tests(test_filepath, missing_tests):
    if not missing_tests:
        return
        
    with open(test_filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    test_methods = ""
    for test_name in missing_tests:
        test_methods += f"    def {test_name}(self):\n        pass # TODO: auto-generated test stub\n\n"
        
    new_content = content.replace("if __name__ == '__main__':", f"{test_methods}if __name__ == '__main__':")
    
    with open(test_filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Successfully added {len(missing_tests)} missing tests to {test_filepath}!")

def main():
    all_functions = []
    for file in FILES_TO_SCAN:
        all_functions.extend(get_defined_functions(file))
        
    # Filter out private functions
    all_functions = [f for f in all_functions if not f.startswith('_')]
    
    existing_tests = get_existing_tests(TEST_FILE)
    
    missing_tests = []
    for func in all_functions:
        expected_test_name = f"test_{func}"
        if expected_test_name not in existing_tests:
            missing_tests.append(expected_test_name)
            
    if missing_tests:
        print(f"Found {len(missing_tests)} missing tests: {missing_tests}")
        append_tests(TEST_FILE, missing_tests)
    else:
        print("All features currently have tests. Nothing to add.")

if __name__ == '__main__':
    main()
