import ast
import sys
import re
import os
import glob

# --- Backend scan targets (Python files, parsed via AST) ---
BACKEND_FILES_TO_SCAN = ['app.py', 'data_fixer.py', 'power_bi_exporter.py']

# --- Frontend scan targets (JSX/JS files, parsed via regex) ---
FRONTEND_SRC_DIR = os.path.join('frontend', 'src')

TEST_FILE = 'master_test.py'

# ─────────────────────── Backend helpers ───────────────────────

def get_defined_functions(filepath):
    """Extract top-level function names from a Python file using AST."""
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

# ─────────────────────── Frontend helpers ───────────────────────

def get_frontend_files():
    """Discover all .jsx and .js source files under the frontend src directory."""
    files = []
    if not os.path.isdir(FRONTEND_SRC_DIR):
        return files
    for ext in ('*.jsx', '*.js'):
        files.extend(glob.glob(os.path.join(FRONTEND_SRC_DIR, '**', ext), recursive=True))
    # Exclude config files (vite.config.js, eslint.config.js, etc.) – only keep src files
    files = [f for f in files if 'node_modules' not in f]
    return files


def get_frontend_components_and_functions(filepath):
    """
    Parse a JSX/JS file with regex to extract:
      - The default-exported React component name
      - Internal handler / helper function names (const funcName = …)
    Returns a list of (component_name, [handler_names]) tuples.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []

    results = []

    # 1. Detect the default export component name
    #    Patterns: "export default ComponentName;" or "function ComponentName("
    component_name = None
    m = re.search(r'export\s+default\s+(\w+)', content)
    if m:
        component_name = m.group(1)

    # 2. Detect internal handler / helper functions
    #    Patterns: "const handleXyz = " or "const someHelper = ("
    #    We look for top-level const arrow functions inside the component
    handler_pattern = re.compile(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(')
    handlers = []
    for match in handler_pattern.finditer(content):
        name = match.group(1)
        # Skip React state variables, refs, and local variables that aren't handlers
        # Keep names that look like handlers/actions/render helpers
        if any(name.startswith(prefix) for prefix in ('handle', 'render', 'toggle', 'add', 'remove', 'fetch', 'load', 'submit', 'on')):
            handlers.append(name)

    if component_name:
        results.append((component_name, handlers))

    return results


def build_frontend_test_names(components_info):
    """
    Given a list of (component_name, [handler_names]) tuples,
    produce the expected test method names for FrontendTest.
    
    Convention:
      - test_<ComponentName>_renders  → component renders without crashing
      - test_<ComponentName>_<handler> → each handler has a test
    """
    test_names = []
    for component_name, handlers in components_info:
        # Component-level render test
        test_names.append(f"test_{component_name}_renders")
        # Handler-level tests
        for handler in handlers:
            test_names.append(f"test_{component_name}_{handler}")
    return test_names

# ─────────────────────── Test file introspection ───────────────────────

def get_existing_tests(test_filepath, class_name=None):
    """
    Extract existing test method names from the test file.
    If class_name is given, only return tests from that class.
    If class_name is None, return tests from ALL classes.
    """
    try:
        if not os.path.exists(test_filepath):
            return []
        with open(test_filepath, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read())
        
        tests = []
        for n in node.body:
            if isinstance(n, ast.ClassDef):
                if class_name and n.name != class_name:
                    continue
                for sub in n.body:
                    if isinstance(sub, ast.FunctionDef) and sub.name.startswith('test_'):
                        tests.append(sub.name)
        return tests
    except Exception as e:
        print(f"Error parsing {test_filepath}: {e}")
        return []


def has_class(test_filepath, class_name):
    """Check if a test class exists in the test file."""
    try:
        if not os.path.exists(test_filepath):
            return False
        with open(test_filepath, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read())
        for n in node.body:
            if isinstance(n, ast.ClassDef) and n.name == class_name:
                return True
        return False
    except Exception:
        return False

# ─────────────────────── Append logic ───────────────────────

def append_backend_tests(test_filepath, missing_tests):
    """Append missing test stubs into the MasterTest class."""
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
        
    print(f"  [Backend] Added {len(missing_tests)} missing tests to MasterTest: {missing_tests}")


def append_frontend_tests(test_filepath, missing_tests):
    """
    Append missing frontend test stubs into FrontendTest class.
    If FrontendTest doesn't exist yet, create it before the __main__ guard.
    """
    if not missing_tests:
        return

    with open(test_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if not has_class(test_filepath, 'FrontendTest'):
        # Create the FrontendTest class before `if __name__`
        class_header = (
            "\n\nclass FrontendTest(unittest.TestCase):\n"
            "    \"\"\"Frontend component tests — validates structure, props, and API contracts.\"\"\"\n\n"
        )
        test_methods = ""
        for test_name in missing_tests:
            test_methods += f"    def {test_name}(self):\n        pass # TODO: auto-generated frontend test stub\n\n"

        new_content = content.replace(
            "if __name__ == '__main__':",
            f"{class_header}{test_methods}if __name__ == '__main__':"
        )
    else:
        # Class exists — insert new methods just before the last method of the class ends
        # Strategy: insert before the `if __name__` guard (which sits after FrontendTest)
        test_methods = ""
        for test_name in missing_tests:
            test_methods += f"    def {test_name}(self):\n        pass # TODO: auto-generated frontend test stub\n\n"

        new_content = content.replace(
            "if __name__ == '__main__':",
            f"{test_methods}if __name__ == '__main__':"
        )

    with open(test_filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  [Frontend] Added {len(missing_tests)} missing tests to FrontendTest: {missing_tests}")

# ─────────────────────── Main ───────────────────────

def main():
    print("=" * 60)
    print("  Auto Test Generator — Backend + Frontend")
    print("=" * 60)

    # ── 1. Backend scan ──
    print("\n[1/2] Scanning backend Python files...")
    all_backend_functions = []
    for file in BACKEND_FILES_TO_SCAN:
        funcs = get_defined_functions(file)
        if funcs:
            print(f"  Found {len(funcs)} functions in {file}")
        all_backend_functions.extend(funcs)
        
    # Filter out private functions
    all_backend_functions = [f for f in all_backend_functions if not f.startswith('_')]
    
    existing_backend_tests = get_existing_tests(TEST_FILE, class_name='MasterTest')
    
    missing_backend = []
    for func in all_backend_functions:
        expected_test_name = f"test_{func}"
        if expected_test_name not in existing_backend_tests:
            missing_backend.append(expected_test_name)
            
    if missing_backend:
        print(f"  => {len(missing_backend)} missing backend tests detected")
        append_backend_tests(TEST_FILE, missing_backend)
    else:
        print("  => All backend functions have tests [OK]")

    # ── 2. Frontend scan ──
    print("\n[2/2] Scanning frontend JSX/JS files...")
    frontend_files = get_frontend_files()

    if not frontend_files:
        print("  No frontend files found. Skipping frontend test generation.")
    else:
        all_components_info = []
        for fpath in sorted(frontend_files):
            components = get_frontend_components_and_functions(fpath)
            if components:
                for comp_name, handlers in components:
                    rel_path = os.path.relpath(fpath)
                    print(f"  Found component '{comp_name}' with {len(handlers)} handlers in {rel_path}")
                all_components_info.extend(components)

        expected_frontend_tests = build_frontend_test_names(all_components_info)
        existing_frontend_tests = get_existing_tests(TEST_FILE, class_name='FrontendTest')

        missing_frontend = [t for t in expected_frontend_tests if t not in existing_frontend_tests]

        if missing_frontend:
            print(f"  => {len(missing_frontend)} missing frontend tests detected")
            append_frontend_tests(TEST_FILE, missing_frontend)
        else:
            print("  => All frontend components have tests [OK]")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
