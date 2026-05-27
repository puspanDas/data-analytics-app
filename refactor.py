import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False

for line in lines:
    if '# --- START: SMART DATA FIXER - DIAGNOSIS ENGINE ---' in line:
        skip = True
        continue
    if '# --- END: SMART DATA FIXER - DIAGNOSIS ENGINE ---' in line:
        skip = False
        continue
    
    if skip:
        continue
        
    if 'from werkzeug.exceptions import RequestEntityTooLarge' in line:
        new_lines.append(line)
        new_lines.append('import logging\n')
        new_lines.append('from data_fixer import diagnose_data, apply_data_fixes\n\n')
        new_lines.append('logger = logging.getLogger(\'app\')\n')
        new_lines.append('logger.setLevel(logging.INFO)\n')
        new_lines.append('fh = logging.FileHandler(\'app.log\', encoding=\'utf-8\')\n')
        new_lines.append('fh.setFormatter(logging.Formatter(\'%(asctime)s - %(levelname)s - %(message)s\'))\n')
        new_lines.append('if not logger.handlers:\n')
        new_lines.append('    logger.addHandler(fh)\n')
        new_lines.append('logger.propagate = False\n')
        continue
        
    if 'print(f"[FIX] Applying auto-fix pipeline for' in line:
        new_lines.append(line.replace('print', 'logger.info'))
        continue
        
    if 'print(f"[SUCCESS] Fix complete:' in line:
        new_lines.append(line.replace('print', 'logger.info'))
        continue
        
    if 'print(f"   Shape: ' in line:
        new_lines.append(line.replace('print', 'logger.info'))
        continue
        
    if 'print(f"   * {fix}")' in line:
        new_lines.append(line.replace('print', 'logger.info'))
        continue
        
    if 'print(f"Error in /fix_data:' in line:
        new_lines.append(line.replace('print', 'logger.error'))
        continue

    new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Refactored app.py successfully')
