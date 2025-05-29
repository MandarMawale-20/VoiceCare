import { Reminder } from '../types';
import { format, parse, isToday, isTomorrow } from 'date-fns';

interface CommandProcessorProps {
  transcript: string;
  reminders: Reminder[];
  addReminder: (reminder: Omit<Reminder, 'id' | 'completed'>) => void;
  completeReminder: (id: string) => void;
  setShowAddForm: (show: boolean) => void;
}

interface CommandResult {
  response: string;
  action?: 'add' | 'complete' | 'list' | 'help';
}

export const processCommand = ({
  transcript,
  reminders,
  addReminder,
  completeReminder,
  setShowAddForm
}: CommandProcessorProps): CommandResult => {
  const text = transcript.toLowerCase().trim();
  
  // Only allow listing reminders, remove add/complete logic
  if (text.includes('what are my reminders') || text.includes('show my reminders') || text.includes('list reminders')) {
    let filteredReminders = reminders;
    let timeFrame = 'all';
    
    if (text.includes('today')) {
      filteredReminders = reminders.filter(r => isToday(parse(r.date, 'yyyy-MM-dd', new Date())));
      timeFrame = 'today';
    } else if (text.includes('tomorrow')) {
      filteredReminders = reminders.filter(r => isTomorrow(parse(r.date, 'yyyy-MM-dd', new Date())));
      timeFrame = 'tomorrow';
    }
    
    if (filteredReminders.length === 0) {
      return {
        response: `You don't have any reminders ${timeFrame === 'all' ? '' : 'for ' + timeFrame}.`,
        action: 'list'
      };
    }
    
    const reminderCount = filteredReminders.length;
    const reminderList = filteredReminders
      .slice(0, 3)
      .map(r => `${r.title} at ${r.time}`)
      .join(', ');
    
    const response = `You have ${reminderCount} reminder${reminderCount > 1 ? 's' : ''} ${timeFrame === 'all' ? '' : 'for ' + timeFrame}. ${
      reminderCount <= 3 
        ? `They are: ${reminderList}.` 
        : `The next few are: ${reminderList}.`
    }`;
    
    return {
      response,
      action: 'list'
    };
  }
  
  // Default response for unrecognized commands
  return {
    response: "I'm not sure what you want me to do. Try saying 'show my reminders for today' or 'list reminders for tomorrow'."
  };
};