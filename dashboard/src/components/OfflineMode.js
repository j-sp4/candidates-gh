'use client';

import { useState, useEffect } from 'react';

export default function OfflineMode({ children }) {
  const [isOnline, setIsOnline] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Check connection status
  const checkConnection = async () => {
    try {
      const response = await fetch('/api/health', { 
        method: 'HEAD',
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' }
      });
      
      if (response.ok) {
        setIsOnline(true);
        setLastUpdated(new Date());
        return true;
      } else {
        setIsOnline(false);
        return false;
      }
    } catch (error) {
      setIsOnline(false);
      return false;
    }
  };

  // Retry connection
  const handleRetry = async () => {
    setRetryCount(prev => prev + 1);
    const success = await checkConnection();
    if (!success && retryCount < 3) {
      // Wait longer between retries
      setTimeout(() => handleRetry(), 5000 * (retryCount + 1));
    }
  };

  // Check connection on mount and periodically
  useEffect(() => {
    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(() => {
      checkConnection();
    }, 30000);
    
    // Handle online/offline events
    const handleOnline = () => {
      checkConnection();
    };
    
    const handleOffline = () => {
      setIsOnline(false);
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (!isOnline) {
    return (
      <div className="fixed inset-0 bg-gray-100 flex items-center justify-center z-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <div className="text-center">
            <svg className="w-16 h-16 text-yellow-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Connection Lost</h2>
            <p className="text-gray-600 mb-6">
              We can't connect to the dashboard API. This could be due to:
            </p>
            
            <ul className="text-left text-gray-600 mb-6 space-y-2">
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>Your internet connection is offline</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>The dashboard API server is not running</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">•</span>
                <span>There's a temporary network issue</span>
              </li>
            </ul>
            
            <div className="space-y-4">
              <button
                onClick={handleRetry}
                className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Retry Connection
              </button>
              
              {lastUpdated && (
                <p className="text-sm text-gray-500">
                  Last connected: {lastUpdated.toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return children;
} 