'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import axios from 'axios';
import Header from '../../../components/Header';
import LoadingSpinner from '../../../components/LoadingSpinner';

export default function ContributorDetailPage() {
  const params = useParams();
  const username = decodeURIComponent(params.username);
  
  const [profile, setProfile] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  
  // Sort state
  const [sortBy, setSortBy] = useState('contributions');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Add this state to your component
  const [showDebug, setShowDebug] = useState(false);
  
  // Add this state to your component
  const [debugData, setDebugData] = useState(null);
  
  useEffect(() => {
    fetchContributorData();
  }, [username, page, pageSize, sortBy, sortOrder]);
  
  const fetchContributorData = async () => {
    try {
      setLoading(true);
      
      const params = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      
      console.log(`Fetching data for contributor: ${username} with params:`, params);
      
      const response = await axios.get(`/api/contributors/${encodeURIComponent(username)}`, { params });
      console.log('Contributor API response:', response.data);
      
      setProfile(response.data.profile);
      setRepositories(response.data.repositories.items);
      setTotalPages(response.data.repositories.total_pages);
      setTotalItems(response.data.repositories.total);
      
      setLoading(false);
    } catch (err) {
      console.error('Error fetching contributor data:', err);
      setError('Failed to load contributor data. Please try again later.');
      setLoading(false);
    }
  };
  
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > totalPages) return;
    setPage(newPage);
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
  
  // Pagination component
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
              Showing <span className="font-medium">{repositories.length > 0 ? (page - 1) * pageSize + 1 : 0}</span> to{' '}
              <span className="font-medium">{Math.min(page * pageSize, totalItems)}</span> of{' '}
              <span className="font-medium">{totalItems}</span> repositories
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
  
  // Add this function to your component
  const toggleDebug = () => {
    setShowDebug(!showDebug);
  };
  
  // Add this function to your component
  const fetchDebugData = async () => {
    try {
      const response = await axios.get(`/api/debug/contributor/${encodeURIComponent(username)}`);
      console.log('Debug data:', response.data);
      
      // Update the debug panel with the raw data
      setDebugData(response.data);
    } catch (err) {
      console.error('Error fetching debug data:', err);
    }
  };
  
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
          <div className="text-center">
            <a href="/" className="text-blue-600 hover:text-blue-800">Return to Dashboard</a>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">Contributor: {username}</h1>
          <button 
            onClick={() => {
              toggleDebug();
              if (!debugData) {
                fetchDebugData();
              }
            }}
            className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
          >
            Debug
          </button>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : (
          <>
            {profile && (
              <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
                <div className="px-4 py-5 sm:px-6 flex items-center">
                  <div className="flex-shrink-0 h-16 w-16 mr-4">
                    <img 
                      className="h-16 w-16 rounded-full" 
                      src={`https://github.com/${username}.png`} 
                      alt="" 
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png";
                      }}
                    />
                  </div>
                  <div>
                    <h3 className="text-lg leading-6 font-medium text-gray-900">{profile.name || username}</h3>
                    {profile.bio && <p className="mt-1 max-w-2xl text-sm text-gray-500">{profile.bio}</p>}
                  </div>
                </div>
                <div className="border-t border-gray-200">
                  <dl>
                    <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Location</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{profile.location || 'Not specified'}</dd>
                    </div>
                    <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Email</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                        {profile.email ? (
                          <a href={`mailto:${profile.email}`} className="text-blue-600 hover:text-blue-800">
                            {profile.email}
                          </a>
                        ) : (
                          'Not specified'
                        )}
                      </dd>
                    </div>
                    <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Company</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{profile.company || 'Not specified'}</dd>
                    </div>
                    <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Blog</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                        {profile.blog ? (
                          <a 
                            href={profile.blog.startsWith('http') ? profile.blog : `https://${profile.blog}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {profile.blog}
                          </a>
                        ) : (
                          'Not specified'
                        )}
                      </dd>
                    </div>
                    <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Twitter</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                        {profile.twitter_username ? (
                          <a 
                            href={`https://twitter.com/${profile.twitter_username}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            @{profile.twitter_username}
                          </a>
                        ) : (
                          'Not specified'
                        )}
                      </dd>
                    </div>
                    <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Followers</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatNumber(profile.followers)}</dd>
                    </div>
                    <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Public Repositories</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatNumber(profile.public_repos)}</dd>
                    </div>
                    <div className="bg-white px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">Total Contributions</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{formatNumber(profile.total_contributions)}</dd>
                    </div>
                    <div className="bg-gray-50 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                      <dt className="text-sm font-medium text-gray-500">GitHub Member Since</dt>
                      <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                        {profile.created_at ? new Date(profile.created_at).toLocaleDateString() : 'Unknown'}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>
            )}
            
            <div className="mb-4">
              <h2 className="text-xl font-semibold mb-4">Contributed Repositories</h2>
              
              {repositories && repositories.length > 0 ? (
                <>
                  <div className="overflow-x-auto bg-white shadow rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSortChange('name')}
                          >
                            Repository {getSortIndicator('name')}
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                            onClick={() => handleSortChange('contributions')}
                          >
                            Contributions {getSortIndicator('contributions')}
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            Language
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            Stars
                          </th>
                          <th 
                            scope="col" 
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            Forks
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {repositories.map((repo, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="ml-4">
                                  <a 
                                    href={`/repositories/${encodeURIComponent(repo.repository)}`}
                                    className="text-sm font-medium text-gray-900 hover:text-blue-600"
                                  >
                                    {repo.repository}
                                  </a>
                                  <div className="text-sm text-gray-500 truncate max-w-md" title={repo.description || ''}>
                                    {repo.description || ''}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatNumber(repo.contributions)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {repo.language || 'Not specified'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <div className="flex items-center">
                                <svg className="w-4 h-4 mr-1 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                                {formatNumber(repo.stars)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              <div className="flex items-center">
                                <svg className="w-4 h-4 mr-1 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M7.707 3.293a1 1 0 010 1.414L5.414 7H11a7 7 0 017 7v2a1 1 0 11-2 0v-2a5 5 0 00-5-5H5.414l2.293 2.293a1 1 0 11-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                                {formatNumber(repo.forks)}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {totalPages > 1 && <Pagination />}
                </>
              ) : (
                <div className="bg-white p-6 rounded-lg shadow text-center">
                  <p className="text-gray-500">No repositories found for this contributor.</p>
                  <div className="mt-4 text-sm text-gray-400">
                    This could be because the contributor data is incomplete or the contributor hasn't made any contributions to the repositories in our dataset.
                  </div>
                </div>
              )}
            </div>
          </>
        )}
        
        {showDebug && (
          <div className="mt-8 p-4 bg-gray-100 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Debug Information</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <h4 className="text-md font-medium mb-1">Profile Data:</h4>
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
                  {JSON.stringify(profile, null, 2)}
                </pre>
              </div>
              <div>
                <h4 className="text-md font-medium mb-1">Repository Data:</h4>
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
                  {JSON.stringify(repositories, null, 2)}
                </pre>
              </div>
            </div>
            
            {debugData && (
              <div>
                <h4 className="text-md font-medium mb-1">Raw Contributor Data:</h4>
                <div className="text-xs mb-2">
                  Found {debugData.entries_count} entries for {username}
                </div>
                <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
                  {JSON.stringify(debugData.entries, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 