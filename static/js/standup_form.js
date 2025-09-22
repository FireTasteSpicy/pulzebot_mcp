document.addEventListener('alpine:init', () => {
  window.standupFormApp = function() {
    return {
      formData: Alpine.$persist({ yesterday: '', today: '', blockers: '' }),
      inputMethod: 'manual',
      voiceProcessingCompleted: false,
      isSubmitting: false,
      isRecording: false,
      hasRecording: false,
      isTranscribing: false,
      isProcessingAI: false,
      recordingDuration: 0,
      isRecordingSupported: false,
      showAutoSaveIndicator: false,
      autoSaveStatus: '',
      submissionResult: null,
      isFormValid: false,
      charCounts: { yesterday: 0, today: 0, blockers: 0 },
      suggestions: [],
      suggestedTeammates: [],
      mediaRecorder: null,
      recordingInterval: null,
      audioBlob: null,
      init() {
        this.checkRecordingSupport();
        this.loadSuggestions();
        this.updateCharCounts();
        this.validateForm();
        if (this.formData.yesterday || this.formData.today || this.formData.blockers) {
          this.autoSaveStatus = 'Draft loaded';
          setTimeout(() => this.autoSaveStatus = '', 3000);
        }
      },
      checkRecordingSupport() { this.isRecordingSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia); },
      updateCharCount(field) { this.charCounts[field] = this.formData[field].length; },
      updateCharCounts() { Object.keys(this.charCounts).forEach(field => { this.updateCharCount(field); }); },
      validateForm() { this.isFormValid = this.formData.yesterday.trim().length > 0 && this.formData.today.trim().length > 0; },
      autoSave() { clearTimeout(this.autoSaveTimeout); this.autoSaveTimeout = setTimeout(() => { this.showAutoSaveIndicator = true; setTimeout(() => this.showAutoSaveIndicator = false, 2000); }, 1000); },
      formatTime(seconds) { const mins = Math.floor(seconds / 60); const secs = seconds % 60; return `${mins}:${secs.toString().padStart(2, '0')}`; },
      generateSuggestions() { this.suggestions = [ { id: 1, text: 'Completed feature implementation' }, { id: 2, text: 'Fixed critical bugs' }, { id: 3, text: 'Code review and documentation' }, { id: 4, text: 'API integration work' }, { id: 5, text: 'Testing and quality assurance' } ]; },
      applySuggestion(suggestion) { if (!this.formData.yesterday.includes(suggestion.text)) { this.formData.yesterday += (this.formData.yesterday ? ' ' : '') + suggestion.text + '.'; this.updateCharCount('yesterday'); this.validateForm(); } },
      showNotification(message, type = 'info') { console.log(`${type.toUpperCase()}: ${message}`); },
      getSentimentClass(sentiment) { if (sentiment >= 4) return 'bg-success'; if (sentiment >= 3) return 'bg-warning'; return 'bg-danger'; },
      getSentimentLabel(sentiment) { if (sentiment >= 4) return 'Positive'; if (sentiment >= 3) return 'Neutral'; return 'Negative'; },
      viewDashboard() { window.location.href = '/dashboard/'; },
      resetForm() { this.formData = { yesterday: '', today: '', blockers: '' }; this.submissionResult = null; this.voiceProcessingCompleted = false; this.inputMethod = 'manual'; this.updateCharCounts(); this.validateForm(); },
      loadSuggestions() { this.suggestedTeammates = ['Alice', 'Bob', 'Charlie']; },
      async startRecording() {
        try {
          if (!this.isRecordingSupported) { this.showNotification('Recording not supported in this browser', 'error'); return; }
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          this.mediaRecorder = new MediaRecorder(stream);
          this.audioBlob = null; this.recordingDuration = 0;
          const audioChunks = [];
          this.mediaRecorder.addEventListener('dataavailable', event => { audioChunks.push(event.data); });
          this.mediaRecorder.addEventListener('stop', () => {
            this.audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            this.hasRecording = true;
            const audioUrl = URL.createObjectURL(this.audioBlob);
            this.$refs.audioPlayer.src = audioUrl;
            this.processRecording();
          });
          this.mediaRecorder.start();
          this.isRecording = true;
          this.recordingInterval = setInterval(() => { this.recordingDuration++; }, 1000);
        } catch (error) {
          console.error('Error starting recording:', error);
          this.showNotification('Failed to start recording. Please check microphone permissions.', 'error');
        }
      },
      stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
          this.mediaRecorder.stop();
          this.isRecording = false;
          if (this.recordingInterval) { clearInterval(this.recordingInterval); this.recordingInterval = null; }
          this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
      },
      clearRecording() { this.hasRecording = false; this.voiceProcessingCompleted = false; this.audioBlob = null; this.recordingDuration = 0; if (this.$refs.audioPlayer) { this.$refs.audioPlayer.src = ''; } },
      async processRecording() {
        if (!this.audioBlob) { this.showNotification('No recording found to process', 'error'); return; }
        this.isTranscribing = true;
        try {
          const formData = new FormData();
          formData.append('audio', this.audioBlob, 'recording.wav');
          formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
          const transcriptionResponse = await fetch('/api/v1/ai/speech/transcribe/', { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          if (!transcriptionResponse.ok) { throw new Error(`Transcription failed: ${transcriptionResponse.statusText}`); }
          const transcriptionResult = await transcriptionResponse.json();
          const transcription = transcriptionResult.transcription;
          this.isTranscribing = false; this.isProcessingAI = true;
          const parseResponse = await fetch('/api/v1/ai/standup/parse/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value }, body: JSON.stringify({ transcription }) });
          if (!parseResponse.ok) { throw new Error(`Parsing failed: ${parseResponse.statusText}`); }
          const parseResult = await parseResponse.json();
          const parsedData = parseResult.parsed || parseResult;
          this.formData.yesterday = parsedData.yesterday || '';
          this.formData.today = parsedData.today || '';
          this.formData.blockers = parsedData.blockers || '';
          this.updateCharCounts(); this.validateForm();
          this.isProcessingAI = false; this.voiceProcessingCompleted = true;
          this.showNotification('Voice recording processed successfully! Please review and edit the form below.', 'success');
        } catch (error) {
          console.error('Error processing recording:', error);
          this.isTranscribing = false; this.isProcessingAI = false;
          this.showNotification(`Failed to process recording: ${error.message}`, 'error');
        }
      },
      async submitStandup() {
        if (!this.isFormValid || this.isSubmitting) { return; }
        this.isSubmitting = true;
        try {
          const formData = new FormData();
          formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
          formData.append('yesterday_work', this.formData.yesterday);
          formData.append('today_plan', this.formData.today);
          formData.append('blockers', this.formData.blockers);
          const response = await fetch('/standup/submit/', { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
          if (response.ok) {
            const result = await response.json();
            this.submissionResult = result;
            this.formData = { yesterday: '', today: '', blockers: '' };
            this.updateCharCounts(); this.validateForm();
            this.showNotification('Standup submitted successfully!', 'success');
          } else {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
        } catch (error) {
          console.error('Submission error:', error);
          this.showNotification('Failed to submit standup. Please try again.', 'error');
        } finally {
          this.isSubmitting = false;
        }
      }
    };
  };
});
