from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC, SVR
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import os
import json
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# --- Dependencies ---
# Make sure to install all required libraries:
# pip install flask flask-cors pandas scikit-learn xgboost matplotlib seaborn openpyxl
# (openpyxl is required for .xlsx file support)
# --------------------


# Custom JSON encoder to handle NaN values
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            if np.isnan(obj):
                return None
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super().default(obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder  # Use custom JSON encoder
CORS(app)  # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Custom error handler for file size limit
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'error': 'File too large. Maximum file size is 100MB. Please use a smaller file or compress your data.'}), 413

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

import uuid
import time

# Session storage for global state
SESSIONS = {}

def get_session(session_id):
    if not session_id or session_id not in SESSIONS:
        return None
    SESSIONS[session_id]['last_accessed'] = time.time()
    return SESSIONS[session_id]

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_visualization(data, plot_type, x_col=None, y_col=None, hue_col=None):
    """Create various types of visualizations"""
    # Limit data size for performance (use first 10000 rows for large datasets)
    if len(data) > 10000:
        data = data.head(10000)
        print(f"Using first 10000 rows for visualization (dataset has {len(data)} rows)")
    
    plt.figure(figsize=(10, 6))
    
    # --- START FIX: Add data type and column validation ---
    if x_col and x_col not in data.columns:
            raise ValueError(f"Column '{x_col}' not found in data.")
    if y_col and y_col not in data.columns:
            raise ValueError(f"Column '{y_col}' not found in data.")
            
    if plot_type == 'histogram' and x_col:
        if not pd.api.types.is_numeric_dtype(data[x_col]):
            raise ValueError(f"Histogram requires a numeric column. '{x_col}' is not numeric.")
        plot_data = data[x_col].dropna()
        if plot_data.empty:
            raise ValueError(f"No valid data in '{x_col}' to plot a histogram.")
        plt.hist(plot_data, bins=30, alpha=0.7, edgecolor='black')
        plt.title(f'Histogram of {x_col}')
        plt.xlabel(x_col)
        plt.ylabel('Frequency')
    
    elif plot_type == 'scatter' and x_col and y_col:
        if not pd.api.types.is_numeric_dtype(data[x_col]) or not pd.api.types.is_numeric_dtype(data[y_col]):
            raise ValueError(f"Scatter plot requires two numeric columns. '{x_col}' or '{y_col}' (or both) are not numeric.")
        plt.scatter(data[x_col], data[y_col], alpha=0.6)
        plt.title(f'Scatter Plot: {x_col} vs {y_col}')
        plt.xlabel(x_col)
        plt.ylabel(y_col)
    
    elif plot_type == 'boxplot' and x_col:
        if not pd.api.types.is_numeric_dtype(data[x_col]):
            raise ValueError(f"Box plot requires a numeric column. '{x_col}' is not numeric.")
        plot_data = data[x_col].dropna()
        if plot_data.empty:
            raise ValueError(f"No valid data in '{x_col}' to plot a box plot.")
        plt.boxplot(plot_data)
        plt.title(f'Box Plot of {x_col}')
        plt.ylabel(x_col)
    # --- END FIX ---
    
    elif plot_type == 'correlation':
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            corr_matrix = numeric_data.corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title('Correlation Matrix')
        else:
            plt.text(0.5, 0.5, 'Not enough numeric columns for correlation', 
                    ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Correlation Matrix')
    
    elif plot_type == 'pairplot' and len(data.select_dtypes(include=[np.number]).columns) >= 2:
        numeric_data = data.select_dtypes(include=[np.number])
        if len(numeric_data.columns) > 1:
            sns.pairplot(numeric_data.head(100))  # Limit to first 100 rows for performance
            plt.title('Pair Plot')
    
    elif plot_type == 'strip':
        # Rainbow strip plot
        try:
            if x_col and y_col:
                if data[x_col].dropna().empty and data[y_col].dropna().empty:
                        raise ValueError(f"No valid data in '{x_col}' or '{y_col}' to plot.")
                sns.stripplot(x=data[x_col], y=data[y_col], palette='rainbow', alpha=0.7)
                plt.title(f'Rainbow Strip Plot: {x_col} vs {y_col}')
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            elif x_col:
                if data[x_col].dropna().empty:
                        raise ValueError(f"No valid data in '{x_col}' to plot.")
                sns.stripplot(x=data[x_col], palette='rainbow', alpha=0.7)
                plt.title(f'Rainbow Strip Plot of {x_col}')
                plt.xlabel(x_col)
            else:
                plt.text(0.5, 0.5, 'Select at least X column for strip plot',
                         ha='center', va='center', transform=plt.gca().transAxes)
                plt.title('Rainbow Strip Plot')
        except Exception as e:
            plt.text(0.5, 0.5, f'Error creating strip plot: {str(e)}',
                     ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Rainbow Strip Plot')
    
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    # Avoid 404 logs when the browser requests a favicon
    return ('', 204)

@app.route('/test')
def test():
    return jsonify({'status': 'OK', 'message': 'Server is running!'})

@app.route('/test_server')
def test_server():
    return send_file('test_server.html')

def reduce_mem_usage(df):
    """Iterate through all columns and modify the data type to reduce memory usage."""
    start_mem = df.memory_usage().sum() / 1024**2
    print(f"Memory usage of dataframe is {start_mem:.2f} MB")
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if col_type != object and not pd.api.types.is_datetime64_any_dtype(df[col]):
            c_min = df[col].min()
            c_max = df[col].max()
            if str(col_type)[:3] == 'int':
                if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                    df[col] = df[col].astype(np.int8)
                elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                    df[col] = df[col].astype(np.int16)
                elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                    df[col] = df[col].astype(np.int32)
                elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                    df[col] = df[col].astype(np.int64)  
            else:
                if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                    df[col] = df[col].astype(np.float32)
                else:
                    df[col] = df[col].astype(np.float64)
                    
    end_mem = df.memory_usage().sum() / 1024**2
    print(f"Memory usage after optimization is: {end_mem:.2f} MB")
    print(f"Decreased by {100 * (start_mem - end_mem) / start_mem:.1f}%")
    return df

@app.route('/upload', methods=['POST'])
def upload_file():
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        'data': None, 'model': None, 'scaler': None, 'target_encoder': None,
        'target_is_classification': False, 'feature_columns_final': None,
        'feature_columns_categorical': None, 'feature_stats': None,
        'categorical_encoder': None, 'last_accessed': time.time()
    }
    session = SESSIONS[session_id]
    
    try:
        print("Upload endpoint called")  # Debug print
        
        if 'file' not in request.files:
            print("No file in request")  # Debug print
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        print(f"File received: {file.filename}")  # Debug print
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not filename:
                 return jsonify({'error': 'Invalid file name. Please rename the file and try again.'}), 400
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f"File saved to: {filepath}")  # Debug print
            
            try:
                # Read the file based on extension
                print(f"Reading file: {filename}")  # Debug print
                if filename.endswith('.csv'):
                    session['data'] = pd.read_csv(filepath)
                else:
                    # This requires 'openpyxl' (for .xlsx) or 'xlrd' (for .xls)
                    session['data'] = pd.read_excel(filepath)
                
                # Compress the dataframe in memory
                session['data'] = reduce_mem_usage(session['data'])
                
                print(f"Data loaded successfully: {session['data'].shape}")  # Debug print
                
                # --- FIX: Auto-detect and convert datetime columns on upload ---
                try:
                    for col in session['data'].columns:
                        if session['data'][col].dtype == 'object':
                            # Try to convert object columns to datetime
                            session['data'][col] = pd.to_datetime(session['data'][col], errors='ignore')
                    
                    # Convert any detected datetime columns to numeric (timestamps)
                    # This is now handled in train_model, but we can update dtypes here
                    pass # Defer conversion to training to keep data readable
                except Exception as e_dt:
                    print(f"Warning: Could not auto-parse datetimes: {str(e_dt)}")
                # ---
                
                # For very large datasets, provide a warning
                if len(session['data']) > 50000:
                    print(f"Large dataset detected: {len(session['data'])} rows. Processing may take time.")
                
                # Clean up the file
                os.remove(filepath)
                
            except Exception as e:
                print(f"Error reading file: {str(e)}")  # Debug print
                # Try to remove the file even if reading failed
                try:
                    os.remove(filepath)
                except Exception:
                    pass # Ignore error on cleanup
                return jsonify({'error': f'Error reading file: {str(e)}. Make sure file is not corrupted and all dependencies (like openpyxl) are installed.'}), 400
            
            # --- Added robust error handling for data processing ---
            try:
                # Get basic info about the dataset
                # Handle NaN values for JSON serialization
                # Detect empty/NaN rows (without mutating original data)
                try:
                    df = session['data']
                    # Treat empty strings/whitespace in object columns as empty for detection only
                    object_cols = df.select_dtypes(include=['object']).columns
                    obj_empty = None
                    if len(object_cols) > 0:
                        # True where object cell is empty after stripping
                        obj_empty = df[object_cols].apply(lambda s: s.astype(str).str.strip() == '')
                    # NaN mask across all columns
                    nan_mask = df.isna()
                    # For fully empty rows, consider either NaN or empty-string in object columns as empty
                    if obj_empty is not None:
                        # Align with all columns
                        obj_empty_all_cols = obj_empty.reindex(columns=df.columns, fill_value=False)
                        empty_or_nan = nan_mask | obj_empty_all_cols
                    else:
                        empty_or_nan = nan_mask
                    fully_empty_rows_mask = empty_or_nan.all(axis=1)
                    fully_nan_rows_mask = nan_mask.all(axis=1)
                    any_nan_rows_mask = nan_mask.any(axis=1)
                    # Build samples (limit to 50 indices for performance)
                    def sample_indices(mask, limit=50):
                        idx = df.index[mask]
                        # convert to python native list to ensure JSON serialization
                        return list(map(lambda x: int(x) if isinstance(x, (np.integer,)) else x, idx[:limit]))
                    row_quality = {
                        'fully_empty_count': int(fully_empty_rows_mask.sum()),
                        'fully_empty_indices_sample': sample_indices(fully_empty_rows_mask),
                        'fully_nan_count': int(fully_nan_rows_mask.sum()),
                        'fully_nan_indices_sample': sample_indices(fully_nan_rows_mask),
                        'any_nan_count': int(any_nan_rows_mask.sum()),
                        'any_nan_indices_sample': sample_indices(any_nan_rows_mask)
                    }
                except Exception as e_row:
                    print(f"Warning: Error detecting row quality: {str(e_row)}")
                    # If detection fails for any reason, fall back silently
                    row_quality = {
                        'fully_empty_count': 0,
                        'fully_empty_indices_sample': [],
                        'fully_nan_count': 0,
                        'fully_nan_indices_sample': [],
                        'any_nan_count': 0,
                        'any_nan_indices_sample': []
                    }
                
                def clean_for_json(obj):
                    if isinstance(obj, dict):
                        return {k: clean_for_json(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_for_json(item) for item in obj]
                    elif isinstance(obj, (np.integer, np.floating)):
                        if np.isnan(obj):
                            return None
                        return obj.item()
                    elif isinstance(obj, np.ndarray):
                        return obj.tolist()
                    else:
                        return obj
                
                # Create data info with proper NaN handling
                info = {
                    'shape': session['data'].shape,
                    'columns': session['data'].columns.tolist(),
                    'dtypes': session['data'].dtypes.astype(str).to_dict(),
                    'missing_values': session['data'].isnull().sum().to_dict(),
                    'numeric_columns': session['data'].select_dtypes(include=[np.number]).columns.tolist(),
                    'categorical_columns': session['data'].select_dtypes(include=['object']).columns.tolist(),
                    'first_few_rows': session['data'].head().fillna('N/A').to_dict('records'),
                    'row_quality': row_quality
                }
                
                # Add simple numeric stats (mean and max) for convenience
                try:
                    numeric_df = session['data'].select_dtypes(include=[np.number])
                    numeric_stats = {}
                    for col in numeric_df.columns:
                        s = numeric_df[col]
                        numeric_stats[col] = {
                            'mean': float(s.mean()) if s.count() > 0 else None,
                            'max': float(s.max()) if s.count() > 0 else None
                        }
                    info['numeric_stats'] = numeric_stats
                except Exception as e_stats:
                    print(f"Warning: Error calculating numeric stats: {str(e_stats)}")
                    info['numeric_stats'] = {}
                
                # Clean the info for JSON serialization
                info = clean_for_json(info)
                
                print("Returning success response")  # Debug print
                return jsonify({'success': True, 'data_info': info, 'session_id': session_id})

            except Exception as e:
                print(f"Error processing data info: {str(e)}")  # Debug print
                return jsonify({'error': f'Error processing data after upload: {str(e)}'}), 500
            # --- End of new try...except block ---
        
        return jsonify({'error': 'Invalid file type'}), 400
        
    except Exception as e:
        print(f"Unexpected error in upload: {str(e)}")  # Debug print
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/visualize', methods=['POST'])
def visualize():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    plot_type = data.get('plot_type')
    x_col = data.get('x_col')
    y_col = data.get('y_col')
    hue_col = data.get('hue_col')
    
    try:
        plot_url = create_visualization(current_data, plot_type, x_col, y_col, hue_col)
        return jsonify({'success': True, 'plot_url': plot_url})
    except Exception as e:
        # This will now catch the ValueErrors from create_visualization
        print(f"Error in /visualize: {str(e)}")
        return jsonify({'error': f'Error creating visualization: {str(e)}'}), 400

@app.route('/train_model', methods=['POST'])
def train_model():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    
    target_column = data.get('target_column')
    feature_columns = data.get('feature_columns', [])
    test_size = data.get('test_size', 0.2)
    model_type = data.get('model_type', 'svm')  # svm, random_forest, xgboost
    
    if not target_column or not feature_columns:
        return jsonify({'error': 'Target column and feature columns are required'}), 400
    
    try:
        print(f"Training {model_type} with target: {target_column}, features: {feature_columns}")

        # Validate columns
        df_cols = set(current_data.columns.tolist())
        missing_features = [c for c in feature_columns if c not in df_cols]
        if missing_features:
            return jsonify({'error': f'Missing feature columns: {missing_features}'}), 400
        if target_column not in df_cols:
            return jsonify({'error': f'Missing target column: {target_column}'}), 400
        # Ensure target is not in features
        feature_columns = [c for c in feature_columns if c != target_column]
        if not feature_columns:
            return jsonify({'error': 'No valid feature columns after excluding target'}), 400

        # Work on a copy and normalize empty strings in object cols to NaN for robust cleaning
        work_df = current_data[feature_columns + [target_column]].copy()
        obj_cols = work_df.select_dtypes(include=['object']).columns
        if len(obj_cols) > 0:
            work_df[obj_cols] = work_df[obj_cols].apply(lambda s: s.astype(str).str.strip().replace({'': np.nan}))
        
        # Drop rows with missing/empty target
        before_rows = len(work_df)
        work_df = work_df[work_df[target_column].notna()]
        dropped_for_target = before_rows - len(work_df)
        if dropped_for_target > 0:
            print(f"Dropped {dropped_for_target} rows with empty/NaN target")
        if len(work_df) < 2:
            return jsonify({'error': 'Not enough rows with a valid target after cleaning'}), 400

        # Prepare the data
        X = work_df[feature_columns]
        y = work_df[target_column]
        
        print(f"X shape: {X.shape}, y shape: {y.shape}")
        
        # --- START DATETIME FIX ---
        datetime_cols = X.select_dtypes(include=['datetime', 'datetime64', 'datetime64[ns]']).columns
        if len(datetime_cols) > 0:
            print(f"Converting datetime columns to numeric: {datetime_cols.tolist()}")
            for col in datetime_cols:
                # Fill NaT with the median datetime before converting to int64
                if X[col].isna().any():
                    median_time = X[col].dropna().median()
                    X[col] = X[col].fillna(median_time if not pd.isna(median_time) else pd.Timestamp(0))
                X[col] = X[col].astype('int64') // 10**9
        # --- END DATETIME FIX ---
        
        # Handle missing values in FEATURES
        # For numeric columns, fill with mean (datetime columns are now numeric)
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
        
        # For categorical columns, fill with mode
        categorical_cols = X.select_dtypes(include=['object']).columns
        current_feature_columns_categorical = categorical_cols.tolist() # Save original categorical col names
        for col in categorical_cols:
            if not X[col].empty:
                mode_value = X[col].mode()
                if not mode_value.empty:
                    X[col] = X[col].fillna(mode_value.iloc[0])
                else:
                    X[col] = X[col].fillna('Unknown') # Fallback if mode is empty
        
        # Handle target variable and determine problem type
        if y.dtype == 'object':
            # Categorical target - classification problem
            y = y.fillna(y.mode().iloc[0] if not y.mode().empty else 'Unknown')
            current_target_encoder = LabelEncoder()
            y = current_target_encoder.fit_transform(y)
            current_target_is_classification = True
            print("Classification problem detected (object target)")
        else:
            # Numeric target - check if it's classification or regression
            unique_values = len(y.unique())
            total_values = len(y)
            
            # If less than 20 unique values and they represent less than 10% of data, treat as classification
            if unique_values <= 20 and (unique_values / total_values) < 0.1:
                # Treat as classification (discrete classes)
                y = y.fillna(y.mode().iloc[0] if not y.mode().empty else 0)
                current_target_encoder = LabelEncoder()
                y = current_target_encoder.fit_transform(y)
                current_target_is_classification = True
                print("Classification problem detected (numeric with few unique values)")
            else:
                # Treat as regression (continuous values)
                y = y.fillna(y.mean())
                current_target_encoder = None
                current_target_is_classification = False
                print("Regression problem detected (continuous numeric target)")
        
        # --- FIX: Handle categorical features in X using One-Hot Encoding ---
        global current_categorical_encoder
        if current_feature_columns_categorical:
            print(f"Applying One-Hot Encoding to: {current_feature_columns_categorical}")
            current_categorical_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False, drop='first')
            encoded_cats = current_categorical_encoder.fit_transform(X[current_feature_columns_categorical].astype(str))
            
            # Create a dataframe with the new encoded columns
            encoded_cols = current_categorical_encoder.get_feature_names_out(current_feature_columns_categorical)
            encoded_df = pd.DataFrame(encoded_cats, columns=encoded_cols, index=X.index)
            
            # Drop original categorical columns and concatenate encoded ones
            X = X.drop(columns=current_feature_columns_categorical)
            X = pd.concat([X, encoded_df], axis=1)
        else:
            current_categorical_encoder = None
            
        # Store the final feature columns (after dummies)
        current_feature_columns_final = X.columns.tolist()
        print(f"Final feature count after encoding: {len(current_feature_columns_final)}")
        
        # Convert all features to numeric (should be redundant now but safe)
        X = X.astype(float)

        # Final sanity checks
        if np.isnan(X.values).any():
            print("NaNs found after cleaning, filling with 0")
            X = X.fillna(0) # Final fallback
        if len(X) < 2:
            return jsonify({'error': 'Not enough rows to train after cleaning'}), 400
        
        # Persist simple stats for prediction UI (on final columns)
        current_feature_stats = {}
        for c in X.columns:
            s = X[c]
            current_feature_stats[c] = {
                'mean': float(s.mean()) if s.count() > 0 else None,
                'min': float(s.min()) if s.count() > 0 else None,
                'max': float(s.max()) if s.count() > 0 else None
            }
        
        # Scale features
        current_scaler = StandardScaler()
        X_scaled = current_scaler.fit_transform(X)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        if len(X_train) == 0 or len(X_test) == 0:
            return jsonify({'error': 'Invalid test_size for dataset size. Adjust test size or provide more rows.'}), 400
        
        # Train model based on problem type and model selection
        if model_type == 'svm':
            if current_target_is_classification:
                current_model = SVC(kernel='rbf', random_state=42)
                print("Training SVM Classifier")
            else:
                current_model = SVR(kernel='rbf')
                print("Training SVM Regressor")
        elif model_type == 'random_forest':
            if current_target_is_classification:
                current_model = RandomForestClassifier(n_estimators=100, random_state=42)
                print("Training Random Forest Classifier")
            else:
                current_model = RandomForestRegressor(n_estimators=100, random_state=42)
                print("Training Random Forest Regressor")
        elif model_type == 'xgboost':
            if current_target_is_classification:
                current_model = xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', use_label_encoder=False)
                print("Training XGBoost Classifier")
            else:
                current_model = xgb.XGBRegressor(n_estimators=100, random_state=42, eval_metric='rmse')
                print("Training XGBoost Regressor")
        elif model_type == 'lightgbm':
            if current_target_is_classification:
                current_model = lgb.LGBMClassifier(random_state=42)
                print("Training LightGBM Classifier")
            else:
                current_model = lgb.LGBMRegressor(random_state=42)
                print("Training LightGBM Regressor")
        else:
            return jsonify({'error': 'Invalid model type. Choose from: svm, random_forest, xgboost, lightgbm'}), 400
        
        current_model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = current_model.predict(X_test)
        
        # Calculate metrics based on problem type
        report = {}
        accuracy = None # Use for main metric (accuracy or R2)
        
        if current_target_is_classification:
            accuracy = accuracy_score(y_test, y_pred)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0) # Added zero_division=0
            print(f"Classification accuracy: {accuracy:.4f}")
        else:
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            accuracy = r2  # Use R² as the main metric for regression
            report = {
                'mse': mse,
                'r2_score': r2,
                'rmse': np.sqrt(mse)
            }
            print(f"Regression R² score: {r2:.4f}, MSE: {mse:.4f}")
        
        # Create confusion matrix plot (for classification) or scatter plot (for regression)
        cm_plot_url = None
        if current_target_is_classification:
            plt.figure(figsize=(8, 6))
            cm = confusion_matrix(y_test, y_pred)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title('Confusion Matrix')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
        else:
            # For regression, create a scatter plot of actual vs predicted
            plt.figure(figsize=(8, 6))
            plt.scatter(y_test, y_pred, alpha=0.6)
            plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
            plt.xlabel('Actual Values')
            plt.ylabel('Predicted Values')
            plt.title('Actual vs Predicted Values')
        
        img = io.BytesIO()
        plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
        img.seek(0)
        cm_plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        
        # Handle NaN values for JSON serialization
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                if np.isnan(obj):
                    return None
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        # Get feature importance if available
        feature_importance = {}
        if hasattr(current_model, 'feature_importances_'):
            feature_importance = dict(zip(current_feature_columns_final, current_model.feature_importances_))
        elif hasattr(current_model, 'coef_'):
            # For SVM, use coefficients as importance
            coefs = current_model.coef_[0] if len(current_model.coef_.shape) > 1 else current_model.coef_
            feature_importance = dict(zip(current_feature_columns_final, abs(coefs)))
        
        result = {
            'success': True,
            'model_type': model_type,
            'problem_type': 'classification' if current_target_is_classification else 'regression',
            'accuracy': accuracy,
            'classification_report': report,
            'evaluation_plot': cm_plot_url, # Renamed for clarity
            'feature_importance': feature_importance,
            'feature_columns': current_feature_columns_final,
            'feature_stats': current_feature_stats
        }
        
        # Clean the result for JSON serialization
        result = clean_for_json(result)
        
        # Save state to session
        session['target_encoder'] = current_target_encoder
        session['target_is_classification'] = current_target_is_classification
        session['categorical_encoder'] = current_categorical_encoder
        session['feature_columns_categorical'] = current_feature_columns_categorical
        session['feature_columns_final'] = current_feature_columns_final
        session['feature_stats'] = current_feature_stats
        session['scaler'] = current_scaler
        session['model'] = current_model
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error training model: {str(e)}")
        return jsonify({'error': f'Error training model: {str(e)}'}), 400

