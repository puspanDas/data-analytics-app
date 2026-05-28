import unittest
import pandas as pd
import io
import csv

class MasterTest(unittest.TestCase):
    
    def test_csv_reader_quotes(self):
        df_excel = pd.DataFrame({
            'Month,Product_ID,Company': [
                'Jan-24,P001,"Apple, Inc."',
                'Feb-24,P002,"Sony Corp."'
            ]
        })
        detected_sep = ','
        lines = [str(df_excel.columns[0])] + df_excel.iloc[:, 0].astype(str).tolist()
        reader = csv.reader(lines, delimiter=detected_sep)
        parsed_data = list(reader)
        df_fixed = pd.DataFrame(parsed_data[1:], columns=parsed_data[0])
        
        self.assertEqual(df_fixed.shape, (2, 3))
        self.assertIn("Company", df_fixed.columns)
        
    def test_quotes_none(self):
        data = b'"Month,Product_ID,Product_Name"\n"Jan-24,P001,Quantum X1"\n'
        df2 = pd.read_csv(io.BytesIO(data), quoting=csv.QUOTE_NONE)
        self.assertEqual(df2.shape, (1, 3))
        
    def test_universal_fix(self):
        df_excel = pd.DataFrame({
            'Month,Product_ID,Product_Name': [
                'Jan-24,P001,Quantum X1',
                'Feb-24,P002,Galaxy S24'
            ]
        })
        detected_sep = ','
        csv_buffer = io.StringIO()
        df_excel.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        df_fixed = pd.read_csv(csv_buffer, sep=detected_sep, engine='python')
        self.assertEqual(df_fixed.shape, (2, 1))

    def test_clean_for_json(self):
        pass # TODO: auto-generated test stub

    def test_handle_file_too_large(self):
        pass # TODO: auto-generated test stub

    def test_get_session(self):
        pass # TODO: auto-generated test stub

    def test_allowed_file(self):
        pass # TODO: auto-generated test stub

    def test_create_visualization(self):
        pass # TODO: auto-generated test stub

    def test_index(self):
        pass # TODO: auto-generated test stub

    def test_favicon(self):
        pass # TODO: auto-generated test stub

    def test_test(self):
        pass # TODO: auto-generated test stub

    def test_test_server(self):
        pass # TODO: auto-generated test stub

    def test_reduce_mem_usage(self):
        pass # TODO: auto-generated test stub

    def test_upload_file(self):
        pass # TODO: auto-generated test stub

    def test_visualize(self):
        pass # TODO: auto-generated test stub

    def test_train_model(self):
        pass # TODO: auto-generated test stub

    def test_compare_models(self):
        pass # TODO: auto-generated test stub

    def test_predict(self):
        pass # TODO: auto-generated test stub

    def test_feature_info(self):
        pass # TODO: auto-generated test stub

    def test_get_sample_row(self):
        pass # TODO: auto-generated test stub

    def test_data_summary(self):
        pass # TODO: auto-generated test stub

    def test_stats_analysis(self):
        pass # TODO: auto-generated test stub

    def test_aggregate_data(self):
        from app import app, SESSIONS
        import json
        import time
        
        # Configure app for testing
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Setup mock session with a dataframe that has dimensions only (no numeric columns)
        session_id = 'test-session-123'
        df = pd.DataFrame({
            'Category': ['Electronics', 'Electronics', 'Clothing', 'Clothing', 'Clothing'],
            'Product': ['Phone', 'Laptop', 'Shirt', 'Jeans', 'Shirt'],
            'Status': ['In Stock', 'Out of Stock', 'In Stock', 'In Stock', 'Out of Stock']
        })
        
        SESSIONS[session_id] = {
            'data': df,
            'last_accessed': time.time()
        }
        
        # Test aggregating Categorical columns as measures with allowed aggregations (count, nunique)
        payload = {
            'session_id': session_id,
            'dimensions': ['Category'],
            'measures': ['Product', 'Status'],
            'aggregations': {
                'Product': 'count',
                'Status': 'nunique'
            }
        }
        
        response = client.post('/aggregate', 
                               data=json.dumps(payload),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        self.assertTrue(res_data['success'])
        self.assertEqual(len(res_data['data']), 2) # Electronics and Clothing
        
        # Verify Electronics values: Product count=2, Status nunique=2
        electronics = [row for row in res_data['data'] if row['Category'] == 'Electronics'][0]
        self.assertEqual(electronics['Product'], 2)
        self.assertEqual(electronics['Status'], 2)
        
        # Verify Clothing values: Product count=3, Status nunique=2
        clothing = [row for row in res_data['data'] if row['Category'] == 'Clothing'][0]
        self.assertEqual(clothing['Product'], 3)
        self.assertEqual(clothing['Status'], 2)

    def test_ai_chat(self):
        from app import app, SESSIONS
        import json
        import time
        
        app.config['TESTING'] = True
        client = app.test_client()
        
        session_id = 'test-session-copilot'
        df = pd.DataFrame({
            'Category': ['Electronics' if i % 2 == 0 else 'Clothing' for i in range(100)],
            'Sales': [float(i * 10) for i in range(100)],
            'CustomerID': [f'C{100+i}' for i in range(100)] # 100 unique values
        })
        
        # Test case 1: No session / No data loaded
        response = client.post('/ai_chat',
                               data=json.dumps({'session_id': 'invalid-session'}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        self.assertTrue("haven't uploaded a dataset yet" in res_data['reply'])
        
        # Setup mock session
        SESSIONS[session_id] = {
            'data': df,
            'last_accessed': time.time()
        }
        
        # Test case 2: Data Leakage Detection
        payload = {
            'session_id': session_id,
            'active_tab': 'training',
            'message': 'please check my features',
            'target_column': 'Sales',
            'selected_features': ['Category', 'Sales'] # Leakage!
        }
        response = client.post('/ai_chat',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(res_data['warnings']), 1)
        self.assertEqual(res_data['warnings'][0]['type'], 'data-leakage')
        
        # Test case 3: High Cardinality Detection
        payload = {
            'session_id': session_id,
            'active_tab': 'training',
            'message': 'check high cardinality',
            'target_column': 'Sales',
            'selected_features': ['CustomerID'] # Cardinality: 3 unique out of 3 rows (100% unique)
        }
        response = client.post('/ai_chat',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        # Should flag CustomerID as high cardinality
        self.assertTrue(any(w['type'] == 'high-cardinality' for w in res_data['warnings']))
        
        # Test case 4: Natural Language Query matching
        payload = {
            'session_id': session_id,
            'active_tab': 'bi-dashboard',
            'message': 'suggest a dashboard setup'
        }
        response = client.post('/ai_chat',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        self.assertTrue("BI Dashboard Guide" in res_data['reply'])

    def test_export_power_bi(self):
        pass # TODO: auto-generated test stub

    def test_export_data(self):
        pass # TODO: auto-generated test stub

    def test_fix_data(self):
        pass # TODO: auto-generated test stub

    def test_diagnose_data(self):
        pass # TODO: auto-generated test stub

    def test_apply_data_fixes(self):
        pass # TODO: auto-generated test stub

    def test_prepare_power_bi_dataset(self):
        pass # TODO: auto-generated test stub

    def test_ping_server(self):
        pass # TODO: auto-generated test stub

if __name__ == '__main__':
    unittest.main()
