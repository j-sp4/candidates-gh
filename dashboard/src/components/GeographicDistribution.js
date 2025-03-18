'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function GeographicDistribution() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/contributors/by-location');
        setLocations(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching location data:', err);
        setError('Failed to load geographic distribution data.');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="text-center py-10">Loading geographic distribution...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center py-10">{error}</div>;
  }

  if (!locations || locations.length === 0) {
    return <div className="text-gray-500 text-center py-10">No location data available.</div>;
  }

  // Filter out "Unknown" location for the chart
  const knownLocations = locations.filter(loc => loc.location !== "Unknown");
  
  // Take top 15 locations for display
  const topLocations = knownLocations.slice(0, 15);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Geographic Distribution of Contributors</h2>
      
      {/* Location bars */}
      <div className="space-y-2">
        {topLocations.map((location, index) => (
          <div 
            key={index} 
            className="relative"
            onClick={() => setSelectedLocation(selectedLocation === location.location ? null : location.location)}
          >
            <div className="flex items-center mb-1">
              <div className="text-sm font-medium truncate w-1/4">{location.location}</div>
              <div className="flex-1 relative h-6">
                <div 
                  className="absolute top-0 left-0 h-full bg-blue-500 rounded"
                  style={{ width: `${(location.count / topLocations[0].count) * 100}%` }}
                ></div>
                <div className="absolute top-0 left-2 h-full flex items-center text-xs text-white">
                  {location.count} contributors
                </div>
              </div>
            </div>
            
            {/* Expanded view with contributors from this location */}
            {selectedLocation === location.location && (
              <div className="ml-6 mt-2 mb-4 bg-gray-50 p-3 rounded-md">
                <h3 className="text-sm font-semibold mb-2">Contributors from {location.location}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {location.contributors.slice(0, 9).map((contributor, idx) => (
                    <div key={idx} className="flex items-center p-2 bg-white rounded shadow-sm">
                      <img 
                        className="h-8 w-8 rounded-full mr-2" 
                        src={`https://github.com/${contributor.username}.png?size=32`} 
                        alt={contributor.username}
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png";
                        }}
                      />
                      <div>
                        <a 
                          href={contributor.html_url || `https://github.com/${contributor.username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-blue-600 hover:underline"
                        >
                          {contributor.name || contributor.username}
                        </a>
                        <div className="text-xs text-gray-500">
                          {contributor.contributions} contributions
                        </div>
                      </div>
                    </div>
                  ))}
                  {location.contributors.length > 9 && (
                    <div className="flex items-center justify-center p-2 bg-gray-100 rounded">
                      <span className="text-sm text-gray-500">
                        +{location.contributors.length - 9} more
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Unknown location count */}
      {locations.some(loc => loc.location === "Unknown") && (
        <div className="text-sm text-gray-500 mt-4">
          <span className="font-medium">Note:</span> {locations.find(loc => loc.location === "Unknown")?.count || 0} contributors have no location information.
        </div>
      )}
    </div>
  );
} 