@app.route('/compare_models', methods=['POST'])
def compare_models():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    target_column = data.get('target_column')
    feature_columns = data.get('feature_columns', [])
    test_size = data.get('test_size', 0.2)
    
    if not target_column or not feature_columns:
        return jsonify({'error': 'Target column and feature columns are required'}), 400
    
    try:
        print(f"Comparing models with target: {target_column}, features: {feature_columns}")
        
        # Work on a copy and normalize
        work_df = current_data[feature_columns + [target_column]].copy()
        obj_cols = work_df.select_dtypes(include=['object']).columns
        if len(obj_cols) > 0:
            work_df[obj_cols] = work_df[obj_cols].apply(lambda s: s.astype(str).str.strip().replace({'': np.nan}))
        
        # Drop rows with missing/empty target
        work_df = work_df[work_df[target_column].notna()]
        if len(work_df) < 2:
            return jsonify({'error': 'Not enough rows with a valid target'}), 400

        # Prepare the data
        X = work_df[feature_columns]
        y = work_df[target_column]
        
        # --- START DATETIME FIX ---
        datetime_cols = X.select_dtypes(include=['datetime', 'datetime64', 'datetime64[ns]']).columns
        if len(datetime_cols) > 0:
            print(f"Converting datetime columns to numeric: {datetime_cols.tolist()}")
            for col in datetime_cols:
                if X[col].isna().any():
                    median_time = X[col].dropna().median()
                    X[col] = X[col].fillna(median_time if not pd.isna(median_time) else pd.Timestamp(0))
                X[col] = X[col].astype('int64') // 10**9 
        # --- END DATETIME FIX ---
        
        # Handle missing values
        numeric_cols = X.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].mean())
        
        categorical_cols = X.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if not X[col].empty:
                mode_value = X[col].mode()
                if not mode_value.empty:
                    X[col] = X[col].fillna(mode_value.iloc[0])
                else:
                    X[col] = X[col].fillna('Unknown')
        
        # Determine problem type
        is_classification = False
        if y.dtype == 'object':
            y = y.fillna(y.mode().iloc[0] if not y.mode().empty else 'Unknown')
            label_encoder = LabelEncoder()
            y = label_encoder.fit_transform(y)
            is_classification = True
        else:
            unique_values = len(y.unique())
            total_values = len(y)
            if unique_values <= 20 and (unique_values / total_values) < 0.1:
                y = y.fillna(y.mode().iloc[0] if not y.mode().empty else 0)
                label_encoder = LabelEncoder()
                y = label_encoder.fit_transform(y)
                is_classification = True
            else:
                y = y.fillna(y.mean())
                label_encoder = None
                is_classification = False
        
        # --- FIX: Apply OneHotEncoder ---
        if len(categorical_cols) > 0:
            comp_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False, drop='first')
            encoded_cats = comp_encoder.fit_transform(X[categorical_cols].astype(str))
            encoded_cols = comp_encoder.get_feature_names_out(categorical_cols)
            encoded_df = pd.DataFrame(encoded_cats, columns=encoded_cols, index=X.index)
            X = X.drop(columns=categorical_cols)
            X = pd.concat([X, encoded_df], axis=1)
        
        X = X.astype(float)
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42
        )
        
        # Define models to compare
        models = {}
        if is_classification:
            models = {
                'SVM': SVC(kernel='rbf', random_state=42),
                'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'XGBoost': xgb.XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss', use_label_encoder=False)
            }
        else:
            models = {
                'SVM': SVR(kernel='rbf'),
                'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
                'XGBoost': xgb.XGBRegressor(n_estimators=100, random_state=42, eval_metric='rmse')
            }
        
        # Train and evaluate each model
        results = {}
        for name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                if is_classification:
                    accuracy = accuracy_score(y_test, y_pred)
                    results[name] = {'accuracy': accuracy}
                else:
                    mse = mean_squared_error(y_test, y_pred)
                    r2 = r2_score(y_test, y_pred)
                    results[name] = {'mse': mse, 'r2_score': r2, 'rmse': np.sqrt(mse)}
                
                print(f"{name} - {'Accuracy' if is_classification else 'R²'}: {results[name]['accuracy' if is_classification else 'r2_score']:.4f}")
                
            except Exception as e:
                print(f"Error training {name}: {str(e)}")
                results[name] = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'problem_type': 'classification' if is_classification else 'regression',
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': f'Error comparing models: {str(e)}'}), 400

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['model'] is None:
        return jsonify({'error': 'No trained model available or session expired. Please train a model first.'}), 400
        
    current_model = session['model']
    current_scaler = session['scaler']
    current_target_encoder = session['target_encoder']
    current_target_is_classification = session['target_is_classification']
    current_feature_columns_final = session['feature_columns_final']
    current_feature_columns_categorical = session['feature_columns_categorical']
    current_categorical_encoder = session['categorical_encoder']
    # --- FIX: Expect a dictionary of features, not a list ---
    features_dict = data.get('features', {})
    
    if not isinstance(features_dict, dict) or not features_dict:
        return jsonify({'error': 'Features must be provided as a non-empty dictionary (e.g., {"col1": value1, "col2": value2})'}), 400
    
    try:
        # Create a single-row DataFrame from the input dictionary
        input_df = pd.DataFrame([features_dict])

        # --- START DATETIME FIX ---
        datetime_cols = input_df.select_dtypes(include=['datetime', 'datetime64', 'datetime64[ns]']).columns
        if len(datetime_cols) > 0:
            print(f"Converting datetime columns to numeric for prediction: {datetime_cols.tolist()}")
            for col in datetime_cols:
                if input_df[col].isna().any():
                    input_df[col] = input_df[col].fillna(pd.Timestamp(0))
                input_df[col] = input_df[col].astype('int64') // 10**9 
        # --- END DATETIME FIX ---

        # Ensure dtypes match training data for categorical columns before encoding
        if current_feature_columns_categorical and current_categorical_encoder:
            for col in current_feature_columns_categorical:
                if col in input_df.columns:
                    input_df[col] = input_df[col].astype(str)
                else:
                    input_df[col] = 'Unknown' # Fallback
            
            # Apply OneHotEncoder
            encoded_cats = current_categorical_encoder.transform(input_df[current_feature_columns_categorical])
            encoded_cols = current_categorical_encoder.get_feature_names_out(current_feature_columns_categorical)
            encoded_df = pd.DataFrame(encoded_cats, columns=encoded_cols, index=input_df.index)
            
            input_df = input_df.drop(columns=current_feature_columns_categorical)
            input_df = pd.concat([input_df, encoded_df], axis=1)
        
        # Align columns to match model's training columns precisely
        input_df = input_df.reindex(columns=current_feature_columns_final, fill_value=0)
        
        # Ensure all columns are float for scaler
        features_array = input_df.astype(float).values
        
        # Validate feature length (should always match now)
        expected = len(current_feature_columns_final)
        if features_array.shape[1] != expected:
            return jsonify({'error': f'Feature mismatch after processing. Expected {expected} features, got {features_array.shape[1]}.'}), 500
        
        # Scale the features
        features_scaled = current_scaler.transform(features_array)
        
        # Make prediction
        prediction = current_model.predict(features_scaled)[0]
        
        # If we have a target encoder, decode the prediction (for classification)
        if current_target_is_classification and current_target_encoder:
            # Ensure prediction is an integer for inverse_transform
            prediction_int = int(np.round(prediction))
            prediction_decoded = current_target_encoder.inverse_transform([prediction_int])[0]
            # Convert numpy types to native python types for JSON
            prediction_out = prediction_decoded.item() if hasattr(prediction_decoded, 'item') else prediction_decoded
        else:
            # For regression, ensure it's a standard float
            prediction_out = float(prediction)
        
        session['latest_prediction'] = {
            'features': features_dict,
            'prediction': prediction_out
        }
        
        return jsonify({
            'success': True,
            'prediction': prediction_out,
            'problem_type': 'classification' if current_target_is_classification else 'regression'
        })
        
    except Exception as e:
        print(f"Error making prediction: {str(e)}")
        return jsonify({'error': f'Error making prediction: {str(e)}'}), 400

