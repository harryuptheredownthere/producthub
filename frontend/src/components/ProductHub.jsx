import React, { useState, useEffect } from 'react';
import { Upload } from 'lucide-react';

export const ProductHub = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [pendingFormData, setPendingFormData] = useState(null);

  useEffect(() => {
    // Check for auth callback responses
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const authSuccess = urlParams.get('auth') === 'success';

    if (error) {
      setMessage(`Authentication failed: ${error}`);
    } else if (authSuccess) {
      setMessage('Authentication successful');
      // If we have pending form data, submit it
      if (pendingFormData) {
        handleUpload(pendingFormData);
        setPendingFormData(null);
      }
    }

    // Clear URL parameters
    if (error || authSuccess) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [pendingFormData]);

  const handleAuth = async () => {
    try {
      console.log('Starting authentication process...');
      const response = await fetch('http://localhost:8080/auth/url', {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (!data.auth_url) {
        throw new Error('No auth URL received');
      }

      // Redirect to Microsoft login
      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Authentication error:', error);
      setMessage(`Failed to start authentication: ${error.message}`);
    }
  };

  const handleUpload = async (formData) => {
    try {
      console.log('Attempting upload...');
      // Log form data for debugging
      for (let [key, value] of formData.entries()) {
        console.log(`Form data - ${key}:`, value);
      }

      const response = await fetch('http://localhost:8080/upload', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Accept': 'application/json'
        },
        body: formData
      });

      console.log('Response status:', response.status);

      if (response.status === 401) {
        console.log('Authentication required, starting auth flow...');
        // Store form data and initiate auth flow
        setPendingFormData(formData);
        await handleAuth();
        return;
      }

      const data = await response.json();
      console.log('Upload response:', data);

      if (!response.ok) {
        throw new Error(data.message || `Upload failed: ${response.status}`);
      }

      setMessage(data.message || 'Upload successful');
      
    } catch (error) {
      console.error('Upload error:', error);
      setMessage(`Error uploading file: ${error.message}`);
      throw error;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const formData = new FormData(e.target);
      await handleUpload(formData);
    } catch (error) {
      console.error('Submission error:', error);
      // Message already set in handleUpload
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container max-w-3xl mx-auto p-4">
      <h1 className="text-3xl font-bold text-center mb-8">UT & UTA Product Hub</h1>

      <div className="p-6 border rounded-lg">
        <h3 className="text-xl font-semibold mb-4">Upload a File</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Brand Name</label>
            <input
              type="text"
              name="brand_name"
              required
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Company</label>
            <select 
              name="company" 
              required
              className="w-full p-2 border rounded"
              defaultValue=""
            >
              <option value="" disabled>Select a company</option>
              <option value="UP THERE">UP THERE</option>
              <option value="UTA">UTA</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Season</label>
            <input
              type="text"
              name="season"
              required
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Upload File</label>
            <input
              type="file"
              name="file"
              required
              accept=".xlsx,.xls"
              className="w-full p-2 border rounded"
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded flex gap-2 items-center justify-center hover:bg-blue-600 disabled:bg-blue-300"
          >
            <Upload className="h-4 w-4" />
            {isLoading ? 'Processing...' : 'Upload'}
          </button>
        </form>

        {message && (
          <div className="mt-4 p-4 border rounded bg-slate-50">
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductHub;