'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function MultiRepoContributors() {
  const [contributors, setContributors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [minRepos, setMinRepos] = useState(2);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/contributors/multi-repo', {
          params: { min_repos: minRepos }
        });
        setContributors(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching multi-repo contributors:', err);
        setError('Failed to load multi-repository contributors data.');
        setLoading(false);
      }
    };

    fetchData();
  }, [minRepos]);

  if (loading) {
    return <div className="text-center py-10">Loading multi-repository contributors...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center py-10">{error}</div>;
  }

  if (!contributors || contributors.length === 0) {
    return <div className="text-gray-500 text-center py-10">No contributors found who work on multiple repositories.</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Contributors Working on Multiple Repositories</h2>
        <div className="flex items-center space-x-2">
          <label htmlFor="min-repos" className="text-sm text-gray-600">
            Min Repositories:
          </label>
          <select
            id="min-repos"
            value={minRepos}
            onChange={(e) => setMinRepos(Number(e.target.value))}
            className="border rounded px-2 py-1 text-sm"
          >
            {[2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contributor
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Repositories
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Contributions
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {contributors.map((contributor, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <img 
                        className="h-10 w-10 rounded-full" 
                        src={`https://github.com/${contributor.username}.png?size=40`} 
                        alt={contributor.username}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png";
                        }}
                      />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        <a 
                          href={contributor.html_url || `https://github.com/${contributor.username}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="hover:text-blue-600"
                        >
                          {contributor.name || contributor.username}
                        </a>
                      </div>
                      <div className="text-sm text-gray-500">
                        @{contributor.username}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900">
                    <span className="font-semibold">{contributor.repository_count}</span> repositories
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {contributor.repositories.slice(0, 3).join(", ")}
                    {contributor.repositories.length > 3 && "..."}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contributor.total_contributions.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contributor.location || "Unknown"}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {contributor.company || "Not specified"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 