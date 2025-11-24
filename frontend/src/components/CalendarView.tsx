import React, { useEffect, useState } from 'react';
import { fetchEvents } from '../api/client';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';

const CalendarView = () => {
    const [events, setEvents] = useState([]);
    const [date, setDate] = useState(new Date());

    useEffect(() => {
        const getEvents = async () => {
            const data = await fetchEvents();
            setEvents(data);
        };
        getEvents();
    }, []);

    const tileContent = ({ date }) => {
        const eventDate = date.toISOString().split('T')[0];
        const eventList = events.filter(event => event.date === eventDate);
        return eventList.length > 0 ? <ul>{eventList.map(event => <li key={event.id}>{event.title}</li>)}</ul> : null;
    };

    return (
        <div>
            <h2>Event Calendar</h2>
            <Calendar
                onChange={setDate}
                value={date}
                tileContent={tileContent}
            />
        </div>
    );
};

export default CalendarView;