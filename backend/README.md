# Personnel Scheduler Backend

This is the backend for the Personnel Scheduler web application, designed to optimize personnel allocation. The application includes user authentication, event management for managers, and availability management for employees.

## Features

- **User Authentication**: Users can log in and manage their personal information.
- **Event Management**: Managers can create, update, and retrieve events.
- **Availability Management**: Employees can submit and manage their availability and shifts.
- **API Integration**: The backend provides a RESTful API for the frontend application.

## Project Structure

- `src/index.ts`: Entry point of the application, initializes the server and sets up middleware and routes.
- `src/controllers`: Contains controllers for handling requests related to authentication, users, and events.
- `src/services`: Contains services for managing employee availability.
- `src/models`: Defines data models for users and events.
- `src/routes`: Main routing configuration linking routes to their respective controllers.
- `src/utils`: Utility functions for input validation.

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the backend directory:
   ```
   cd personnel-scheduler/backend
   ```
3. Install dependencies:
   ```
   npm install
   ```

## Usage

To start the backend server, run:
```
npm start
```

The server will be running on `http://localhost:3000` by default.

## Environment Variables

Create a `.env` file in the backend directory and define the necessary environment variables. You can refer to the `.env.example` file for guidance.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.