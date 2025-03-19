/**
 * Simple data caching mechanism for the dashboard
 */

// Cache duration in milliseconds (1 hour)
const CACHE_DURATION = 60 * 60 * 1000;

// Initialize cache
let cache = {};

// Load cache from localStorage on startup
if (typeof window !== 'undefined') {
  try {
    const savedCache = localStorage.getItem('dashboardCache');
    if (savedCache) {
      cache = JSON.parse(savedCache);
    }
  } catch (error) {
    console.error('Error loading cache:', error);
  }
}

/**
 * Get data from cache or fetch from API
 * @param {string} key - Cache key
 * @param {Function} fetchFn - Function to fetch data if not in cache
 * @param {boolean} forceRefresh - Force refresh from API
 * @returns {Promise<any>} - Cached or fresh data
 */
export async function getCachedData(key, fetchFn, forceRefresh = false) {
  const now = Date.now();
  
  // Check if we have valid cached data
  if (
    !forceRefresh &&
    cache[key] &&
    cache[key].timestamp &&
    now - cache[key].timestamp < CACHE_DURATION
  ) {
    return cache[key].data;
  }
  
  try {
    // Fetch fresh data
    const data = await fetchFn();
    
    // Update cache
    cache[key] = {
      data,
      timestamp: now
    };
    
    // Save to localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('dashboardCache', JSON.stringify(cache));
      } catch (error) {
        console.error('Error saving cache:', error);
      }
    }
    
    return data;
  } catch (error) {
    // If fetch fails but we have cached data (even if expired), use it
    if (cache[key] && cache[key].data) {
      console.warn(`Using stale cached data for ${key} due to fetch error`);
      return cache[key].data;
    }
    
    // Otherwise, rethrow the error
    throw error;
  }
}

/**
 * Clear the entire cache or a specific key
 * @param {string} key - Optional specific key to clear
 */
export function clearCache(key = null) {
  if (key) {
    delete cache[key];
  } else {
    cache = {};
  }
  
  // Update localStorage
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem('dashboardCache', JSON.stringify(cache));
    } catch (error) {
      console.error('Error saving cache:', error);
    }
  }
} 