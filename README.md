# Personnel Scheduler

This project is a web application designed to optimize personnel allocation. It includes features for user authentication, event management, and employee availability management.

## Features

- **User Login**: Users can log in to enter and manage their personal information.
- **Event Creation**: Managers can create and manage events.
- **Calendar View**: A calendar interface for visibility of events.
- **Availability Management**: Employees can submit and manage their availability and shifts.

## Project Structure

```
personnel-scheduler
├── backend
│   ├── src
│   │   ├── index.ts
│   │   ├── controllers
│   │   │   ├── auth.controller.ts
│   │   │   ├── users.controller.ts
│   │   │   └── events.controller.ts
│   │   ├── services
│   │   │   └── availability.service.ts
│   │   ├── models
│   │   │   └── index.ts
│   │   ├── routes
│   │   │   └── index.ts
│   │   └── utils
│   │       └── validator.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
├── frontend
│   ├── src
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api
│   │   │   └── client.ts
│   │   ├── components
│   │   │   ├── Login.tsx
│   │   │   ├── CalendarView.tsx
│   │   │   ├── EventForm.tsx
│   │   │   ├── AvailabilityForm.tsx
│   │   │   └── ShiftList.tsx
│   │   ├── pages
│   │   │   ├── Dashboard.tsx
│   │   │   └── ManagerPanel.tsx
│   │   └── styles
│   │       └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md
├── docs
│   └── api.md
├── scripts
│   └── seed-db.ts
├── .vscode
│   ├── launch.json
│   └── extensions.json
├── .env.example
├── docker-compose.yml
├── package.json
├── tsconfig.json
├── .gitignore
└── README.md
```

## Getting Started

1. Clone the repository.
2. Install dependencies for both backend and frontend.
3. Set up the environment variables as needed.
4. Run the backend and frontend servers.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.