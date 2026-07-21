// Customer section JS files
// support.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requireCustomer()) return;
    
    try {
        const data = await getWithAuth('/api/v1/customers/support');
        loadTickets(data.tickets);
    } catch (error) {
        console.error('Failed to load support tickets:', error);
    }
});

function loadTickets(tickets) {
    const tbody = document.getElementById('ticketsTableBody');
    if (tbody) {
        tbody.innerHTML = '';
        tickets.forEach(ticket => {
            const row = `
                <tr>
                    <td>${ticket.ticket_number}</td>
                    <td>${ticket.subject}</td>
                    <td><span class="badge bg-${getStatusColor(ticket.status)}">${ticket.status}</span></td>
                    <td>${ticket.created}</td>
                    <td>${ticket.updated}</td>
                    <td><a href="/support/${ticket.id}" class="btn btn-sm btn-primary">View</a></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
}

function getStatusColor(status) {
    switch(status) {
        case 'open': return 'danger';
        case 'in_progress': return 'warning';
        case 'resolved': return 'success';
        default: return 'secondary';
    }
}

async function createTicket() {
    const category = document.getElementById('category').value;
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value;

    try {
        await postWithAuth('/api/v1/customers/support', {
            category,
            subject,
            message
        });
        alert('Support ticket created');
        location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
