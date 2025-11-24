import React, { useEffect, useState } from 'react';
import { fetchEvents, fetchAvailability } from '../api/client';
import CalendarView from '../components/CalendarView';
import EventForm from '../components/EventForm';
import ShiftList from '../components/ShiftList';

const ManagerPanel: React.FC = () => {
    const [events, setEvents] = useState([]);
    const [availability, setAvailability] = useState([]);

    useEffect(() => {
        const loadEvents = async () => {
            const fetchedEvents = await fetchEvents();
            setEvents(fetchedEvents);
        };

        const loadAvailability = async () => {
            const fetchedAvailability = await fetchAvailability();
            setAvailability(fetchedAvailability);
        };

        loadEvents();
        loadAvailability();
    }, []);

    return (
        <div>
            <h1>Manager Panel</h1>
            <EventForm />
            <CalendarView events={events} />
            <ShiftList availability={availability} />
        </div>
    );
};

export default ManagerPanel;