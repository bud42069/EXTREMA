import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        toast.error('Please select a CSV file');
        return;
      }
      setFile(selectedFile);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select a file first');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    // Show info toast for large files
    toast.info('⏳ Processing... Large files may take 1-3 minutes', {
      autoClose: false,
      position: 'top-center'
    });

    try {
      const response = await axios.post(`${API}/data/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 180000, // 3 minutes timeout
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });

      toast.dismiss(); // Dismiss the processing toast
      toast.success(`✅ Uploaded ${response.data.rows} rows successfully!`, {
        position: 'top-right'
      });
      setUploadResult(response.data);
      
      // Navigate to analysis page after success
      setTimeout(() => navigate('/analysis'), 2000);
    } catch (error) {
      toast.dismiss(); // Dismiss the processing toast
      console.error('Upload error:', error);
      
      let errorMsg = 'Failed to upload dataset';
      if (error.code === 'ECONNABORTED') {
        errorMsg = '⏱️ Upload timed out. File may be too large (>20K rows). Try splitting the file.';
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      }
      
      toast.error(errorMsg, { autoClose: 8000 });
    } finally {
      setUploading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-white mb-2">Upload Data</h1>
        <p className="text-gray-400">Upload your SOLUSDT 5-minute OHLCV CSV file for analysis</p>
      </div>

      {/* Upload Card */}
      <div className="bg-gray-900 rounded-lg p-8 mb-6">
        <div className="border-2 border-dashed border-gray-700 rounded-lg p-12 text-center hover:border-blue-500 transition-colors">
          <div className="text-6xl mb-4">📁</div>
          
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          
          {!file ? (
            <div>
              <label
                htmlFor="file-upload"
                className="cursor-pointer bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-block"
              >
                Select CSV File
              </label>
              <p className="text-gray-400 mt-4 text-sm">or drag and drop your file here</p>
            </div>
          ) : (
            <div>
              <p className="text-white font-semibold mb-2">{file.name}</p>
              <p className="text-gray-400 text-sm mb-4">{(file.size / 1024).toFixed(2)} KB</p>
              <div className="space-x-3">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Uploading...' : 'Upload & Parse'}
                </button>
                <label
                  htmlFor="file-upload"
                  className="bg-gray-700 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors cursor-pointer inline-block"
                >
                  Change File
                </label>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Result */}
      {uploadResult && (
        <div className="bg-gray-900 rounded-lg p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Upload Successful!</h2>
            <span className="text-4xl">✅</span>
          </div>
          
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Total Bars</p>
              <p className="text-2xl font-bold text-white">{uploadResult.total_bars?.toLocaleString()}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Dataset ID</p>
              <p className="text-sm font-mono text-blue-400">{uploadResult.dataset_id}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Start Time</p>
              <p className="text-sm text-white">{formatTimestamp(uploadResult.start_time)}</p>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">End Time</p>
              <p className="text-sm text-white">{formatTimestamp(uploadResult.end_time)}</p>
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => navigate('/analysis', { state: { datasetId: uploadResult.dataset_id } })}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Analyze This Dataset →
            </button>
          </div>
        </div>
      )}

      {/* Requirements */}
      <div className="bg-gray-900 rounded-lg p-8">
        <h2 className="text-xl font-bold text-white mb-4">CSV Format Requirements</h2>
        <div className="space-y-3 text-gray-300 text-sm">
          <p>Your CSV file must contain the following columns:</p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">time</span> - Unix timestamp (seconds)</li>
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">open</span> - Opening price</li>
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">high</span> - Highest price</li>
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">low</span> - Lowest price</li>
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">close</span> - Closing price</li>
            <li><span className="font-mono bg-gray-800 px-2 py-1 rounded">Volume</span> - Trading volume</li>
          </ul>
          <p className="mt-4 text-gray-400">Example:</p>
          <pre className="bg-gray-800 p-4 rounded-lg overflow-x-auto text-xs">
time,open,high,low,close,Volume
1754870400,182.72,182.76,182.34,182.37,2443.676
1754870700,182.38,182.43,181.97,182.01,1260.567
          </pre>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;