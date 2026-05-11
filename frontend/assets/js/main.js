/**
 * Main Application Logic
 */

const API_URL = "https://trip-planner-backend-5v75.onrender.com";

const elements = {
    form: document.getElementById('planner-form'),
    submitBtn: document.getElementById('submit-btn'),
    progressSection: document.getElementById('progress-section'),
    resultSection: document.getElementById('result-section'),
    itineraryContent: document.getElementById('itinerary-content'),
    resetBtn: document.getElementById('reset-btn'),
    downloadBtn: document.getElementById('download-btn')
};

let currentJobId = null;
let pollInterval = null;

elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Collect form data
    const formData = {
        origin_city: document.getElementById('origin_city').value,
        destination: document.getElementById('destination').value,
        travel_dates: document.getElementById('travel_dates').value,
        date_yyyymmdd: document.getElementById('date_yyyymmdd').value,
        num_travellers: parseInt(document.getElementById('num_travellers').value),
        budget_inr: parseInt(document.getElementById('budget_inr').value),
        interests: document.getElementById('interests').value,
        travel_mode: document.querySelector('input[name="travel_mode"]:checked').value
    };

    let wakeUpMessageTimer = null;
    try {
        // UI Transition
        elements.form.parentElement.classList.add('hidden');
        elements.progressSection.classList.remove('hidden');
        PipelineUI.reset();
        PipelineUI.update(1);

        wakeUpMessageTimer = setTimeout(() => {
            const statusText = document.getElementById('status-text');
            if (statusText) {
                statusText.textContent = "Backend is waking up, please wait...";
            }
        }, 5000);

        // Start Planning
        const response = await fetch(`${API_URL}/api/plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        clearTimeout(wakeUpMessageTimer);

        if (!response.ok) throw new Error("Failed to start planning");

        const data = await response.json();
        currentJobId = data.job_id;
        
        // Start Polling
        startPolling();

    } catch (error) {
        if (wakeUpMessageTimer) clearTimeout(wakeUpMessageTimer);
        alert("Error: " + error.message);
        resetUI();
    }
});

function startPolling() {
    let phase = 1;
    // Simulate phase changes for better UX, or sync with backend logs if possible
    // Here we just increment phase slowly while waiting
    const phaseTimer = setInterval(() => {
        if (phase < 6) {
            phase++;
            PipelineUI.update(phase);
        }
    }, 15000); // 15 seconds per agent roughly

    pollInterval = setInterval(async () => {
        try {
            const resp = await fetch(`${API_URL}/api/status/${currentJobId}`);
            const data = await resp.json();

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                clearInterval(phaseTimer);
                showResult(data.result);
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                clearInterval(phaseTimer);
                alert("Planning failed: " + (data.error || "Unknown error"));
                resetUI();
            }
        } catch (error) {
            console.error("Polling error:", error);
        }
    }, 3000);
}

function showResult(markdown) {
    elements.progressSection.classList.add('hidden');
    elements.resultSection.classList.remove('hidden');
    elements.itineraryContent.innerHTML = MarkdownRenderer.render(markdown);
}

function resetUI() {
    elements.form.parentElement.classList.remove('hidden');
    elements.progressSection.classList.add('hidden');
    elements.resultSection.classList.add('hidden');
    if (pollInterval) clearInterval(pollInterval);
}

elements.resetBtn.addEventListener('click', resetUI);

elements.downloadBtn.addEventListener('click', () => {
    const text = elements.itineraryContent.innerText;
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `itinerary-${Date.now()}.txt`;
    a.click();
});
