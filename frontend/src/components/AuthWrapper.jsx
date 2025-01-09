import React, { useState, useEffect } from 'react';
import { LogIn } from 'lucide-react';

const AuthWrapper = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check for auth callback responses
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const authSuccess = urlParams.get('auth') === 'success';

    if (error) {
      setError(`Authentication failed: ${error}`);
      setIsLoading(false);
    } else if (authSuccess) {
      setIsAuthenticated(true);
      setIsLoading(false);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    } else {
      checkAuthStatus();
    }
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('http://localhost:8080/auth/status', {
        credentials: 'include',
      });
      
      const data = await response.json();
      setIsAuthenticated(data.isAuthenticated);
    } catch (error) {
      console.error('Auth check failed:', error);
      setError('Failed to check authentication status');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuth = async () => {
    try {
      setError(null);
      setIsLoading(true);
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

      window.location.href = data.auth_url;
    } catch (error) {
      console.error('Authentication error:', error);
      setError(`Failed to start authentication: ${error.message}`);
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50">
        <div className="p-8 bg-white rounded-lg shadow-md max-w-md w-full">
          <h2 className="text-2xl font-bold text-center mb-6">Welcome to Product Hub</h2>
          
          <p className="text-gray-600 mb-6 text-center">
            Please sign in with your Microsoft account to continue.
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded text-red-600">
              {error}
            </div>
          )}

          <button
            onClick={handleAuth}
            disabled={isLoading}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded flex gap-2 items-center justify-center hover:bg-blue-600 disabled:bg-blue-300"
          >
            <LogIn className="h-4 w-4" />
            Sign in with Microsoft
          </button>
        </div>
      </div>
    );
  }

  return children;
};

export default AuthWrapper;