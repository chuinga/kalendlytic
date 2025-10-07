import { faker } from 'faker';
import axios from 'axios';

export interface TestUser {
  id: string;
  email: string;
  password: string;
  name: string;
  timezone: string;
  accessToken?: string;
  refreshToken?: string;
}

export interface TestCalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  attendees: string[];
  provider: 'google' | 'microsoft';
}

export class TestDataManager {
  private baseUrl: string;
  private testUsers: TestUser[] = [];
  private testEvents: TestCalendarEvent[] = [];

  constructor() {
    this.baseUrl = process.env.API_BASE_URL || 'https://api.example.com';
  }

  async initialize(): Promise<void> {
    console.log('Initializing test data manager...');
    // Verify API connectivity
    try {
      await axios.get(`${this.baseUrl}/health`);
    } catch (error) {
      console.warn('API health check failed, using mock data mode');
    }
  }

  async createTestUsers(): Promise<TestUser[]> {
    console.log('Creating test users...');
    
    const users: TestUser[] = [
      {
        id: 'test-user-1',
        email: 'test.user1@example.com',
        password: 'TestPassword123!',
        name: 'Test User One',
        timezone: 'America/New_York'
      },
      {
        id: 'test-user-2', 
        email: 'test.user2@example.com',
        password: 'TestPassword123!',
        name: 'Test User Two',
        timezone: 'America/Los_Angeles'
      },
      {
        id: 'test-admin',
        email: 'admin@example.com',
        password: 'AdminPassword123!',
        name: 'Test Admin',
        timezone: 'UTC'
      }
    ];

    // Create users in the system
    for (const user of users) {
      try {
        await this.createUser(user);
        this.testUsers.push(user);
      } catch (error) {
        console.error(`Failed to create user ${user.email}:`, error);
      }
    }

    return this.testUsers;
  }

  async createTestCalendarData(): Promise<TestCalendarEvent[]> {
    console.log('Creating test calendar data...');
    
    const events: TestCalendarEvent[] = [];
    const now = new Date();
    
    // Create various test scenarios
    for (let i = 0; i < 20; i++) {
      const startTime = new Date(now.getTime() + (i * 24 * 60 * 60 * 1000)); // i days from now
      const endTime = new Date(startTime.getTime() + (60 * 60 * 1000)); // 1 hour duration
      
      const event: TestCalendarEvent = {
        id: `test-event-${i}`,
        title: faker.company.catchPhrase(),
        start: startTime.toISOString(),
        end: endTime.toISOString(),
        attendees: [
          faker.internet.email(),
          faker.internet.email()
        ],
        provider: i % 2 === 0 ? 'google' : 'microsoft'
      };
      
      events.push(event);
    }

    // Create conflicting events for testing conflict resolution
    const conflictEvent1: TestCalendarEvent = {
      id: 'conflict-event-1',
      title: 'Important Meeting',
      start: new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000)).toISOString(),
      end: new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000) + (60 * 60 * 1000)).toISOString(),
      attendees: ['vip@company.com'],
      provider: 'google'
    };

    const conflictEvent2: TestCalendarEvent = {
      id: 'conflict-event-2', 
      title: 'Team Standup',
      start: new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000)).toISOString(),
      end: new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000) + (30 * 60 * 1000)).toISOString(),
      attendees: ['team@company.com'],
      provider: 'microsoft'
    };

    events.push(conflictEvent1, conflictEvent2);
    this.testEvents = events;

    return events;
  }

  async createLargeDataset(eventCount: number = 1000): Promise<TestCalendarEvent[]> {
    console.log(`Creating large dataset with ${eventCount} events...`);
    
    const events: TestCalendarEvent[] = [];
    const now = new Date();
    
    for (let i = 0; i < eventCount; i++) {
      const startTime = new Date(now.getTime() + (Math.random() * 365 * 24 * 60 * 60 * 1000)); // Random time within a year
      const duration = [30, 60, 90, 120][Math.floor(Math.random() * 4)] * 60 * 1000; // Random duration
      const endTime = new Date(startTime.getTime() + duration);
      
      const event: TestCalendarEvent = {
        id: `large-dataset-event-${i}`,
        title: faker.company.catchPhrase(),
        start: startTime.toISOString(),
        end: endTime.toISOString(),
        attendees: Array.from({ length: Math.floor(Math.random() * 5) + 1 }, () => faker.internet.email()),
        provider: Math.random() > 0.5 ? 'google' : 'microsoft'
      };
      
      events.push(event);
    }

    return events;
  }

  private async createUser(user: TestUser): Promise<void> {
    try {
      const response = await axios.post(`${this.baseUrl}/auth/register`, {
        email: user.email,
        password: user.password,
        name: user.name,
        timezone: user.timezone
      });
      
      if (response.data.accessToken) {
        user.accessToken = response.data.accessToken;
        user.refreshToken = response.data.refreshToken;
      }
    } catch (error) {
      // In test environment, we might not have a real API
      console.log(`Mock user creation for ${user.email}`);
    }
  }

  async cleanup(): Promise<void> {
    console.log('Cleaning up test data...');
    
    // Clean up test users
    for (const user of this.testUsers) {
      try {
        await axios.delete(`${this.baseUrl}/users/${user.id}`, {
          headers: { Authorization: `Bearer ${user.accessToken}` }
        });
      } catch (error) {
        console.log(`Mock cleanup for user ${user.email}`);
      }
    }

    // Clean up test events
    for (const event of this.testEvents) {
      try {
        await axios.delete(`${this.baseUrl}/events/${event.id}`);
      } catch (error) {
        console.log(`Mock cleanup for event ${event.id}`);
      }
    }

    this.testUsers = [];
    this.testEvents = [];
  }

  getTestUsers(): TestUser[] {
    return this.testUsers;
  }

  getTestEvents(): TestCalendarEvent[] {
    return this.testEvents;
  }

  getTestUser(email: string): TestUser | undefined {
    return this.testUsers.find(user => user.email === email);
  }
}