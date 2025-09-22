function standupReportApp() {
  return {
    currentReportType: 'daily',
    init() {
      this.setupToggleListeners();
      const root = document.getElementById('standup-report-root');
      window.STANDUP_SELECTED_DATE = root ? root.getAttribute('data-selected-date') : '';
      // Ensure the correct main section is visible on initial load
      const checked = document.querySelector('input[name="mainSection"]:checked');
      this.switchMainSection(checked ? checked.value : 'reports');
    },
    setupToggleListeners() {
      const mainToggles = document.querySelectorAll('input[name="mainSection"]');
      mainToggles.forEach(toggle => {
        toggle.addEventListener('change', (e) => { 
          this.switchMainSection(e.target.value); 
        });
      });
    },
    switchMainSection(section) {
      const reportsSection = document.getElementById('reportsSection');
      const blockersSection = document.getElementById('blockersSection');
      const mainTabContent = document.getElementById('mainTabContent');
      
      // Check if blockersSection is nested inside reportsSection and move it if needed
      if (blockersSection && reportsSection && reportsSection.contains(blockersSection)) {
        mainTabContent.appendChild(blockersSection);
      }
      
      // Hide all sections first
      if (reportsSection) {
        reportsSection.style.display = 'none';
        reportsSection.classList.remove('show', 'active');
        reportsSection.classList.remove('fade');
      }
      if (blockersSection) {
        blockersSection.style.display = 'none';
        blockersSection.classList.remove('show', 'active');
        blockersSection.classList.remove('fade');
      }
      
      // Ensure parent container is visible
      if (mainTabContent) {
        mainTabContent.style.display = 'block';
      }
      
      switch(section) {
        case 'reports':
          if (reportsSection) {
            reportsSection.style.display = 'block';
            reportsSection.classList.add('show', 'active');
            reportsSection.classList.remove('fade');
          }
          break;
        case 'blockers':
          if (blockersSection) {
            blockersSection.style.display = 'block';
            blockersSection.style.visibility = 'visible';
            blockersSection.style.opacity = '1';
            blockersSection.style.height = 'auto';
            blockersSection.style.minHeight = '200px';
            blockersSection.classList.add('show', 'active');
            blockersSection.classList.remove('fade');
            
            // Force a reflow to ensure the browser applies the changes
            blockersSection.offsetHeight;
          }
          break;
      }
    }
  }
}

