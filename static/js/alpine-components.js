/**
 * PulzeBot Alpine.js Components Library
 * Reusable interactive components for enhanced UX
 */

document.addEventListener('alpine:init', () => {
    
    // Real-time Clock Component
    Alpine.data('liveClock', () => ({
        time: new Date(),
        
        init() {
            setInterval(() => {
                this.time = new Date();
            }, 1000);
        },
        
        get formattedTime() {
            return this.time.toLocaleTimeString();
        },
        
        get formattedDate() {
            return this.time.toLocaleDateString();
        }
    }));
    
    // Animated Counter Component
    Alpine.data('animatedCounter', (target, duration = 2000) => ({
        current: 0,
        target: target,
        
        init() {
            this.animateToTarget();
        },
        
        animateToTarget() {
            const start = 0;
            const startTime = performance.now();
            
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function (ease out)
                const easeOut = 1 - Math.pow(1 - progress, 3);
                this.current = Math.floor(start + (this.target - start) * easeOut);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            
            requestAnimationFrame(animate);
        }
    }));
    
    // Loading Spinner Component
    Alpine.data('loadingSpinner', (initialState = false) => ({
        isLoading: initialState,
        
        show() {
            this.isLoading = true;
        },
        
        hide() {
            this.isLoading = false;
        },
        
        toggle() {
            this.isLoading = !this.isLoading;
        }
    }));
    
    
    // Form Validator Component
    Alpine.data('formValidator', (rules = {}) => ({
        fields: {},
        errors: {},
        touched: {},
        
        init() {
            // Initialise fields based on rules
            Object.keys(rules).forEach(field => {
                this.fields[field] = '';
                this.errors[field] = '';
                this.touched[field] = false;
            });
        },
        
        validate(field, value) {
            this.fields[field] = value;
            this.touched[field] = true;
            
            const rule = rules[field];
            if (!rule) return true;
            
            this.errors[field] = '';
            
            // Required validation
            if (rule.required && (!value || value.trim() === '')) {
                this.errors[field] = rule.required === true ? 'This field is required' : rule.required;
                return false;
            }
            
            // Min length validation
            if (rule.minLength && value.length < rule.minLength) {
                this.errors[field] = `Minimum ${rule.minLength} characters required`;
                return false;
            }
            
            // Max length validation
            if (rule.maxLength && value.length > rule.maxLength) {
                this.errors[field] = `Maximum ${rule.maxLength} characters allowed`;
                return false;
            }
            
            // Email validation
            if (rule.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                this.errors[field] = 'Please enter a valid email address';
                return false;
            }
            
            // Custom validation function
            if (rule.custom && typeof rule.custom === 'function') {
                const result = rule.custom(value);
                if (result !== true) {
                    this.errors[field] = result;
                    return false;
                }
            }
            
            return true;
        },
        
        validateAll() {
            let isValid = true;
            Object.keys(rules).forEach(field => {
                if (!this.validate(field, this.fields[field])) {
                    isValid = false;
                }
            });
            return isValid;
        },
        
        hasError(field) {
            return this.touched[field] && this.errors[field];
        },
        
        getError(field) {
            return this.hasError(field) ? this.errors[field] : '';
        }
    }));
    
    // Auto-save Component
    Alpine.data('autoSave', (endpoint, interval = 5000) => ({
        data: {},
        lastSaved: null,
        isSaving: false,
        hasChanges: false,
        autoSaveInterval: null,
        
        init() {
            this.startAutoSave();
        },
        
        destroy() {
            this.stopAutoSave();
        },
        
        startAutoSave() {
            this.autoSaveInterval = setInterval(() => {
                if (this.hasChanges && !this.isSaving) {
                    this.save();
                }
            }, interval);
        },
        
        stopAutoSave() {
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }
        },
        
        markChanged() {
            this.hasChanges = true;
        },
        
        async save() {
            if (this.isSaving) return;
            
            this.isSaving = true;
            
            try {
                await Alpine.store('app').apiCall(endpoint, {
                    method: 'POST',
                    body: JSON.stringify(this.data)
                });
                
                this.hasChanges = false;
                this.lastSaved = new Date();
                console.log('Changes saved automatically');
                
            } catch (error) {
                console.error('Auto-save failed', error);
            } finally {
                this.isSaving = false;
            }
        }
    }));
    
    // Data Table Component
    Alpine.data('dataTable', (initialData = []) => ({
        data: initialData,
        filteredData: [],
        sortColumn: null,
        sortDirection: 'asc',
        searchTerm: '',
        currentPage: 1,
        itemsPerPage: 10,
        
        init() {
            this.filteredData = [...this.data];
        },
        
        search() {
            if (!this.searchTerm) {
                this.filteredData = [...this.data];
            } else {
                this.filteredData = this.data.filter(item => {
                    return Object.values(item).some(value => 
                        String(value).toLowerCase().includes(this.searchTerm.toLowerCase())
                    );
                });
            }
            this.currentPage = 1;
        },
        
        sort(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'asc';
            }
            
            this.filteredData.sort((a, b) => {
                let aVal = a[column];
                let bVal = b[column];
                
                if (typeof aVal === 'string') {
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }
                
                if (this.sortDirection === 'asc') {
                    return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
                } else {
                    return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
                }
            });
        },
        
        get paginatedData() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            const end = start + this.itemsPerPage;
            return this.filteredData.slice(start, end);
        },
        
        get totalPages() {
            return Math.ceil(this.filteredData.length / this.itemsPerPage);
        },
        
        nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
            }
        },
        
        prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
            }
        },
        
        goToPage(page) {
            if (page >= 1 && page <= this.totalPages) {
                this.currentPage = page;
            }
        }
    }));
    
    // File Upload Component
    Alpine.data('fileUpload', (options = {}) => ({
        files: [],
        dragOver: false,
        uploading: false,
        progress: 0,
        maxSize: options.maxSize || 10 * 1024 * 1024, // 10MB
        allowedTypes: options.allowedTypes || [],
        
        addFiles(fileList) {
            Array.from(fileList).forEach(file => {
                if (this.validateFile(file)) {
                    this.files.push({
                        id: Date.now() + Math.random(),
                        file,
                        name: file.name,
                        size: file.size,
                        type: file.type,
                        preview: null,
                        uploaded: false
                    });
                    
                    // Create preview for images
                    if (file.type.startsWith('image/')) {
                        this.createPreview(file);
                    }
                }
            });
        },
        
        validateFile(file) {
            if (file.size > this.maxSize) {
                console.error(`File ${file.name} is too large`);
                return false;
            }
            
            if (this.allowedTypes.length > 0 && !this.allowedTypes.includes(file.type)) {
                console.error(`File type ${file.type} is not allowed`);
                return false;
            }
            
            return true;
        },
        
        removeFile(id) {
            this.files = this.files.filter(f => f.id !== id);
        },
        
        createPreview(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const fileObj = this.files.find(f => f.file === file);
                if (fileObj) {
                    fileObj.preview = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        },
        
        async uploadFiles(endpoint) {
            if (this.files.length === 0) return;
            
            this.uploading = true;
            this.progress = 0;
            
            try {
                for (let i = 0; i < this.files.length; i++) {
                    const fileObj = this.files[i];
                    
                    const formData = new FormData();
                    formData.append('file', fileObj.file);
                    
                    await Alpine.store('app').apiCall(endpoint, {
                        method: 'POST',
                        body: formData,
                        headers: {} // Remove Content-Type for FormData
                    });
                    
                    fileObj.uploaded = true;
                    this.progress = ((i + 1) / this.files.length) * 100;
                }
                
                console.log('All files uploaded successfully');
                
            } catch (error) {
                console.error('Upload failed', error);
            } finally {
                this.uploading = false;
            }
        }
    }));
    
    // Modal Component
    Alpine.data('modal', (initialShow = false) => ({
        show: initialShow,
        
        open() {
            this.show = true;
            document.body.style.overflow = 'hidden';
        },
        
        close() {
            this.show = false;
            document.body.style.overflow = '';
        },
        
        toggle() {
            if (this.show) {
                this.close();
            } else {
                this.open();
            }
        }
    }));
    
    // Tabs Component
    Alpine.data('tabs', (initialTab = 0) => ({
        activeTab: initialTab,
        
        setActive(index) {
            this.activeTab = index;
        },
        
        isActive(index) {
            return this.activeTab === index;
        }
    }));
    
    // Chart Data Refresher
    Alpine.data('chartRefresher', (chartId, endpoint, interval = 30000) => ({
        isRefreshing: false,
        lastUpdated: new Date(),
        autoRefresh: false,
        refreshInterval: null,
        
        init() {
            this.startAutoRefresh();
        },
        
        destroy() {
            this.stopAutoRefresh();
        },
        
        async refresh() {
            if (this.isRefreshing) return;
            
            this.isRefreshing = true;
            
            try {
                const data = await Alpine.store('app').apiCall(endpoint);
                
                // Update chart if Chart.js instance exists
                if (window[chartId]) {
                    window[chartId].data = data;
                    window[chartId].update();
                }
                
                this.lastUpdated = new Date();
                
            } catch (error) {
                console.error('Failed to refresh chart data', error);
            } finally {
                this.isRefreshing = false;
            }
        },
        
        startAutoRefresh() {
            this.autoRefresh = true;
            this.refreshInterval = setInterval(() => {
                this.refresh();
            }, interval);
        },
        
        stopAutoRefresh() {
            this.autoRefresh = false;
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        },
        
        toggleAutoRefresh() {
            if (this.autoRefresh) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        }
    }));
});

// Export for use in other modules
window.AlpineComponents = {
    liveClock: 'liveClock',
    animatedCounter: 'animatedCounter',
    loadingSpinner: 'loadingSpinner',
    toastNotification: 'toastNotification',
    formValidator: 'formValidator',
    autoSave: 'autoSave',
    dataTable: 'dataTable',
    fileUpload: 'fileUpload',
    modal: 'modal',
    tabs: 'tabs',
    chartRefresher: 'chartRefresher'
};
