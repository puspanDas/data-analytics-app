import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/upload': 'http://127.0.0.1:5000',
      '/visualize': 'http://127.0.0.1:5000',
      '/train_model': 'http://127.0.0.1:5000',
      '/compare_models': 'http://127.0.0.1:5000',
      '/export': 'http://127.0.0.1:5000',
      '/aggregate': 'http://127.0.0.1:5000',
      '/predict': 'http://127.0.0.1:5000',
      '/feature_info': 'http://127.0.0.1:5000',
      '/get_sample_row': 'http://127.0.0.1:5000',
      '/data_summary': 'http://127.0.0.1:5000',
      '/stats_analysis': 'http://127.0.0.1:5000',
    }
  }
})
