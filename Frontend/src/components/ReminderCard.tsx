import React from 'react';
import { Clock, Calendar, Check, Pill, CalendarClock, Bookmark } from 'lucide-react';
import { Reminder } from '../types';

interface ReminderCardProps {
  reminder: Reminder;
  onComplete: (id: string) => void;
}

const ReminderCard: React.FC<ReminderCardProps> = ({ reminder, onComplete }) => {
  const getCategoryIcon = () => {
    switch (reminder.category) {
      case 'medication':
        return <Pill className="text-blue-500" />;
      case 'appointment':
        return <CalendarClock className="text-purple-500" />;
      default:
        return <Bookmark className="text-green-500" />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 mb-4 border-l-4 ${
      reminder.category === 'medication' ? 'border-blue-500' :
      reminder.category === 'appointment' ? 'border-purple-500' : 'border-green-500'
    } ${reminder.completed ? 'opacity-60' : ''}`}>
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center mb-2">
            {getCategoryIcon()}
            <h3 className={`ml-2 text-lg font-semibold ${reminder.completed ? 'line-through text-gray-500' : ''}`}>
              {reminder.title}
            </h3>
          </div>
          {reminder.description && (
            <p className="text-gray-600 mb-3">{reminder.description}</p>
          )}
          <div className="flex items-center text-sm text-gray-500 space-x-4">
            <div className="flex items-center">
              <Calendar size={16} className="mr-1" />
              <span>{reminder.date}</span>
            </div>
            <div className="flex items-center">
              <Clock size={16} className="mr-1" />
              <span>{reminder.time}</span>
            </div>
          </div>
        </div>
        <button
          onClick={() => onComplete(reminder.id)}
          className={`p-2 rounded-full ${
            reminder.completed 
              ? 'bg-green-100 text-green-600' 
              : 'bg-gray-100 text-gray-500 hover:bg-green-100 hover:text-green-600'
          }`}
          aria-label={reminder.completed ? "Completed" : "Mark as completed"}
        >
          <Check size={20} />
        </button>
      </div>
    </div>
  );
};

export default ReminderCard;