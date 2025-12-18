# Personnel Scheduler

We have created a web application for intelligent personnel allocation and shift scheduling. It features an ILP-inspired assignment algorithm with constraint satisfaction, multi-tenant company support, and comprehensive availability management.

## Features

- **Multi-Tenant System**: Company registration codes for isolated workspaces
- **Role-Based Access**: Manager and employee roles with different permissions
- **Smart Shift Assignment**: Automated assignment with conflict detection and fairness optimization
- **Availability Management**: Employees submit availability windows, system validates assignments
- **Shift Swaps**: Request and approve shift swaps between employees
- **Calendar Views**: Visual calendar interface for events and shifts
- **Statistics Dashboard**: Utilization rates, workload distribution, and shift analytics
- **iCal Export**: Export personal schedules to calendar applications
- **Conflict Detection**: Validates overlapping shifts, break times, and daily hour limits

## Technology Stack

- **Backend**: Flask (Python) with Blueprint architecture
- **Database**: PostgreSQL via Supabase REST API
- **Algorithm**: Greedy ILP-inspired constraint satisfaction for shift assignment
- **Frontend**: Jinja2 templates with responsive CSS
- **Authentication**: Session-based with bcrypt password hashing

## Project Structure

```
personnel-scheduler/
├── backend_flask/              # Flask backend application
│   ├── app.py                 # Main application entry point
│   ├── models.py              # Database models and operations
│   ├── migrations.py          # Database schema migrations
│   ├── routes/                # Blueprint route handlers
│   │   ├── main.py           # Dashboard and home routes
│   │   ├── auth.py           # Authentication routes
│   │   ├── events.py         # Event/shift management
│   │   ├── users.py          # User management
│   │   ├── availability.py   # Availability management
│   │   └── ical.py           # iCalendar export
│   ├── utils/                 # Core algorithms and utilities
│   │   ├── ilp_assignment.py # Shift assignment algorithm
│   │   └── shift_validator.py # Constraint validation
│   ├── templates/             # Jinja2 HTML templates
│   ├── static/                # CSS, JS, and static assets
│   └── requirements.txt       # Python dependencies
├── docs/                      # Documentation
│   └── api.md                # API documentation
├── docker-compose.yml         # Docker configuration
└── README.md                  # This file
```

## Algorithm Overview

The shift assignment system uses a greedy constraint satisfaction approach with:

**Hard Constraints** (must satisfy):
- No overlapping shifts per employee
- Minimum 1-hour break between shifts
- Maximum 12 hours per employee per day
- Availability window matching
- Shift capacity requirements

**Soft Constraints** (optimize for):
- Fairness: Even hour distribution across employees (60% weight)
- Availability match: Prefer shifts within availability windows (40% weight)

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database (or Supabase account)
- pip for package management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd personnel-scheduler
```

2. Set up Python environment:
```bash
cd backend_flask
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create `.env` file in `backend_flask/` with:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_secret_key
```

5. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Database Setup

The application automatically runs migrations on startup. Tables created:
- `companies` - Company/organization records
- `users` - User accounts (managers and employees)
- `events` - Shifts and events
- `availabilities` - Employee availability windows
- `shift_swaps` - Shift swap requests and approvals

## Usage

### For Managers

1. Register as a manager (creates a new company)
2. Share the registration code with employees
3. Create shifts/events with required capacity
4. Use autofill to automatically assign employees based on availability
5. Review and approve shift swap requests
6. View statistics and workload distribution

### For Employees

1. Register with company registration code
2. Submit availability windows
3. View assigned shifts on dashboard
4. Request shift swaps with colleagues
5. Export schedule to calendar app via iCal

## Key Features

### Intelligent Assignment

The autofill feature suggests optimal employee assignments considering:
- Employee availability windows
- Current workload fairness
- Constraint violations (overlaps, breaks, daily limits)
- Assignment quality scores with detailed reasoning

### Multi-Tenant Isolation

All data is isolated by `company_id` ensuring:
- Employees only see their company's data
- Managers only manage their company's shifts
- Secure separation between organizations

### Constraint Validation

Every assignment is validated against:
- Shift overlap conflicts
- Insufficient break time between shifts
- Excessive daily working hours
- Availability window mismatches

## Contributing

This is an academic project for a programming course. Contributions should focus on:
- Code quality and documentation
- Algorithm optimization
- Additional constraint types
- UI/UX improvements

## License

Academic project - see course requirements for usage terms.
## Link to audio/video recording of feedback sessions with  external partner
https://ugentbe-my.sharepoint.com/:v:/g/personal/viktor_walravens_ugent_be/IQBliQ_LfeJ6RKcuD-5ybIGyAZ0ryFH2BlIWO1IuOKLV2FM

