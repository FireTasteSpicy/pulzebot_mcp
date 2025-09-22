// Wait for Alpine.js and all plugins to be ready
document.addEventListener('DOMContentLoaded', () => {
  const initStore = () => {
    if (window.Alpine && window.Alpine.$persist) {
      Alpine.store('app', {
        async apiCall(url, options = {}) {
          const defaultOptions = {
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            }
          };
          try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            if (!response.ok) {
              const errorData = await response.json().catch(() => ({}));
              throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
          } catch (error) {
            console.error('API Call Error:', error);
            throw error;
          }
        },
        performanceMetrics: {
          pageLoadTime: performance.now(),
          apiCalls: 0,
          errors: 0
        },
        trackApiCall() {
          this.performanceMetrics.apiCalls++;
        },
        trackError() {
          this.performanceMetrics.errors++;
        }
      });

      Alpine.magic('clipboard', () => {
        return (text) => {
          navigator.clipboard.writeText(text).then(() => {
            console.log('Copied to clipboard:', text);
          });
        };
      });

      Alpine.magic('formatDate', () => {
        return (date, options = {}) => {
          const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
          };
          return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
        };
      });

      return true;
    }
    return false;
  };

  if (!initStore()) {
    const checkInterval = setInterval(() => {
      if (initStore()) {
        clearInterval(checkInterval);
      }
    }, 50);

    setTimeout(() => {
      clearInterval(checkInterval);
      console.error('Alpine.js plugins failed to load within 5 seconds');
    }, 5000);
  }
});