@app.route('/feature_info', methods=['GET'])
def feature_info():
    """Return trained feature columns and basic stats (mean/min/max)"""
    session_id = request.args.get('session_id')
    session = get_session(session_id)
    
    if not session or session['feature_columns_final'] is None:
        return jsonify({'error': 'No trained model available or session expired'}), 400
        
    return jsonify({
        'success': True, 
        'feature_columns': session['feature_columns_final'], 
        'feature_stats': session['feature_stats']
    })

@app.route('/data_summary')
def data_summary():
    session_id = request.args.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    
    try:
        # Handle NaN values for JSON serialization
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                if np.isnan(obj):
                    return None
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        # Use pandas .describe() for numeric and categorical
        numeric_desc = current_data.describe(include=[np.number]).to_dict()
        categorical_desc = current_data.describe(include=['object']).to_dict()

        summary = {
            'shape': current_data.shape,
            'columns': current_data.columns.tolist(),
            'dtypes': current_data.dtypes.astype(str).to_dict(),
            'missing_values': current_data.isnull().sum().to_dict(),
            'numeric_summary': numeric_desc,
            'categorical_summary': categorical_desc
        }
        
        # Clean the summary for JSON serialization
        summary = clean_for_json(summary)
        
        return jsonify({'success': True, 'summary': summary})
        
    except Exception as e:
        return jsonify({'error': f'Error generating summary: {str(e)}'}), 400