// AI Content Cleanup function
function cleanupAIContent() {
    const aiContainers = document.querySelectorAll('.ai-content-formatted');
    
    aiContainers.forEach(container => {
        let innerHTML = container.innerHTML;
        
        // Remove "Strategic Team Standup Analysis" header (various formats)
        innerHTML = innerHTML.replace(/<h[1-6][^>]*>[\s\S]*?Strategic Team Standup Analysis[\s\S]*?<\/h[1-6]>/gi, '');
        innerHTML = innerHTML.replace(/##?\s*Strategic Team Standup Analysis\s*/gi, '');
        
        // Remove "📈 Strategic Metadata" section and everything after it until next major header
        innerHTML = innerHTML.replace(/<h[1-6][^>]*>[\s\S]*?📈[\s\S]*?Strategic Metadata[\s\S]*?<\/h[1-6]>[\s\S]*?(?=<h[1-6]|$)/gi, '');
        innerHTML = innerHTML.replace(/\*\*📈 Strategic Metadata\*\*:[\s\S]*?(?=\*\*[^📈]|\n##|$)/gi, '');
        
        // Remove JSON metadata blocks
        innerHTML = innerHTML.replace(/<pre[^>]*>[\s\S]*?"team_sentiment"[\s\S]*?<\/pre>/gi, '');
        innerHTML = innerHTML.replace(/\{[\s\S]*?"team_sentiment"[\s\S]*?\}/gi, '');
        
        // Clean up any remaining metadata patterns
        innerHTML = innerHTML.replace(/📈\s*Strategic Metadata[:\s]*[\s\S]*?(?=\*\*|##|$)/gi, '');
        
        // Remove empty paragraphs and extra whitespace
        innerHTML = innerHTML.replace(/<p[^>]*>\s*<\/p>/gi, '');
        innerHTML = innerHTML.replace(/\n\s*\n\s*\n/g, '\n\n');
        
        container.innerHTML = innerHTML;
        
        // Second pass: Remove any remaining elements that contain the unwanted content
        const allElements = container.querySelectorAll('*');
        allElements.forEach(el => {
            const text = el.textContent.trim();
            if ((text.includes('Strategic Team Standup Analysis') && text.length < 100) ||
                (text.includes('📈 Strategic Metadata') && text.length < 50) ||
                (text.includes('team_sentiment') && text.includes('velocity_score'))) {
                el.remove();
            }
        });
    });
}

// Charts init
document.addEventListener('DOMContentLoaded', function() {
  // Run AI content cleanup immediately
  cleanupAIContent();
  
  // Run cleanup again after a short delay to catch dynamically loaded content
  setTimeout(cleanupAIContent, 500);
  const moodCanvas = document.getElementById('moodChart');
  if (moodCanvas) {
    try {
      const payload = JSON.parse(moodCanvas.dataset.chart || '{}');
      const labels = payload.labels || [];
      const data = payload.data || [];
      new Chart(moodCanvas, { type: 'line', data: { labels, datasets: [{ label: 'Team Mood', data, borderColor: 'rgb(147, 51, 234)', backgroundColor: 'rgba(147, 51, 234, 0.1)', tension: 0.1 }] }, options: { responsive: true, scales: { y: { beginAtZero: true, max: 10 } } } });
    } catch (e) { console.error('Mood chart payload error:', e); }
  }

  const blockerCanvas = document.getElementById('blockerChart');
  if (blockerCanvas) {
    try {
      const payload = JSON.parse(blockerCanvas.dataset.chart || '{}');
      const labels = payload.labels || [];
      const data = payload.data || [];
      new Chart(blockerCanvas, { type: 'doughnut', data: { labels, datasets: [{ data, backgroundColor: ['rgb(239, 68, 68)','rgb(245, 158, 11)','rgb(59, 130, 246)','rgb(16, 185, 129)','rgb(139, 92, 246)'] }] }, options: { responsive: true, plugins: { legend: { position: 'bottom' } } } });
    } catch (e) { console.error('Blocker chart payload error:', e); }
  }

  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('resolve-blocker-btn') || e.target.parentElement?.classList.contains('resolve-blocker-btn')) {
      const btn = e.target.classList.contains('resolve-blocker-btn') ? e.target : e.target.parentElement;
      const blockerId = btn.getAttribute('data-blocker-id');
      const blockerTitle = btn.getAttribute('data-blocker-title');
      document.getElementById('blockerTitleDisplay').textContent = blockerTitle;
      document.getElementById('resolutionNotes').value = '';
      const confirmBtn = document.getElementById('confirmResolveBtn');
      confirmBtn.setAttribute('data-blocker-id', blockerId);
      confirmBtn.setAttribute('data-blocker-title', blockerTitle);
      const modal = new bootstrap.Modal(document.getElementById('resolveBlockerModal'));
      modal.show();
    }

    if (e.target.classList.contains('unresolve-blocker-btn') || e.target.parentElement?.classList.contains('unresolve-blocker-btn')) {
      const btn = e.target.classList.contains('unresolve-blocker-btn') ? e.target : e.target.parentElement;
      const blockerId = btn.getAttribute('data-blocker-id');
      const blockerTitle = btn.getAttribute('data-blocker-title');
      if (!confirm(`Are you sure you want to reopen "${blockerTitle}"?`)) { return; }
      fetch(`/standup/api/blockers/unresolve/${blockerId}/`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCsrfToken() } })
        .then(r => r.json()).then(data => { if (data.success) { showMessage(data.message, 'success'); setTimeout(() => window.location.reload(), 1000); } else { showMessage(data.error, 'error'); } })
        .catch(error => { console.error('Error unresolving blocker:', error); showMessage('Failed to reopen blocker', 'error'); });
    }
  });

  document.getElementById('confirmResolveBtn')?.addEventListener('click', function() {
    const blockerId = this.getAttribute('data-blocker-id');
    const blockerTitle = this.getAttribute('data-blocker-title');
    const resolutionNotes = document.getElementById('resolutionNotes').value.trim();
    const modal = bootstrap.Modal.getInstance(document.getElementById('resolveBlockerModal'));
    modal.hide();
    fetch(`/standup/api/blockers/resolve/${blockerId}/`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCsrfToken() }, body: `resolution_notes=${encodeURIComponent(resolutionNotes)}` })
      .then(r => r.json()).then(data => { if (data.success) { showMessage(data.message, 'success'); setTimeout(() => window.location.reload(), 1000); } else { showMessage(data.error, 'error'); } })
      .catch(error => { console.error('Error resolving blocker:', error); showMessage('Failed to resolve blocker', 'error'); });
  });
});

function showMessage(message, type) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
  toast.style.position = 'fixed'; toast.style.top = '20px'; toast.style.right = '20px'; toast.style.zIndex = '9999'; toast.style.minWidth = '300px';
  toast.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  document.body.appendChild(toast);
  setTimeout(() => { if (toast.parentNode) { toast.parentNode.removeChild(toast); } }, 5000);
}

function getCsrfToken() {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
  if (csrfToken) return csrfToken.value;
  const cookieValue = document.cookie.split(';').find(cookie => cookie.trim().startsWith('csrftoken='));
  if (cookieValue) return cookieValue.split('=')[1];
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  return metaToken ? metaToken.getAttribute('content') : '';
}

function openResolveModal(blockerId, blockerTitle) {
  document.getElementById('blockerTitleDisplay').textContent = blockerTitle;
  document.getElementById('resolutionNotes').value = '';
  const confirmBtn = document.getElementById('confirmResolveBtn');
  confirmBtn.setAttribute('data-blocker-id', blockerId);
  confirmBtn.setAttribute('data-blocker-title', blockerTitle);
  const modal = new bootstrap.Modal(document.getElementById('resolveBlockerModal'));
  modal.show();
}
