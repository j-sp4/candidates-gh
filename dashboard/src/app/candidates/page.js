'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../../components/Header';
import LoadingSpinner from '../../components/LoadingSpinner';
import { getCachedData } from '../../lib/dataCache';

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState([]);
  const [languages, setLanguages] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filter and sort state
  const [sortBy, setSortBy] = useState('contributions');
  const [sortOrder, setSortOrder] = useState('desc');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [minFollowers, setMinFollowers] = useState('');
  const [minContributions, setMinContributions] = useState('');
  
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebug, setShowDebug] = useState(false);
  const [contributorDebug, setContributorDebug] = useState(null);
  const [repoDetails, setRepoDetails] = useState({});
  
  // Add these states to your component
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch languages with caching
        const languagesData = await getCachedData('candidateLanguages', 
          () => axios.get('/api/candidates/languages').then(res => res.data)
        );
        setLanguages(languagesData);
        
        // Fetch locations with caching
        const locationsData = await getCachedData('candidateLocations', 
          () => axios.get('/api/candidates/locations').then(res => res.data)
        );
        setLocations(locationsData);
        
        // Fetch candidates with current filters
        await fetchCandidates();
        
      } catch (err) {
        console.error('Error fetching candidate data:', err);
        setError('Failed to load candidate data. Please make sure the API server is running.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);
  
  const fetchCandidates = async (newPage = page) => {
    try {
      setLoading(true);
      
      // Build query parameters
      const params = {
        sort_by: sortBy,
        sort_order: sortOrder,
        page: newPage,
        page_size: pageSize
      };
      
      if (selectedLocation) params.location = selectedLocation;
      if (selectedLanguage) params.language = selectedLanguage;
      if (minFollowers) params.min_followers = minFollowers;
      if (minContributions) params.min_contributions = minContributions;
      
      try {
        // Try the full endpoint first
        const response = await axios.get('/api/candidates', { params });
        setCandidates(response.data.items);
        setTotalPages(response.data.total_pages);
        setTotalItems(response.data.total);
        setPage(response.data.page);
      } catch (err) {
        console.error('Error with main endpoint, trying simple endpoint:', err);
        
        // If that fails, try the simple endpoint
        const simpleParams = {
          sort_by: sortBy,
          sort_order: sortOrder,
          page: newPage,
          page_size: pageSize
        };
        
        if (minFollowers) simpleParams.min_followers = minFollowers;
        if (minContributions) simpleParams.min_contributions = minContributions;
        
        const simpleResponse = await axios.get('/api/candidates/simple', { params: simpleParams });
        setCandidates(simpleResponse.data.items);
        setTotalPages(simpleResponse.data.total_pages);
        setTotalItems(simpleResponse.data.total);
        setPage(simpleResponse.data.page);
        
        // Show a warning that some filters are disabled
        if (selectedLocation || selectedLanguage) {
          setError('Some filters are disabled due to data loading issues. Location and language filtering are not available.');
        }
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching candidates:', err);
      setError('Failed to load candidates with the selected filters.');
      setLoading(false);
    }
  };
  
  const handleFilterChange = () => {
    fetchCandidates();
  };
  
  const handleSortChange = (field) => {
    if (sortBy === field) {
      // Toggle sort order if clicking the same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to descending for new sort field
      setSortBy(field);
      setSortOrder('desc');
    }
    fetchCandidates();
  };
  
  const getSortIndicator = (field) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  const formatNumber = (value) => {
    if (value === undefined || value === null) return 'N/A';
    if (typeof value === 'number') return value.toLocaleString();
    if (typeof value === 'string' && !isNaN(value)) return parseInt(value).toLocaleString();
    return value;
  };

  const fetchDebugInfo = async () => {
    try {
      const response = await axios.get('/api/debug/file-structure');
      setDebugInfo(response.data);
      setShowDebug(true);
    } catch (err) {
      console.error('Error fetching debug info:', err);
      setError('Failed to load debug information.');
    }
  };

  const fetchContributorDebug = async () => {
    try {
      const response = await axios.get('/api/debug/contributors');
      setContributorDebug(response.data);
      setShowDebug(true);
    } catch (err) {
      console.error('Error fetching contributor debug info:', err);
      setError('Failed to load contributor debug information.');
    }
  };

  const getContributions = (candidate) => {
    // Try different possible field names for contributions
    if (typeof candidate.total_contributions !== 'undefined' && candidate.total_contributions !== null) {
      return candidate.total_contributions;
    }
    
    // Log the candidate object to see what fields are available
    console.log('Candidate with no contributions:', candidate);
    
    return 0;
  };

  const getRepositoryStars = (candidate) => {
    if (typeof candidate.repository_stars !== 'undefined' && candidate.repository_stars !== null) {
      return candidate.repository_stars;
    }
    return 0;
  };

  const fetchRepositoryDetails = async (repoName) => {
    if (repoDetails[repoName]) return; // Already fetched
    
    try {
      const response = await axios.get(`/api/repositories/${encodeURIComponent(repoName)}`);
      setRepoDetails(prev => ({
        ...prev,
        [repoName]: response.data
      }));
    } catch (err) {
      console.error(`Error fetching details for ${repoName}:`, err);
    }
  };

  // Add a function to handle page changes
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages) return;
    setPage(newPage);
    fetchCandidates(newPage);
  };

  // Add a pagination component at the bottom of the table
  const Pagination = () => {
    const pageNumbers = [];
    const maxPageButtons = 5;
    
    let startPage = Math.max(1, page - Math.floor(maxPageButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);
    
    if (endPage - startPage + 1 < maxPageButtons) {
      startPage = Math.max(1, endPage - maxPageButtons + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }
    
    return (
      <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200 sm:px-6">
        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Showing <span className="font-medium">{candidates.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to{' '}
              <span className="font-medium">{Math.min(page * pageSize, totalItems)}</span> of{' '}
              <span className="font-medium">{totalItems}</span> results
            </p>
          </div>
          <div>
            <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
                className={`relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium ${
                  page === 1 ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'
                }`}
              >
                <span className="sr-only">Previous</span>
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              
              {startPage > 1 && (
                <>
                  <button
                    onClick={() => handlePageChange(1)}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    1
                  </button>
                  {startPage > 2 && (
                    <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                      ...
                    </span>
                  )}
                </>
              )}
              
              {pageNumbers.map(number => (
                <button
                  key={number}
                  onClick={() => handlePageChange(number)}
                  className={`relative inline-flex items-center px-4 py-2 border ${
                    page === number
                      ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                      : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  } text-sm font-medium`}
                >
                  {number}
                </button>
              ))}
              
              {endPage < totalPages && (
                <>
                  {endPage < totalPages - 1 && (
                    <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                      ...
                    </span>
                  )}
                  <button
                    onClick={() => handlePageChange(totalPages)}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {totalPages}
                  </button>
                </>
              )}
              
              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages}
                className={`relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium ${
                  page === totalPages ? 'text-gray-300 cursor-not-allowed' : 'text-gray-500 hover:bg-gray-50'
                }`}
              >
                <span className="sr-only">Next</span>
                <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </nav>
          </div>
        </div>
      </div>
    );
  };

  if (error) {
    return (
      <div className="min-h-screen">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center p-8">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
            <p className="text-gray-700 mb-6">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="btn btn-primary"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Candidate Search</h1>
        
        {/* Filters */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">Any Location</option>
                {locations.slice(0, 20).map((location, index) => (
                  <option key={index} value={location.name}>
                    {location.name} ({location.count})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Programming Language
              </label>
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">Any Language</option>
                {languages.slice(0, 20).map((language, index) => (
                  <option key={index} value={language.name}>
                    {language.name} ({language.count})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min. Followers
              </label>
              <input
                type="number"
                value={minFollowers}
                onChange={(e) => setMinFollowers(e.target.value)}
                placeholder="Any"
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Min. Contributions
              </label>
              <input
                type="number"
                value={minContributions}
                onChange={(e) => setMinContributions(e.target.value)}
                placeholder="Any"
                className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <div className="mt-4">
            <button
              onClick={handleFilterChange}
              className="btn btn-primary"
            >
              Apply Filters
            </button>
          </div>
        </div>
        
        {/* Results */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Candidates</h2>
          
          {loading ? (
            <div className="py-10 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading candidates...</p>
            </div>
          ) : candidates.length === 0 ? (
            <div className="py-10 text-center text-gray-500">
              No candidates found matching your criteria.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Candidate
                    </th>
                    <th 
                      scope="col" 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                      onClick={() => handleSortChange('total_contributions')}
                    >
                      Contributions {getSortIndicator('total_contributions')}
                    </th>
                    <th 
                      scope="col" 
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                      onClick={() => handleSortChange('followers')}
                    >
                      Followers {getSortIndicator('followers')}
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Repository
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {candidates.map((candidate, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <img 
                              className="h-10 w-10 rounded-full" 
                              src={`https://github.com/${candidate.username}.png`} 
                              alt="" 
                              onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png";
                              }}
                            />
                          </div>
                          <div className="ml-4">
                            <a 
                              href={`/contributors/${candidate.username}`}
                              className="text-sm font-medium text-gray-900 hover:text-blue-600"
                            >
                              {candidate.username}
                            </a>
                            <div className="text-sm text-gray-500">{candidate.name || ''}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">
                          {formatNumber(getContributions(candidate))}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          c: {candidate.total_contributions || 'null'}, 
                          rc: {candidate.repository_contributions || 'null'}, 
                          tc: {candidate.total_contributions || 'null'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatNumber(candidate.followers)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {candidate.location || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <a 
                            href={`/repositories/${encodeURIComponent(candidate.repository)}`}
                            className="hover:text-blue-600"
                            onMouseEnter={() => fetchRepositoryDetails(candidate.repository)}
                          >
                            {candidate.repository}
                          </a>
                        </div>
                        <div className="text-xs text-gray-500 flex items-center mt-1">
                          <svg className="w-3 h-3 mr-1 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          {formatNumber(getRepositoryStars(candidate) || 
                            (repoDetails[candidate.repository]?.stargazers_count || 0))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="mt-4">
          <button 
            onClick={fetchDebugInfo}
            className="ml-2 px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
          >
            Debug
          </button>
          <button 
            onClick={fetchContributorDebug}
            className="ml-2 px-3 py-1 bg-blue-200 text-blue-700 rounded text-sm hover:bg-blue-300"
          >
            Debug Contributors
          </button>
        </div>

        {/* Add the Pagination component after the table */}
        {!loading && candidates.length > 0 && <Pagination />}
      </div>

      {showDebug && (debugInfo || contributorDebug) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Debug Information</h3>
              <button 
                onClick={() => {
                  setShowDebug(false);
                  setContributorDebug(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            {contributorDebug && (
              <div className="mb-6 border p-4 rounded">
                <h4 className="font-medium mb-2">Contributor Debug</h4>
                <p className="text-sm text-gray-600 mb-2">Path: {contributorDebug.file_path}</p>
                
                <div className="mb-4">
                  <h5 className="text-sm font-medium">Headers:</h5>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                    {JSON.stringify(contributorDebug.headers, null, 2)}
                  </pre>
                </div>
                
                <div className="mb-4">
                  <h5 className="text-sm font-medium">Contribution Column Indices:</h5>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                    {JSON.stringify(contributorDebug.contribution_column_indices, null, 2)}
                  </pre>
                </div>
                
                <div className="mb-4">
                  <h5 className="text-sm font-medium">Sample Rows (Raw):</h5>
                  <div className="overflow-x-auto">
                    <table className="text-xs border-collapse">
                      <thead>
                        <tr>
                          {contributorDebug.headers.map((header, i) => (
                            <th key={i} className="border border-gray-300 p-1 bg-gray-100">
                              {header} ({i})
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {contributorDebug.sample_rows.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {row.map((cell, cellIndex) => (
                              <td 
                                key={cellIndex} 
                                className={`border border-gray-300 p-1 ${
                                  contributorDebug.contribution_column_indices.includes(cellIndex) 
                                    ? 'bg-yellow-100' 
                                    : ''
                                }`}
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div>
                  <h5 className="text-sm font-medium">Processed Data:</h5>
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                    {JSON.stringify(contributorDebug.processed_data, null, 2)}
                  </pre>
                </div>
              </div>
            )}
            
            {debugInfo && (
              <div className="space-y-4">
                {Object.entries(debugInfo).map(([fileType, info]) => (
                  <div key={fileType} className="border p-4 rounded">
                    <h4 className="font-medium mb-2">{fileType}</h4>
                    <p className="text-sm text-gray-600 mb-2">Path: {info.path}</p>
                    {info.error ? (
                      <p className="text-red-500">{info.error}</p>
                    ) : (
                      <>
                        <div className="mb-2">
                          <h5 className="text-sm font-medium">Headers:</h5>
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(info.headers, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <h5 className="text-sm font-medium">Sample Row:</h5>
                          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                            {JSON.stringify(info.sample_row, null, 2)}
                          </pre>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 