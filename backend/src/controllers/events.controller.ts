import { Request, Response } from 'express';
import Event from '../models/index'; // Assuming Event model is defined in models/index.ts
import { validateEvent } from '../utils/validator'; // Assuming validation functions are defined in utils/validator.ts

export const createEvent = async (req: Request, res: Response) => {
    const { title, date, time, description } = req.body;

    const { error } = validateEvent(req.body);
    if (error) return res.status(400).send(error.details[0].message);

    try {
        const newEvent = new Event({ title, date, time, description });
        await newEvent.save();
        res.status(201).send(newEvent);
    } catch (err) {
        res.status(500).send('Server error');
    }
};

export const updateEvent = async (req: Request, res: Response) => {
    const { id } = req.params;
    const { title, date, time, description } = req.body;

    try {
        const updatedEvent = await Event.findByIdAndUpdate(id, { title, date, time, description }, { new: true });
        if (!updatedEvent) return res.status(404).send('Event not found');
        res.send(updatedEvent);
    } catch (err) {
        res.status(500).send('Server error');
    }
};

export const getEvents = async (req: Request, res: Response) => {
    try {
        const events = await Event.find();
        res.send(events);
    } catch (err) {
        res.status(500).send('Server error');
    }
};