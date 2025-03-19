'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../components/Header';
import StatCard from '../components/StatCard';
import LanguageChart from '../components/LanguageChart';
import TopicCloud from '../components/TopicCloud';
import RepositoryTable from '../components/RepositoryTable';
import ContributorTable from '../components/ContributorTable';
import LoadingSpinner from '../components/LoadingSpinner';
import MultiRepoContributors from '../components/MultiRepoContributors';
import GeographicDistribution from '../components/GeographicDistribution';
import ActivityTimeline from '../components/ActivityTimeline';
import OfflineMode from '../components/OfflineMode';
import { getCachedData } from '../lib/dataCache';

export default function Home() {
  const [stats, setStats] = useState(null);
  const [extendedStats, setExtendedStats] = useState(null);
  const [repositories, setRepositories] = useState([]);
  const [contributors, setContributors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch dashboard stats with caching
        const statsData = await getCachedData('dashboardStats', 
          () => axios.get('/api/stats').then(res => res.data)
        );
        setStats(statsData);
        
        // Fetch extended stats with caching
        const extendedStatsData = await getCachedData('extendedStats', 
          () => axios.get('/api/stats/extended').then(res => res.data)
        );
        setExtendedStats(extendedStatsData);
        
        // Fetch top repositories with caching
        const reposData = await getCachedData('repositories', 
          () => axios.get('/api/repositories', { params: { limit: 20 } }).then(res => res.data)
        );
        setRepositories(reposData);
        
        // Fetch top contributors with caching
        const contribData = await getCachedData('contributors', 
          () => axios.get('/api/contributors', { params: { limit: 20 } }).then(res => res.data)
        );
        setContributors(contribData);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please make sure the API server is running.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center p-8 max-w-md">
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
    );
  }

  return (
    <OfflineMode>
      <main className="min-h-screen">
        <Header />
        
        <div className="container mx-auto px-4 py-8">
          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 mb-8">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('contributors')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'contributors'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Contributors
              </button>
              <button
                onClick={() => setActiveTab('geography')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'geography'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Geographic Distribution
              </button>
              <button
                onClick={() => setActiveTab('activity')}
                className={`pb-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'activity'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Activity & Trends
              </button>
            </nav>
          </div>
          
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              {/* Stats Overview */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatCard 
                  title="Total Repositories" 
                  value={stats?.total_repositories || 0} 
                  icon="repository"
                />
                <StatCard 
                  title="Total Contributors" 
                  value={stats?.total_contributors || 0} 
                  icon="users"
                />
                <StatCard 
                  title="Top Language" 
                  value={stats?.top_languages[0]?.name || 'N/A'} 
                  icon="code"
                />
                <StatCard 
                  title="Top Topic" 
                  value={stats?.top_topics[0]?.name || 'N/A'} 
                  icon="tag"
                />
              </div>
              
              {/* Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div className="card">
                  <h2 className="text-xl font-semibold mb-4">Top Languages</h2>
                  <LanguageChart languages={stats?.top_languages || []} />
                </div>
                
                <div className="card">
                  <h2 className="text-xl font-semibold mb-4">Popular Topics</h2>
                  <TopicCloud topics={stats?.top_topics || []} />
                </div>
              </div>
              
              {/* Tables */}
              <div className="grid grid-cols-1 gap-8">
                <div className="card">
                  <h2 className="text-xl font-semibold mb-4">Top Repositories by Stars</h2>
                  <RepositoryTable repositories={repositories} />
                </div>
              </div>
            </>
          )}
          
          {/* Contributors Tab */}
          {activeTab === 'contributors' && (
            <div className="space-y-8">
              <div className="card">
                <MultiRepoContributors />
              </div>
              
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Top Contributors</h2>
                <ContributorTable contributors={contributors} />
              </div>
              
              {extendedStats?.top_companies && extendedStats.top_companies.length > 0 && (
                <div className="card">
                  <h2 className="text-xl font-semibold mb-4">Top Companies</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Company
                          </th>
                          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Contributors
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {extendedStats.top_companies.map((company, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {company.name}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {company.count}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Geography Tab */}
          {activeTab === 'geography' && (
            <div className="card">
              <GeographicDistribution />
            </div>
          )}
          
          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div className="space-y-8">
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Repository Creation Timeline</h2>
                <ActivityTimeline timelineData={extendedStats?.activity_timeline || []} />
              </div>
              
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Repository Size Distribution</h2>
                <div className="py-4">
                  {extendedStats?.size_distribution && (
                    <div className="space-y-4">
                      {extendedStats.size_distribution.map((size, index) => (
                        <div key={index} className="relative">
                          <div className="flex items-center mb-1">
                            <div className="text-sm font-medium w-1/3">{size.category}</div>
                            <div className="flex-1 relative h-6">
                              <div 
                                className="absolute top-0 left-0 h-full bg-green-500 rounded"
                                style={{ 
                                  width: `${(size.count / Math.max(...extendedStats.size_distribution.map(s => s.count))) * 100}%` 
                                }}
                              ></div>
                              <div className="absolute top-0 left-2 h-full flex items-center text-xs text-white">
                                {size.count} repositories
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </OfflineMode>
  );
} 