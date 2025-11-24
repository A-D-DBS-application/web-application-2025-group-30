# API Documentation for Personnel Scheduler

## Authentication

### Login
- **Endpoint:** `POST /api/auth/login`
- **Description:** Authenticates a user and returns a token.
- **Request Body:**
  - `email`: string (required)
  - `password`: string (required)
- **Response:**
  - `token`: string
  - `user`: object (contains user details)

### Register
- **Endpoint:** `POST /api/auth/register`
- **Description:** Registers a new user.
- **Request Body:**
  - `name`: string (required)
  - `email`: string (required)
  - `password`: string (required)
- **Response:**
  - `message`: string

## Users

### Get User
- **Endpoint:** `GET /api/users/:id`
- **Description:** Retrieves user information by ID.
- **Response:**
  - `user`: object (contains user details)

### Update User
- **Endpoint:** `PUT /api/users/:id`
- **Description:** Updates user information.
- **Request Body:**
  - `name`: string (optional)
  - `email`: string (optional)
- **Response:**
  - `message`: string

## Events

### Create Event
- **Endpoint:** `POST /api/events`
- **Description:** Creates a new event.
- **Request Body:**
  - `title`: string (required)
  - `date`: string (required, format: YYYY-MM-DD)
  - `time`: string (required, format: HH:MM)
  - `description`: string (optional)
- **Response:**
  - `event`: object (contains event details)

### Get Events
- **Endpoint:** `GET /api/events`
- **Description:** Retrieves all events.
- **Response:**
  - `events`: array of objects (contains event details)

### Update Event
- **Endpoint:** `PUT /api/events/:id`
- **Description:** Updates an existing event.
- **Request Body:**
  - `title`: string (optional)
  - `date`: string (optional)
  - `time`: string (optional)
  - `description`: string (optional)
- **Response:**
  - `message`: string

## Availability

### Submit Availability
- **Endpoint:** `POST /api/availability`
- **Description:** Submits employee availability.
- **Request Body:**
  - `employeeId`: string (required)
  - `availableDays`: array of strings (required)
- **Response:**
  - `message`: string

### Get Availability
- **Endpoint:** `GET /api/availability/:employeeId`
- **Description:** Retrieves availability for a specific employee.
- **Response:**
  - `availability`: object (contains availability details)