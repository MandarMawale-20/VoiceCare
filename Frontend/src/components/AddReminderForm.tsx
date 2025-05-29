import React, { useState } from 'react';
import { Plus, X } from 'lucide-react';
import { Reminder } from '../types';
import { format } from 'date-fns';

interface AddReminderFormProps {
  onAdd: (reminder: Omit<Reminder, 'id' | 'completed'>) => void;
  onClose: () => void;
}

const AddReminderForm: React.FC<AddReminderFormProps> = ({ onAdd, onClose }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [time, setTime] = useState(format(new Date(), 'HH:mm'));
  const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [category, setCategory] = useState<'medication' | 'appointment' | 'general'>('general');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    // Call your backend API to add a reminder
    try {
      await fetch('http://localhost:5000/api/reminders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, time, date, category })
      });
      // Optionally, show a success message here
    } catch (error) {
      // Optionally, show an error message here
      console.error('Failed to add reminder:', error);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Add New Reminder</h2>
          <button 
            onClick={onClose}
            className="p-1 rounded-full hover:bg-gray-200"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Take medication"
              required
            />
          </div>
          
          <div className="mb-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Take 2 pills with water"
              rows={2}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-1">
                Date
              </label>
              <input
                type="date"
                id="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label htmlFor="time" className="block text-sm font-medium text-gray-700 mb-1">
                Time
              </label>
              <input
                type="time"
                id="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setCategory('medication')}
                className={`p-2 rounded-md text-center ${
                  category === 'medication' 
                    ? 'bg-blue-100 text-blue-700 border-2 border-blue-500' 
                    : 'bg-gray-100 hover:bg-blue-50'
                }`}
              >
                Medication
              </button>
              <button
                type="button"
                onClick={() => setCategory('appointment')}
                className={`p-2 rounded-md text-center ${
                  category === 'appointment' 
                    ? 'bg-purple-100 text-purple-700 border-2 border-purple-500' 
                    : 'bg-gray-100 hover:bg-purple-50'
                }`}
              >
                Appointment
              </button>
              <button
                type="button"
                onClick={() => setCategory('general')}
                className={`p-2 rounded-md text-center ${
                  category === 'general' 
                    ? 'bg-green-100 text-green-700 border-2 border-green-500' 
                    : 'bg-gray-100 hover:bg-green-50'
                }`}
              >
                General
              </button>
            </div>
          </div>
          
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-4 rounded-md hover:from-blue-700 hover:to-purple-700 flex items-center justify-center"
          >
            <Plus size={20} className="mr-1" />
            Add Reminder
          </button>
        </form>
      </div>
    </div>
  );
};

export default AddReminderForm;