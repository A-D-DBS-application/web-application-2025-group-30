import React, { useEffect, useState } from 'react';
import { getShifts } from '../api/client';

const ShiftList: React.FC = () => {
    const [shifts, setShifts] = useState([]);

    useEffect(() => {
        const fetchShifts = async () => {
            const data = await getShifts();
            setShifts(data);
        };

        fetchShifts();
    }, []);

    return (
        <div>
            <h2>Your Shifts</h2>
            <ul>
                {shifts.map((shift) => (
                    <li key={shift.id}>
                        {shift.date} - {shift.startTime} to {shift.endTime}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default ShiftList;