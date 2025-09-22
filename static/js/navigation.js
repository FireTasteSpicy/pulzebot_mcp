function navigationApp() {
  return {
    mobileMenuOpen: false,
    isOnline: navigator.onLine,
    currentPage: window.location.pathname.split('/')[1] || 'dashboard',
    init() {
      window.addEventListener('online', () => {
        this.isOnline = true;
      });
      window.addEventListener('offline', () => {
        this.isOnline = false;
      });
    },
    clearCache() {
      if ('caches' in window) {
        caches.keys().then(names => {
          names.forEach(name => caches.delete(name));
        });
      }
      localStorage.clear();
      console.log('Cache cleared successfully');
    }
  }
}


