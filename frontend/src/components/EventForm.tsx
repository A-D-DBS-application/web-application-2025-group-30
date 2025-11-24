import React, { useState } from 'react';

const EventForm = () => {
    const [eventData, setEventData] = useState({
        title: '',
        date: '',
        time: '',
        description: ''
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setEventData({
            ...eventData,
            [name]: value
        });
    };

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        // Add logic to submit eventData to the backend
        console.log('Event submitted:', eventData);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label htmlFor="title">Event Title:</label>
                <input
                    type="text"
                    id="title"
                    name="title"
                    value={eventData.title}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label htmlFor="date">Date:</label>
                <input
                    type="date"
                    id="date"
                    name="date"
                    value={eventData.date}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label htmlFor="time">Time:</label>
                <input
                    type="time"
                    id="time"
                    name="time"
                    value={eventData.time}
                    onChange={handleChange}
                    required
                />
            </div>
            <div>
                <label htmlFor="description">Description:</label>
                <textarea
                    id="description"
                    name="description"
                    value={eventData.description}
                    onChange={handleChange}
                    required
                />
            </div>
            <button type="submit">Create Event</button>
        </form>
    );
};

export default EventForm;