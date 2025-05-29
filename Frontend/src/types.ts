export interface Reminder {
  id: string;
  title: string;
  description?: string;
  time: string;
  date: string;
  completed: boolean;
  category: 'medication' | 'appointment' | 'general';
}