@app.route('/stats_analysis', methods=['POST'])
def stats_analysis():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    try:
        analysis_type = data.get('analysis_type', 'summary')  # summary, column_stats, correlation, missingness, value_counts
        columns = data.get('columns', [])
        top_n = int(data.get('top_n', 10))

        df = current_data
        result = {}

        if analysis_type == 'summary':
            # Numeric summary
            result['numeric_summary'] = df.select_dtypes(include=[np.number]).describe().to_dict()
            # Categorical summary (count of unique, top, freq)
            cat = df.select_dtypes(include=['object']).copy()
            cat_desc = {}
            for c in cat.columns:
                vc = cat[c].value_counts(dropna=False)
                cat_desc[c] = {
                    'unique': int(cat[c].nunique(dropna=False)),
                    'top': None if vc.empty else str(vc.index[0]),
                    'freq': 0 if vc.empty else int(vc.iloc[0])
                }
            result['categorical_summary'] = cat_desc

        elif analysis_type == 'column_stats':
            if not columns:
                return jsonify({'error': 'columns is required for column_stats'}), 400
            sub = df[columns]
            # For non-numeric, include counts and unique
            stats = {}
            for c in sub.columns:
                s = sub[c]
                if np.issubdtype(s.dropna().dtype, np.number):
                    stats[c] = {
                        'count': int(s.count()),
                        'mean': float(s.mean()) if s.count() > 0 else None,
                        'std': float(s.std()) if s.count() > 0 else None,
                        'min': float(s.min()) if s.count() > 0 else None,
                        '25%': float(s.quantile(0.25)) if s.count() > 0 else None,
                        '50%': float(s.median()) if s.count() > 0 else None,
                        '75%': float(s.quantile(0.75)) if s.count() > 0 else None,
                        'max': float(s.max()) if s.count() > 0 else None,
                        'missing': int(s.isna().sum())
                    }
                else:
                    vc = s.value_counts(dropna=False)
                    stats[c] = {
                        'count': int(s.count()),
                        'unique': int(s.nunique(dropna=False)),
                        'top': None if vc.empty else str(vc.index[0]),
                        'freq': 0 if vc.empty else int(vc.iloc[0]),
                        'missing': int(s.isna().sum())
                    }
            result['column_stats'] = stats

        elif analysis_type == 'correlation':
            num = df.select_dtypes(include=[np.number])
            if num.shape[1] < 2:
                return jsonify({'error': 'Not enough numeric columns for correlation'}), 400
            result['correlation'] = num.corr().to_dict()

        elif analysis_type == 'missingness':
            miss = df.isna().sum().to_dict()
            result['missing_values'] = miss
            result['missing_ratio'] = {k: (float(v) / float(len(df))) for k, v in miss.items() if len(df) > 0}

        elif analysis_type == 'value_counts':
            if not columns:
                return jsonify({'error': 'columns is required for value_counts'}), 400
            vc_out = {}
            for c in columns:
                if c not in df.columns:
                    return jsonify({'error': f'Column not found: {c}'}), 400
                vc = df[c].value_counts(dropna=False).head(top_n)
                vc_out[c] = {str(k): int(v) for k, v in vc.items()}
            result['value_counts'] = vc_out

        else:
            return jsonify({'error': 'Invalid analysis_type'}), 400

        # Use the custom JSON encoder to handle any remaining NaNs
        return jsonify(json.loads(json.dumps({'success': True, 'analysis_type': analysis_type, 'result': result}, cls=CustomJSONEncoder)))
    
    except Exception as e:
        return jsonify({'error': f'Error computing analysis: {str(e)}'}), 400

