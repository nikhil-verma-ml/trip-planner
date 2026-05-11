/**
 * Handles the visual progress of the 6-agent pipeline
 */
const PipelineUI = {
    steps: [
        "Researching destination and hidden gems...",
        "Checking 5-day weather forecast...",
        "Finding best hotel recommendations...",
        "Searching for flights and transport...",
        "Crafting day-by-day itinerary...",
        "Finalizing budget estimates..."
    ],

    update: function(phase) {
        const stepElements = document.querySelectorAll('.agent-step');
        const statusText = document.getElementById('status-text');

        stepElements.forEach((el, index) => {
            const stepNum = index + 1;
            if (stepNum < phase) {
                el.classList.add('completed');
                el.classList.remove('active');
            } else if (stepNum === phase) {
                el.classList.add('active');
                el.classList.remove('completed');
                statusText.innerText = this.steps[index];
            } else {
                el.classList.remove('active', 'completed');
            }
        });
    },

    reset: function() {
        document.querySelectorAll('.agent-step').forEach(el => {
            el.classList.remove('active', 'completed');
        });
        document.getElementById('status-text').innerText = "Waking up agents...";
    }
};
