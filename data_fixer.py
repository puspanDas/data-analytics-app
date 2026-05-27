import pandas as pd
import numpy as np
import io
import csv
import logging

# --- Setup Secure File Logging ---
# This ensures that no print statements go to the Windows terminal,
# completely eliminating charmap UnicodeEncodeErrors.
logger = logging.getLogger('data_fixer')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('data_fixer.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(fh)
logger.propagate = False  # Prevent logs from bubbling up to the console

def diagnose_data(raw_bytes, filename, df):
    """
    Diagnose structural issues in uploaded data.
    Returns a diagnosis dict with detected issues and whether auto-fix is possible.
    """
    issues = []
    is_csv = filename.lower().endswith('.csv')
    
    logger.info(f"DIAGNOSIS RUNNING for {filename}. Cols: {len(df.columns)}, Shape: {df.shape}")
    
    # --- Issue 1: Wrong delimiter / data crammed into single column ---
    if len(df.columns) == 1:
        logger.info("Checking single column...")
        single_col_values = df.iloc[:, 0].dropna().astype(str)
        if len(single_col_values) > 0:
            # Check if values contain common delimiters
            sample = '\n'.join(single_col_values.head(20).tolist())
            delimiter_counts = {
                'semicolon (;)': sample.count(';'),
                'tab (\\t)': sample.count('\t'),
                'pipe (|)': sample.count('|'),
                'comma (,)': sample.count(',')
            }
            dominant = max(delimiter_counts, key=delimiter_counts.get)
            logger.info(f"Dominant delimiter: {dominant}, count: {delimiter_counts[dominant]}, threshold: {len(single_col_values.head(20)) * 0.5}")
            if delimiter_counts[dominant] > len(single_col_values.head(20)) * 0.5:
                logger.info("SINGLE_COLUMN issue added!")
                issues.append({
                    'code': 'SINGLE_COLUMN',
                    'severity': 'critical',
                    'description': f'All data is crammed into a single column. Detected embedded {dominant} delimiters that should separate columns.',
                    'affected': str(df.columns[0]),
                    'detail': f'Found {delimiter_counts[dominant]} occurrences of {dominant} in first 20 rows'
                })
    elif is_csv and len(df.columns) <= 2:
        # Could still have wrong delimiter - try sniffing
        try:
            text_sample = raw_bytes[:8192].decode('utf-8', errors='ignore')
            dialect = csv.Sniffer().sniff(text_sample, delimiters=';,\t|')
            if dialect.delimiter != ',':
                issues.append({
                    'code': 'WRONG_DELIMITER',
                    'severity': 'critical',
                    'description': f'File appears to use "{dialect.delimiter}" as delimiter instead of comma.',
                    'affected': 'entire file',
                    'detail': f'Detected delimiter: "{dialect.delimiter}"'
                })
        except Exception:
            pass
    
    # --- Issue 2: Messy / unnamed headers ---
    unnamed_cols = [c for c in df.columns if str(c).startswith('Unnamed:') or str(c).strip() == '']
    if unnamed_cols:
        issues.append({
            'code': 'UNNAMED_HEADERS',
            'severity': 'warning',
            'description': f'{len(unnamed_cols)} column(s) have missing or auto-generated names.',
            'affected': unnamed_cols[:10],  # limit for display
            'detail': 'These columns will be renamed to Column_1, Column_2, etc.'
        })
    
    # --- Issue 3: Header row not the first row (junk rows at top) ---
    if len(df) >= 3 and len(df.columns) >= 2:
        # Heuristic: if the first row looks very different from rows 2-5
        first_row_types = set()
        for val in df.iloc[0].values:
            if pd.isna(val):
                first_row_types.add('nan')
            elif isinstance(val, (int, float, np.integer, np.floating)):
                first_row_types.add('number')
            else:
                first_row_types.add('string')
        # Check if most columns have numeric data but first row is all strings (possible header in data)
        numeric_col_count = len(df.select_dtypes(include=[np.number]).columns)
        if numeric_col_count == 0 and len(df.columns) >= 3:
            # All object columns - check if row 1 looks like a header
            row0_vals = df.iloc[0].astype(str).tolist()
            row1_vals = df.iloc[1].astype(str).tolist() if len(df) > 1 else []
            # If row 0 values are very short (header-like) and row 1 values are longer (data-like)
            avg_len_r0 = np.mean([len(v) for v in row0_vals]) if row0_vals else 0
            avg_len_r1 = np.mean([len(v) for v in row1_vals]) if row1_vals else 0
            if avg_len_r0 < 15 and avg_len_r1 > avg_len_r0 * 2 and len(unnamed_cols) > len(df.columns) * 0.5:
                issues.append({
                    'code': 'HEADER_IN_DATA',
                    'severity': 'warning',
                    'description': 'The actual column headers may be in the first data row instead of the header row.',
                    'affected': 'row 0',
                    'detail': 'The first row will be promoted to column headers.'
                })
    
    # --- Issue 4: Trailing empty / ghost columns (>95% NaN) ---
    ghost_cols = []
    for col in df.columns:
        nan_ratio = df[col].isna().sum() / max(len(df), 1)
        if nan_ratio > 0.95:
            ghost_cols.append(str(col))
    if ghost_cols:
        issues.append({
            'code': 'GHOST_COLUMNS',
            'severity': 'warning',
            'description': f'{len(ghost_cols)} column(s) are >95% empty and likely artifacts.',
            'affected': ghost_cols[:10],
            'detail': 'These empty columns will be removed.'
        })
    
    # --- Issue 5: Whitespace pollution ---
    obj_cols = df.select_dtypes(include=['object']).columns
    whitespace_cols = []
    for col in obj_cols:
        sample = df[col].dropna().head(100)
        if len(sample) > 0:
            has_leading = sample.astype(str).str.startswith(' ').any()
            has_trailing = sample.astype(str).str.endswith(' ').any()
            if has_leading or has_trailing:
                whitespace_cols.append(str(col))
    if whitespace_cols:
        issues.append({
            'code': 'WHITESPACE',
            'severity': 'info',
            'description': f'{len(whitespace_cols)} column(s) contain leading/trailing whitespace in values.',
            'affected': whitespace_cols[:10],
            'detail': 'Whitespace will be trimmed from all text values.'
        })
    
    # --- Issue 6: Duplicate column names ---
    if df.columns.duplicated().any():
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        issues.append({
            'code': 'DUPLICATE_COLUMNS',
            'severity': 'warning',
            'description': f'{len(dup_cols)} duplicate column name(s) detected.',
            'affected': list(set(str(c) for c in dup_cols))[:10],
            'detail': 'Duplicate columns will be renamed with _2, _3 suffixes.'
        })
    
    # --- Issue 7: Fully empty rows (more than 10% of data) ---
    empty_row_count = df.isna().all(axis=1).sum()
    empty_ratio = empty_row_count / max(len(df), 1)
    if empty_ratio > 0.05 and empty_row_count > 2:
        issues.append({
            'code': 'EMPTY_ROWS',
            'severity': 'warning',
            'description': f'{int(empty_row_count)} fully empty rows detected ({empty_ratio:.0%} of data).',
            'affected': f'{int(empty_row_count)} rows',
            'detail': 'Empty rows will be removed.'
        })
    
    has_issues = len(issues) > 0
    has_critical = any(i['severity'] == 'critical' for i in issues)
    
    return {
        'has_issues': has_issues,
        'has_critical': has_critical,
        'issue_count': len(issues),
        'issues': issues,
        'fixable': has_issues  # All detected issues are auto-fixable
    }

def apply_data_fixes(raw_bytes, filename, diagnosis):
    """
    Apply auto-fix pipeline based on diagnosis results.
    Returns a cleaned DataFrame and a summary of fixes applied.
    """
    fixes_applied = []
    is_csv = filename.lower().endswith('.csv')
    issue_codes = set(i['code'] for i in diagnosis.get('issues', []))
    
    # --- Step 1: Re-read with correct delimiter if needed ---
    if is_csv and ('SINGLE_COLUMN' in issue_codes or 'WRONG_DELIMITER' in issue_codes):
        try:
            text = raw_bytes.decode('utf-8', errors='ignore')
            # Try csv.Sniffer first
            try:
                dialect = csv.Sniffer().sniff(text[:8192], delimiters=';,\t|')
                detected_sep = dialect.delimiter
            except Exception:
                # Fallback: count delimiters in first few lines
                first_lines = text.split('\n')[:10]
                sample = '\n'.join(first_lines)
                counts = {';': sample.count(';'), '\t': sample.count('\t'), '|': sample.count('|'), ',': sample.count(',')}
                detected_sep = max(counts, key=counts.get)
            
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), sep=detected_sep, engine='python', encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(raw_bytes), sep=detected_sep, engine='python', encoding='cp1252')
            
            # If the row was fully quoted, it might still read as 1 column. Use QUOTE_NONE to force split.
            if len(df.columns) == 1 and detected_sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), sep=detected_sep, engine='python', encoding='utf-8', quoting=csv.QUOTE_NONE)
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(raw_bytes), sep=detected_sep, engine='python', encoding='cp1252', quoting=csv.QUOTE_NONE)
                
                # Strip quotes from headers and values
                df.columns = df.columns.str.strip('"')
                for col in df.columns:
                    if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                        df[col] = df[col].astype(str).str.strip('"')
                
            fixes_applied.append(f'Re-parsed CSV using "{detected_sep}" delimiter (was incorrectly parsed)')
        except Exception as e:
            logger.error(f"Fix: delimiter re-read failed: {e}, falling back to original")
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding='cp1252')
    elif is_csv:
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding='cp1252')
    else:
        df = pd.read_excel(io.BytesIO(raw_bytes))
        
    # --- Step 1.5: Universal Fix for SINGLE_COLUMN ---
    # If it is STILL 1 column (e.g. it was an .xlsx file, or quoting prevented splitting)
    if 'SINGLE_COLUMN' in issue_codes and len(df.columns) == 1:
        try:
            col_name = str(df.columns[0])
            counts = {';': col_name.count(';'), '\t': col_name.count('\t'), '|': col_name.count('|'), ',': col_name.count(',')}
            detected_sep = max(counts, key=counts.get)
            if counts[detected_sep] > 0:
                lines = [col_name] + df.iloc[:, 0].astype(str).tolist()
                reader = csv.reader(lines, delimiter=detected_sep)
                parsed_data = list(reader)
                
                if len(parsed_data) > 1:
                    header = parsed_data[0]
                    rows = []
                    for row in parsed_data[1:]:
                        if len(row) > len(header):
                            row = row[:len(header)]
                        elif len(row) < len(header):
                            row = row + [None] * (len(header) - len(row))
                        rows.append(row)
                    df = pd.DataFrame(rows, columns=header)
                    
                    # Convert string columns to numeric where possible so models don't fail on strings
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                        
                    fixes_applied.append(f'Extracted columns from single column using "{detected_sep}" delimiter')
        except Exception as e:
            logger.error(f"Universal split failed: {e}")
    
    # --- Step 2: Promote header from first data row if needed ---
    if 'HEADER_IN_DATA' in issue_codes:
        new_headers = df.iloc[0].astype(str).tolist()
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = new_headers
        fixes_applied.append('Promoted first data row to column headers')
    
    # --- Step 3: Fix unnamed / empty headers ---
    if 'UNNAMED_HEADERS' in issue_codes:
        new_cols = []
        unnamed_counter = 1
        for col in df.columns:
            if str(col).startswith('Unnamed:') or str(col).strip() == '':
                new_cols.append(f'Column_{unnamed_counter}')
                unnamed_counter += 1
            else:
                new_cols.append(col)
        df.columns = new_cols
        fixes_applied.append(f'Renamed {unnamed_counter - 1} unnamed columns')
    
    # --- Step 4: Remove ghost columns (>95% NaN) ---
    if 'GHOST_COLUMNS' in issue_codes:
        before_cols = len(df.columns)
        threshold = 0.95
        ghost_mask = df.isna().sum() / max(len(df), 1) > threshold
        ghost_names = df.columns[ghost_mask].tolist()
        df = df.loc[:, ~ghost_mask]
        removed = before_cols - len(df.columns)
        if removed > 0:
            fixes_applied.append(f'Removed {removed} empty ghost column(s): {ghost_names[:5]}')
    
    # --- Step 5: Strip whitespace from text columns ---
    if 'WHITESPACE' in issue_codes:
        obj_cols = df.select_dtypes(include=['object']).columns
        for col in obj_cols:
            df[col] = df[col].astype(str).str.strip()
            # Restore actual NaN where we stringified 'nan'
            df[col] = df[col].replace({'nan': np.nan, 'None': np.nan, '': np.nan})
        fixes_applied.append(f'Stripped whitespace from {len(obj_cols)} text column(s)')
    
    # --- Step 6: Deduplicate column names ---
    if 'DUPLICATE_COLUMNS' in issue_codes:
        seen = {}
        new_names = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_names.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 1
                new_names.append(col)
        df.columns = new_names
        fixes_applied.append('Deduplicated column names')
    
    # --- Step 7: Remove fully empty rows ---
    if 'EMPTY_ROWS' in issue_codes:
        before_rows = len(df)
        df = df.dropna(how='all').reset_index(drop=True)
        removed = before_rows - len(df)
        if removed > 0:
            fixes_applied.append(f'Removed {removed} fully empty rows')
    
    # --- Always: auto-detect datetime columns ---
    try:
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                df[col] = pd.to_datetime(df[col], errors='ignore')
    except Exception:
        pass
    
    return df, fixes_applied
