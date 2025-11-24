import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function seed() {
    // Seed users
    const user1 = await prisma.user.create({
        data: {
            username: 'manager1',
            password: 'password123',
            role: 'manager',
        },
    });

    const user2 = await prisma.user.create({
        data: {
            username: 'employee1',
            password: 'password123',
            role: 'employee',
        },
    });

    // Seed events
    const event1 = await prisma.event.create({
        data: {
            title: 'Team Meeting',
            description: 'Monthly team meeting to discuss project updates.',
            date: new Date('2023-10-15T10:00:00Z'),
            createdBy: user1.id,
        },
    });

    const event2 = await prisma.event.create({
        data: {
            title: 'Project Deadline',
            description: 'Final deadline for project submission.',
            date: new Date('2023-10-30T17:00:00Z'),
            createdBy: user1.id,
        },
    });

    console.log({ user1, user2, event1, event2 });
}

seed()
    .catch(e => {
        console.error(e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });