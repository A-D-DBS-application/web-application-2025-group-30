import { Availability } from '../models';
import { Request, Response } from 'express';

export const submitAvailability = async (req: Request, res: Response) => {
    const { userId, availableTimes } = req.body;

    try {
        const availability = new Availability({ userId, availableTimes });
        await availability.save();
        res.status(201).json({ message: 'Availability submitted successfully' });
    } catch (error) {
        res.status(500).json({ message: 'Error submitting availability', error });
    }
};

export const getAvailability = async (req: Request, res: Response) => {
    const { userId } = req.params;

    try {
        const availability = await Availability.find({ userId });
        res.status(200).json(availability);
    } catch (error) {
        res.status(500).json({ message: 'Error retrieving availability', error });
    }
};