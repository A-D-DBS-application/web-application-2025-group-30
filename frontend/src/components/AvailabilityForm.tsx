import React, { useState } from 'react';

const AvailabilityForm: React.FC = () => {
    const [availability, setAvailability] = useState({
        day: '',
        startTime: '',
        endTime: '',
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setAvailability({
            ...availability,
            [name]: value,
        });
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        // Submit availability to the backend
        console.log('Submitting availability:', availability);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label>
                    Day:
                    <input
                        type="text"
                        name="day"
                        value={availability.day}
                        onChange={handleChange}
                        required
                    />
                </label>
            </div>
            <div>
                <label>
                    Start Time:
                    <input
                        type="time"
                        name="startTime"
                        value={availability.startTime}
                        onChange={handleChange}
                        required
                    />
                </label>
            </div>
            <div>
                <label>
                    End Time:
                    <input
                        type="time"
                        name="endTime"
                        value={availability.endTime}
                        onChange={handleChange}
                        required
                    />
                </label>
            </div>
            <button type="submit">Submit Availability</button>
        </form>
    );
};

export default AvailabilityForm;