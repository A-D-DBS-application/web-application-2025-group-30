const api = {
  login: async (username) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username})
    });
    return res.json();
  },
  register: async (username, role) => {
    const res = await fetch('/auth/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, role})
    });
    return res.json();
  },
  me: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    const res = await fetch('/users/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) return null;
    return res.json();
  },
  fetchEvents: async () => {
    const res = await fetch('/events/');
    return res.json();
  },
  createEvent: async (data) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch('/events/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(data)
    });
    return res.json();
  },
  subscribeEvent: async (eventId) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`/events/${eventId}/subscribe`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return res.json();
  },
  confirmAssignment: async (eventId, userId) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch(`/events/${eventId}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ user_id: userId })
    });
    return res.json();
  },
  getShifts: async () => {
    const token = localStorage.getItem('access_token');
    const res = await fetch('/events/shifts', { headers: { 'Authorization': `Bearer ${token}` } });
    return res.json();
  },
  submitAvailability: async (data) => {
    const token = localStorage.getItem('access_token');
    const res = await fetch('/availability', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(data)
    });
    return res.json();
  }
};

// Utils
function formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString();
}

// Page Logic
document.addEventListener('DOMContentLoaded', async () => {
    const path = window.location.pathname;

    // Login Page
    if (document.getElementById('loginForm')) {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const showRegister = document.getElementById('showRegister');
        const cancelRegister = document.getElementById('cancelRegister');
        const loginError = document.getElementById('loginError');

        showRegister.addEventListener('click', () => {
            registerForm.style.display = 'block';
            showRegister.parentElement.style.display = 'none';
        });

        if (cancelRegister) {
            cancelRegister.addEventListener('click', () => {
                registerForm.style.display = 'none';
                showRegister.parentElement.style.display = 'block';
            });
        }

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const res = await api.login(username);
            if (res.access_token) {
                localStorage.setItem('access_token', res.access_token);
                const me = await api.me();
                if (me.role === 'manager') window.location.href = '/manager';
                else window.location.href = '/dashboard';
            } else {
                loginError.textContent = res.error || 'Login failed';
            }
        });

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('regUsername').value;
            const role = document.getElementById('regRole').value;
            const res = await api.register(username, role);
            if (res.access_token) {
                localStorage.setItem('access_token', res.access_token);
                if (role === 'manager') window.location.href = '/manager';
                else window.location.href = '/dashboard';
            } else {
                alert(res.error || 'Registration failed');
            }
        });
    }

    // Manager Page
    if (path === '/manager') {
        const eventsList = document.getElementById('eventsList');
        const createModal = document.getElementById('createEventModal');
        const openModalBtn = document.getElementById('openCreateEventModal');
        const closeModalBtn = document.getElementById('closeCreateEventModal');
        const createForm = document.getElementById('createEventForm');

        // Modal Logic
        if (openModalBtn) {
            openModalBtn.addEventListener('click', () => createModal.classList.add('active'));
            closeModalBtn.addEventListener('click', () => createModal.classList.remove('active'));
            window.addEventListener('click', (e) => {
                if (e.target === createModal) createModal.classList.remove('active');
            });
        }

        if (createForm) {
            createForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(createForm);
                const data = Object.fromEntries(formData.entries());
                // Combine date and time
                data.start = `${data.date}T${data.start_time}`;
                data.end = `${data.date}T${data.end_time}`;
                
                const res = await api.createEvent(data);
                if (res.id) {
                    createModal.classList.remove('active');
                    createForm.reset();
                    loadManagerEvents();
                } else {
                    alert('Error creating event');
                }
            });
        }

        async function loadManagerEvents() {
            const events = await api.fetchEvents();
            eventsList.innerHTML = '';
            events.forEach(event => {
                const assignedCount = (event.assigned || []).length;
                const capacity = event.capacity || 1;
                const progress = Math.min((assignedCount / capacity) * 100, 100);
                
                const div = document.createElement('div');
                div.className = 'event-item card';
                div.innerHTML = `
                    <div class="event-header">
                        <span class="event-title">${event.title}</span>
                        <span class="event-meta">${formatDate(event.start)}</span>
                    </div>
                    <p>${event.description || 'No description'}</p>
                    <div class="event-meta">
                        ${event.start.split('T')[1]} - ${event.end.split('T')[1]}
                    </div>
                    
                    <div class="progress-container">
                        <div class="progress-bar" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-text">
                        <span>${assignedCount} / ${capacity} Assigned</span>
                    </div>

                    ${(event.pending && event.pending.length > 0) ? `
                        <div class="pending-list">
                            <strong>Pending Requests:</strong>
                            ${event.pending.map(uid => `
                                <div class="pending-item">
                                    <span>User ID: ${uid.substring(0,8)}...</span>
                                    <button class="btn btn-success btn-sm" onclick="confirmUser('${event.id}', '${uid}')">Confirm</button>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                `;
                eventsList.appendChild(div);
            });
        }

        window.confirmUser = async (eventId, userId) => {
            await api.confirmAssignment(eventId, userId);
            loadManagerEvents();
        };

        loadManagerEvents();
    }

    // Employee Dashboard
    if (path === '/dashboard') {
        const myShiftsList = document.getElementById('myShiftsList');
        const availableShiftsList = document.getElementById('availableShiftsList');
        const me = await api.me();

        async function loadEmployeeData() {
            const allEvents = await api.fetchEvents();
            const myShifts = await api.getShifts(); // This returns assigned shifts
            
            // My Shifts
            myShiftsList.innerHTML = '';
            if (myShifts.length === 0) {
                myShiftsList.innerHTML = '<p>No shifts assigned yet.</p>';
            } else {
                myShifts.forEach(event => {
                    const div = document.createElement('div');
                    div.className = 'event-item';
                    div.innerHTML = `
                        <div class="event-header">
                            <span class="event-title">${event.title}</span>
                            <span class="event-meta">${formatDate(event.start)}</span>
                        </div>
                        <p>${event.description || ''}</p>
                        <div class="event-meta">
                            ${event.start.split('T')[1]} - ${event.end.split('T')[1]}
                        </div>
                    `;
                    myShiftsList.appendChild(div);
                });
            }

            // Available Shifts (Not assigned to me)
            availableShiftsList.innerHTML = '';
            const availableEvents = allEvents.filter(e => {
                const isAssigned = (e.assigned || []).includes(me.id);
                return !isAssigned;
            });

            if (availableEvents.length === 0) {
                availableShiftsList.innerHTML = '<p>No available shifts.</p>';
            } else {
                availableEvents.forEach(event => {
                    const isPending = (event.pending || []).includes(me.id);
                    const isFull = (event.assigned || []).length >= event.capacity;

                    const div = document.createElement('div');
                    div.className = 'event-item';
                    div.innerHTML = `
                        <div class="event-header">
                            <span class="event-title">${event.title}</span>
                            <span class="event-meta">${formatDate(event.start)}</span>
                        </div>
                        <p>${event.description || ''}</p>
                        <div class="event-meta">
                            ${event.start.split('T')[1]} - ${event.end.split('T')[1]}
                        </div>
                        <div class="event-actions">
                            ${isPending 
                                ? '<span class="btn btn-secondary" style="cursor: default;">Pending Approval...</span>' 
                                : (isFull 
                                    ? '<span style="color: var(--text-light);">Full</span>' 
                                    : `<button class="btn btn-primary" onclick="subscribe('${event.id}')">I'm Available</button>`
                                )
                            }
                        </div>
                    `;
                    availableShiftsList.appendChild(div);
                });
            }
        }

        window.subscribe = async (eventId) => {
            await api.subscribeEvent(eventId);
            loadEmployeeData();
        };

        loadEmployeeData();
    }
});