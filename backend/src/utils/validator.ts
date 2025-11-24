export function validateUserInput(input: any): boolean {
    // Add validation logic for user input
    if (!input.username || !input.password) {
        return false;
    }
    return true;
}

export function validateEventData(event: any): boolean {
    // Add validation logic for event data
    if (!event.title || !event.date || !event.time) {
        return false;
    }
    return true;
}

export function validateAvailabilityData(availability: any): boolean {
    // Add validation logic for availability data
    if (!availability.userId || !availability.availableTimes) {
        return false;
    }
    return true;
}