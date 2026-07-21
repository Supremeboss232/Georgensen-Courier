// Partner section JS files
// jobs.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requirePartner()) return;
    
    try {
        const data = await getWithAuth('/api/v1/partners/jobs');
        loadAvailableJobs(data.available_jobs);
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
});

function loadAvailableJobs(jobs) {
    const tbody = document.getElementById('jobsTableBody');
    if (tbody) {
        tbody.innerHTML = '';
        jobs.forEach(job => {
            const row = `
                <tr>
                    <td>${job.job_id}</td>
                    <td>${job.pickup_location}</td>
                    <td>${job.delivery_location}</td>
                    <td>${job.distance} km</td>
                    <td>$${job.payout.toFixed(2)}</td>
                    <td><button class="btn btn-sm btn-success" onclick="acceptJob('${job.job_id}')">Accept</button></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
}

async function acceptJob(jobId) {
    try {
        await postWithAuth(`/api/v1/api/v1/partners/jobs/${jobId}/accept`, {});
        alert('Job accepted');
        location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