# --- START: NEW POWER BI-LIKE AGGREGATION ENDPOINT ---
@app.route('/aggregate', methods=['POST'])
def aggregate_data():
    """
    Acts like a Power BI aggregation engine.
    Receives dimensions, measures, and time-grouping settings.
    Returns aggregated data as JSON, not a plot.
    """
    data = request.get_json() or {}
    session_id = data.get('session_id')
    session = get_session(session_id)
    if not session or session['data'] is None:
        return jsonify({'error': 'No data loaded or session expired'}), 400
    current_data = session['data']
    
    try:
        dimensions = data.get('dimensions', []) # e.g., ['Region', 'Category']
        measures = data.get('measures', [])     # e.g., ['Sales', 'Profit']
        aggregations = data.get('aggregations', {}) # e.g., {'Sales': 'sum', 'Profit': 'mean'}
        
        time_dimension = data.get('time_dimension') # e.g., 'Order Date'
        time_frequency = data.get('time_frequency') # e.g., 'M' (Month), 'Q' (Quarter), 'Y' (Year)

        if not dimensions and not time_dimension:
            return jsonify({'error': 'You must provide at least one dimension or a time dimension.'}), 400
        if not measures or not aggregations:
            return jsonify({'error': 'You must provide measures and their aggregation functions.'}), 400

        df = current_data.copy()
        
        # --- Validate and prepare columns ---
        all_cols = set(df.columns)
        for col in dimensions + measures:
            if col not in all_cols:
                return jsonify({'error': f"Column '{col}' not found."}), 400
        
        agg_config = {}
        for measure in measures:
            if measure not in aggregations:
                return jsonify({'error': f"Aggregation function for '{measure}' not provided."}), 400
            agg_config[measure] = aggregations[measure]

        grouping_keys = []
        if dimensions:
            grouping_keys.extend(dimensions)
            
        # --- Handle Time Dimension ---
        if time_dimension:
            if time_dimension not in all_cols:
                    return jsonify({'error': f"Time dimension column '{time_dimension}' not found."}), 400
            
            # Ensure the time column is datetime
            if not pd.api.types.is_datetime64_any_dtype(df[time_dimension]):
                try:
                    df[time_dimension] = pd.to_datetime(df[time_dimension])
                    print(f"Converted column '{time_dimension}' to datetime.")
                except Exception as e:
                    return jsonify({'error': f"Could not convert time dimension '{time_dimension}' to datetime: {str(e)}"}), 400
            
            if not time_frequency:
                return jsonify({'error': "You must provide 'time_frequency' (e.g., 'M', 'Q', 'Y') with 'time_dimension'."}), 400
            
            grouping_keys.append(pd.Grouper(key=time_dimension, freq=time_frequency))
        
        # --- Perform Aggregation ---
        print(f"Aggregating by: {grouping_keys} with config: {agg_config}")
        aggregated_df = df.groupby(grouping_keys).agg(agg_config)
        aggregated_df = aggregated_df.reset_index()

        # --- Clean for JSON ---
        # Convert timestamps to strings for JSON
        if time_dimension:
            aggregated_df[time_dimension] = aggregated_df[time_dimension].astype(str)
            
        # Store the aggregated dataframe in session for exporting
        session['bi_data'] = aggregated_df
        
        # Use the custom encoder-safe method
        result_json = aggregated_df.to_dict('records')
        cleaned_json = json.loads(json.dumps(result_json, cls=CustomJSONEncoder))
        
        return jsonify({'success': True, 'data': cleaned_json})

    except Exception as e:
        print(f"Error in /aggregate: {str(e)}")
        return jsonify({'error': f'Error during aggregation: {str(e)}'}), 400
