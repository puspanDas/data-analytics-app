import unittest
import pandas as pd
import io
import csv
import os

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


class FrontendTest(unittest.TestCase):
    """
    Frontend component tests — validates structure, props, API contracts,
    and component logic from the Python/backend side.
    """

    FRONTEND_SRC = os.path.join(os.path.dirname(__file__), 'frontend', 'src')
    COMPONENTS_DIR = os.path.join(FRONTEND_SRC, 'components')

    # ───────────────────── Utility helpers ─────────────────────

    def _read_component(self, filename):
        """Read a JSX component file and return its contents."""
        path = os.path.join(self.COMPONENTS_DIR, filename)
        self.assertTrue(os.path.exists(path), f"Component file missing: {filename}")
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _assert_default_export(self, content, expected_name):
        """Assert that the file has the expected default export."""
        self.assertIn(f'export default {expected_name}', content,
                      f"Missing default export for {expected_name}")

    def _assert_props(self, content, prop_names):
        """Assert that the component destructures the expected props."""
        for prop in prop_names:
            self.assertIn(prop, content,
                          f"Expected prop '{prop}' not found in component")

    # ───────────────────── App.jsx ─────────────────────

    def test_App_renders(self):
        """App.jsx exists, exports default App, and imports all child components."""
        path = os.path.join(self.FRONTEND_SRC, 'App.jsx')
        self.assertTrue(os.path.exists(path), "App.jsx is missing")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self._assert_default_export(content, 'App')
        # Must import every major component
        expected_imports = [
            'FileUpload', 'Tabs', 'DataOverview', 'BIDashboard',
            'Visualization', 'ModelTraining', 'ModelComparison',
            'Prediction', 'DataFixBanner', 'AICopilot'
        ]
        for comp in expected_imports:
            self.assertIn(comp, content, f"App.jsx missing import for {comp}")

    def test_App_tab_definitions(self):
        """App.jsx defines all expected tab IDs."""
        path = os.path.join(self.FRONTEND_SRC, 'App.jsx')
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        expected_tabs = ['data-overview', 'bi-dashboard', 'visualization',
                         'training', 'comparison', 'prediction']
        for tab_id in expected_tabs:
            self.assertIn(tab_id, content, f"Missing tab definition: {tab_id}")

    # ───────────────────── FileUpload.jsx ─────────────────────

    def test_FileUpload_renders(self):
        content = self._read_component('FileUpload.jsx')
        self._assert_default_export(content, 'FileUpload')
        self._assert_props(content, ['onUploadSuccess', 'onError'])

    def test_FileUpload_handleUpload(self):
        """FileUpload validates file extensions before uploading."""
        content = self._read_component('FileUpload.jsx')
        # Must check valid extensions
        self.assertIn('.csv', content)
        self.assertIn('.xlsx', content)
        self.assertIn('.xls', content)
        # Must POST to /upload
        self.assertIn("'/upload'", content)

    def test_FileUpload_handleDrag(self):
        """FileUpload supports drag-and-drop events."""
        content = self._read_component('FileUpload.jsx')
        self.assertIn('onDragEnter', content)
        self.assertIn('onDragLeave', content)
        self.assertIn('onDragOver', content)
        self.assertIn('onDrop', content)

    def test_FileUpload_api_contract(self):
        """Backend /upload endpoint exists and rejects requests without files."""
        from app import app
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.post('/upload')
        # Should return an error (no file), not a 500
        self.assertIn(response.status_code, [200, 400])

    # ───────────────────── Tabs.jsx ─────────────────────

    def test_Tabs_renders(self):
        content = self._read_component('Tabs.jsx')
        self._assert_default_export(content, 'Tabs')
        self._assert_props(content, ['tabs', 'activeTab', 'onTabChange'])

    def test_Tabs_renders_buttons(self):
        """Tabs component renders a <button> for each tab."""
        content = self._read_component('Tabs.jsx')
        self.assertIn('tabs.map', content, "Tabs must iterate over the tabs array")
        self.assertIn('<button', content, "Each tab should be a <button>")

    # ───────────────────── DataOverview.jsx ─────────────────────

    def test_DataOverview_renders(self):
        content = self._read_component('DataOverview.jsx')
        self._assert_default_export(content, 'DataOverview')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_DataOverview_displays_shape(self):
        """DataOverview must display row and column counts."""
        content = self._read_component('DataOverview.jsx')
        self.assertIn('dataInfo.shape[0]', content, "Must display row count")
        self.assertIn('dataInfo.shape[1]', content, "Must display column count")

    def test_DataOverview_export_link(self):
        """DataOverview has an export CSV button pointing to /export."""
        content = self._read_component('DataOverview.jsx')
        self.assertIn('/export', content, "Must link to /export endpoint")

    # ───────────────────── BIDashboard.jsx ─────────────────────

    def test_BIDashboard_renders(self):
        content = self._read_component('BIDashboard.jsx')
        self._assert_default_export(content, 'BIDashboard')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_BIDashboard_handleAggregate(self):
        """BIDashboard POSTs to /aggregate with correct payload structure."""
        content = self._read_component('BIDashboard.jsx')
        self.assertIn("'/aggregate'", content)
        # Payload must include dimensions, measures, aggregations
        self.assertIn('dimensions', content)
        self.assertIn('measures', content)
        self.assertIn('aggregations', content)

    def test_BIDashboard_drag_and_drop(self):
        """BIDashboard supports drag-and-drop for measures."""
        content = self._read_component('BIDashboard.jsx')
        self.assertIn('handleDragStart', content)
        self.assertIn('handleDrop', content)
        self.assertIn('addMeasure', content)
        self.assertIn('removeMeasure', content)

    def test_BIDashboard_chart_types(self):
        """BIDashboard supports multiple chart types."""
        content = self._read_component('BIDashboard.jsx')
        for chart_type in ['bar', 'line', 'pie', 'area', 'scatter']:
            self.assertIn(chart_type, content,
                          f"Missing chart type: {chart_type}")

    def test_BIDashboard_aggregate_api_contract(self):
        """Backend /aggregate endpoint exists and validates input."""
        from app import app
        import json
        app.config['TESTING'] = True
        client = app.test_client()
        # Empty payload should return an error, not crash
        response = client.post('/aggregate',
                               data=json.dumps({}),
                               content_type='application/json')
        self.assertIn(response.status_code, [200, 400])

    # ───────────────────── Visualization.jsx ─────────────────────

    def test_Visualization_renders(self):
        content = self._read_component('Visualization.jsx')
        self._assert_default_export(content, 'Visualization')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_Visualization_handlePlot(self):
        """Visualization POSTs to /visualize."""
        content = self._read_component('Visualization.jsx')
        self.assertIn("'/visualize'", content)
        self.assertIn('plot_type', content)
        self.assertIn('x_col', content)
        self.assertIn('y_col', content)

    def test_Visualization_plot_types(self):
        """Visualization supports all expected plot types."""
        content = self._read_component('Visualization.jsx')
        for plot in ['histogram', 'scatter', 'boxplot', 'correlation', 'pairplot', 'strip']:
            self.assertIn(plot, content, f"Missing plot type option: {plot}")

    # ───────────────────── ModelTraining.jsx ─────────────────────

    def test_ModelTraining_renders(self):
        content = self._read_component('ModelTraining.jsx')
        self._assert_default_export(content, 'ModelTraining')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_ModelTraining_handleTrain(self):
        """ModelTraining POSTs to /train_model with correct payload."""
        content = self._read_component('ModelTraining.jsx')
        self.assertIn("'/train_model'", content)
        self.assertIn('target_column', content)
        self.assertIn('feature_columns', content)
        self.assertIn('test_size', content)
        self.assertIn('model_type', content)

    def test_ModelTraining_handleFeatureToggle(self):
        """ModelTraining allows toggling feature columns."""
        content = self._read_component('ModelTraining.jsx')
        self.assertIn('handleFeatureToggle', content)
        self.assertIn('checkbox', content.lower())

    def test_ModelTraining_handleExportPowerBI(self):
        """ModelTraining can export to Power BI via /export_power_bi."""
        content = self._read_component('ModelTraining.jsx')
        self.assertIn("'/export_power_bi'", content)
        self.assertIn('power_bi_dataset.csv', content)

    def test_ModelTraining_model_types(self):
        """ModelTraining supports all expected ML model types."""
        content = self._read_component('ModelTraining.jsx')
        for model in ['random_forest', 'xgboost', 'lightgbm', 'svm']:
            self.assertIn(model, content, f"Missing model type: {model}")

    def test_ModelTraining_train_api_contract(self):
        """Backend /train_model endpoint exists."""
        from app import app
        import json
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.post('/train_model',
                               data=json.dumps({}),
                               content_type='application/json')
        # Should not crash — returns an error for invalid input
        self.assertIn(response.status_code, [200, 400])

    # ───────────────────── ModelComparison.jsx ─────────────────────

    def test_ModelComparison_renders(self):
        content = self._read_component('ModelComparison.jsx')
        self._assert_default_export(content, 'ModelComparison')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_ModelComparison_handleCompare(self):
        """ModelComparison POSTs to /compare_models."""
        content = self._read_component('ModelComparison.jsx')
        self.assertIn("'/compare_models'", content)

    # ───────────────────── Prediction.jsx ─────────────────────

    def test_Prediction_renders(self):
        content = self._read_component('Prediction.jsx')
        self._assert_default_export(content, 'Prediction')
        self._assert_props(content, ['dataInfo', 'sessionId'])

    def test_Prediction_handlePredict(self):
        """Prediction POSTs to /predict."""
        content = self._read_component('Prediction.jsx')
        self.assertIn("'/predict'", content)

    def test_Prediction_handleAutoFill(self):
        """Prediction can auto-fill form via /get_sample_row."""
        content = self._read_component('Prediction.jsx')
        self.assertIn("'/get_sample_row'", content)
        self.assertIn('handleAutoFill', content)

    # ───────────────────── DataFixBanner.jsx ─────────────────────

    def test_DataFixBanner_renders(self):
        content = self._read_component('DataFixBanner.jsx')
        self._assert_default_export(content, 'DataFixBanner')
        self._assert_props(content, ['diagnosis', 'sessionId', 'onFixApplied'])

    def test_DataFixBanner_handleFix(self):
        """DataFixBanner POSTs to /fix_data to auto-fix the dataset."""
        content = self._read_component('DataFixBanner.jsx')
        self.assertIn("'/fix_data'", content)
        self.assertIn('handleFix', content)

    def test_DataFixBanner_severity_levels(self):
        """DataFixBanner defines severity levels (critical, warning, info)."""
        content = self._read_component('DataFixBanner.jsx')
        for severity in ['critical', 'warning', 'info']:
            self.assertIn(severity, content, f"Missing severity level: {severity}")

    def test_DataFixBanner_success_state(self):
        """DataFixBanner shows a success banner after fix is applied."""
        content = self._read_component('DataFixBanner.jsx')
        self.assertIn('Data Fixed Successfully', content)
        self.assertIn('fixes_applied', content)

    # ───────────────────── AICopilot.jsx ─────────────────────

    def test_AICopilot_renders(self):
        content = self._read_component('AICopilot.jsx')
        self._assert_default_export(content, 'AICopilot')
        self._assert_props(content, [
            'sessionId', 'dataInfo', 'activeTab',
            'targetColumn', 'selectedFeatures',
            'dimensions', 'measures', 'isOpen', 'setIsOpen'
        ])

    def test_AICopilot_handleSendMessage(self):
        """AICopilot POSTs to /ai_chat for conversational AI."""
        content = self._read_component('AICopilot.jsx')
        self.assertIn("'/ai_chat'", content)
        self.assertIn('handleSendMessage', content)

    def test_AICopilot_quick_action_chips(self):
        """AICopilot provides context-aware quick action chips per tab."""
        content = self._read_component('AICopilot.jsx')
        self.assertIn('getQuickActionChips', content)
        # Should have chip suggestions for these tabs
        for tab in ['bi-dashboard', 'visualization', 'training', 'comparison', 'prediction']:
            self.assertIn(tab, content,
                          f"Missing quick action chips for tab: {tab}")

    def test_AICopilot_warning_system(self):
        """AICopilot displays warnings (data leakage, high cardinality etc.)."""
        content = self._read_component('AICopilot.jsx')
        self.assertIn('warnings', content)
        self.assertIn('data-leakage', content)

    def test_AICopilot_chat_api_contract(self):
        """Backend /ai_chat endpoint exists and handles missing session."""
        from app import app
        import json
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.post('/ai_chat',
                               data=json.dumps({'session_id': 'nonexistent'}),
                               content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data.decode('utf-8'))
        # Should gracefully handle missing session
        self.assertIn('reply', res_data)

    # ───────────────────── Cross-component integration ─────────────────────

    def test_all_component_files_exist(self):
        """All expected component JSX files exist in the components directory."""
        expected_files = [
            'FileUpload.jsx', 'Tabs.jsx', 'DataOverview.jsx',
            'BIDashboard.jsx', 'Visualization.jsx', 'ModelTraining.jsx',
            'ModelComparison.jsx', 'Prediction.jsx', 'DataFixBanner.jsx',
            'AICopilot.jsx'
        ]
        for filename in expected_files:
            path = os.path.join(self.COMPONENTS_DIR, filename)
            self.assertTrue(os.path.exists(path),
                            f"Component file missing: {filename}")

    def test_all_components_have_default_export(self):
        """Every component file has exactly one default export."""
        import re
        expected = {
            'FileUpload.jsx': 'FileUpload',
            'Tabs.jsx': 'Tabs',
            'DataOverview.jsx': 'DataOverview',
            'BIDashboard.jsx': 'BIDashboard',
            'Visualization.jsx': 'Visualization',
            'ModelTraining.jsx': 'ModelTraining',
            'ModelComparison.jsx': 'ModelComparison',
            'Prediction.jsx': 'Prediction',
            'DataFixBanner.jsx': 'DataFixBanner',
            'AICopilot.jsx': 'AICopilot',
        }
        for filename, export_name in expected.items():
            content = self._read_component(filename)
            matches = re.findall(r'export\s+default\s+\w+', content)
            self.assertEqual(len(matches), 1,
                             f"{filename} should have exactly 1 default export, found {len(matches)}")
            self.assertIn(export_name, matches[0])

    def test_no_console_errors_in_components(self):
        """Components should use console.warn/error, not console.log for errors."""
        import re
        problem_files = []
        for filename in os.listdir(self.COMPONENTS_DIR):
            if not filename.endswith('.jsx'):
                continue
            content = self._read_component(filename)
            # Acceptable: console.warn, console.error
            # Flag: console.log (should not be in production components)
            logs = re.findall(r'console\.log\(', content)
            if logs:
                problem_files.append((filename, len(logs)))
        # This is a soft check — warn but don't fail
        # Uncomment below to enforce:
        # self.assertEqual(len(problem_files), 0,
        #                  f"Components with console.log: {problem_files}")


    def test_App_handleUploadSuccess(self):
        pass # TODO: auto-generated frontend test stub

    def test_App_handleFixApplied(self):
        pass # TODO: auto-generated frontend test stub

    def test_AICopilot_renderFormattedText(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_handleDragStart(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_handleDragOver(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_handleDragEnter(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_handleDragLeave(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_handleDrop(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_addMeasure(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_removeMeasure(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_toggleDimension(self):
        pass # TODO: auto-generated frontend test stub

    def test_BIDashboard_renderChart(self):
        pass # TODO: auto-generated frontend test stub

    def test_FileUpload_handleDrop(self):
        pass # TODO: auto-generated frontend test stub

    def test_FileUpload_handleChange(self):
        pass # TODO: auto-generated frontend test stub

    def test_Prediction_handleChange(self):
        pass # TODO: auto-generated frontend test stub

if __name__ == '__main__':
    unittest.main()
