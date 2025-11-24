import React from 'react';
import { useEffect, useState } from 'react';
import { getUserData } from '../api/client';
import CalendarView from '../components/CalendarView';
import ShiftList from '../components/ShiftList';
import AvailabilityForm from '../components/AvailabilityForm';

const Dashboard: React.FC = () => {
    const [userData, setUserData] = useState(null);

    useEffect(() => {
        const fetchUserData = async () => {
            const data = await getUserData();
            setUserData(data);
        };

        fetchUserData();
    }, []);

    return (
        <div className="dashboard">
            <h1>Welcome to the Personnel Scheduler</h1>
            {userData && (
                <div>
                    <h2>Hello, {userData.name}</h2>
                    <AvailabilityForm />
                    <CalendarView />
                    <ShiftList />
                </div>
            )}
        </div>
    );
};

export default Dashboard;