document.addEventListener('DOMContentLoaded', function() {
    
    // AI Analysis Button Handler
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async function() {
            const titleInput = document.getElementById('title');
            const descInput = document.getElementById('description');
            
            const title = titleInput ? titleInput.value.trim() : '';
            const description = descInput ? descInput.value.trim() : '';

            if (!title || !description) {
                alert('Please enter both Complaint Title and Description before analyzing.');
                return;
            }

            // UI loading state
            const originalBtnText = analyzeBtn.innerHTML;
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = `<div class="spinner"></div> Analyzing with Gemini AI...`;

            const previewCard = document.getElementById('ai-preview-card');
            if (previewCard) previewCard.style.display = 'none';

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ title, description })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    const result = data.analysis;

                    // Fill preview UI fields
                    document.getElementById('res-category').innerText = result.category || 'Other';
                    document.getElementById('res-priority').innerText = result.priority || 'Medium';
                    document.getElementById('res-department').innerText = result.department || 'General';
                    document.getElementById('res-summary').innerText = result.summary || 'Summary unavailable.';

                    // Fill hidden inputs for database submission
                    document.getElementById('input-category').value = result.category || 'Other';
                    document.getElementById('input-priority').value = result.priority || 'Medium';
                    document.getElementById('input-department').value = result.department || 'General';
                    document.getElementById('input-summary').value = result.summary || '';

                    // Apply status badge color to priority badge in preview
                    const prioBadge = document.getElementById('res-priority-badge');
                    if (prioBadge) {
                        prioBadge.className = `badge badge-priority-${(result.priority || 'Medium').toLowerCase()}`;
                    }

                    // Show Notice if fallback used
                    const noticeEl = document.getElementById('res-notice');
                    if (noticeEl) {
                        if (result.notice) {
                            noticeEl.innerText = result.notice;
                            noticeEl.style.display = 'block';
                        } else {
                            noticeEl.style.display = 'none';
                        }
                    }

                    // Display Preview Card
                    if (previewCard) {
                        previewCard.style.display = 'block';
                        previewCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }

                    // Enable Submit Button
                    const submitBtn = document.getElementById('submit-complaint-btn');
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('btn-secondary');
                        submitBtn.classList.add('btn-primary');
                    }
                } else {
                    alert(data.error || 'Failed to analyze complaint. Please try again.');
                }
            } catch (err) {
                console.error('AI Analysis Error:', err);
                alert('An error occurred while connecting to AI classifier service.');
            } finally {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = originalBtnText;
            }
        });
    }

    // Auto-dismiss Flash Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

});