# --- END: NEW POWER BI-LIKE AGGREGATION ENDPOINT ---

# --- START: EXPORT ENDPOINT ---
@app.route('/export', methods=['GET'])
def export_data():
    session_id = request.args.get('session_id')
    export_type = request.args.get('type') # 'raw', 'bi', 'prediction'
    export_format = request.args.get('format', 'csv') # 'csv' or 'xlsx'
    
    session = get_session(session_id)
    if not session:
        return jsonify({'error': 'Session expired or not found.'}), 400
        
    df_to_export = None
    filename_prefix = 'export'
    
    if export_type == 'raw':
        df_to_export = session.get('data')
        filename_prefix = 'raw_data'
    elif export_type == 'bi':
        df_to_export = session.get('bi_data')
        filename_prefix = 'aggregated_bi_data'
    elif export_type == 'prediction':
        latest_pred = session.get('latest_prediction')
        if latest_pred:
            pred_df = pd.DataFrame([latest_pred['features']])
            pred_df['Predicted_Value'] = latest_pred['prediction']
            df_to_export = pred_df
            filename_prefix = 'prediction'
            
    if df_to_export is None:
        return jsonify({'error': f'No data available for export type: {export_type}'}), 400
        
    # Generate file in memory
    buffer = io.BytesIO()
    
    try:
        if export_format == 'csv':
            df_to_export.to_csv(buffer, index=False)
            buffer.seek(0)
            mimetype = 'text/csv'
            filename = f"{filename_prefix}.csv"
        elif export_format == 'xlsx':
            df_to_export.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename = f"{filename_prefix}.xlsx"
        else:
            return jsonify({'error': 'Invalid format. Use csv or xlsx'}), 400
            
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
    except Exception as e:
        return jsonify({'error': f"Error generating export: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

