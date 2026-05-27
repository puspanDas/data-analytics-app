import pandas as pd
import io
import logging

logger = logging.getLogger('power_bi')
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler('power_bi.log', encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
logger.propagate = False

def prepare_power_bi_dataset(session):
    """
    Extracts and prepares the session data for direct ingestion into Power BI.
    """
    try:
        if not session or 'data' not in session or session['data'] is None:
            raise ValueError("No data found in session.")
            
        df = session['data'].copy()
        
        # Ensure all columns are strings or basic numeric types for Power BI compatibility
        # Power BI sometimes struggles with complex nested JSON or Python objects in CSVs
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
                
        # Write to in-memory CSV string
        output = io.StringIO()
        df.to_csv(output, index=False)
        csv_data = output.getvalue()
        
        logger.info(f"Successfully generated Power BI dataset: {df.shape[0]} rows, {df.shape[1]} columns")
        
        return csv_data
        
    except Exception as e:
        logger.error(f"Error preparing Power BI dataset: {str(e)}")
        raise
