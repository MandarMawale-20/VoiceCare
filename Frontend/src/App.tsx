import React, { useState, useEffect, useCallback, ReactNode, ChangeEvent } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Toaster, toast } from 'sonner';
import { Sun, Moon, Settings, LogOut, Mic, Send, Trash2, CheckCircle2, Circle, User as UserIcon, Bell, Home } from 'lucide-react';
import { format, parseISO, isToday, isTomorrow, compareAsc } from 'date-fns';

import { useAuth, AuthProvider } from './lib/auth'; // Assuming AuthProvider is exported if App is wrapped
import Login from './components/Login';
import Signup from './components/Signup';
import AddReminderForm from './components/AddReminderForm';
// import VoiceAssistant from './components/VoiceAssistant'; // Assuming this might be re-integrated or its parts used differently
import { ThemeProvider, useTheme } from './components/ThemeProvider';
import SettingsPage from './components/SettingsPage';

interface Reminder {
  id: string;
  text: string;
  datetime: string; // Or Date object, ensure consistency
  completed: boolean;
  userId?: string; // If applicable
}

interface User {
  id: string;
  email: string;
  // Add other user properties as needed
}

// Props for DashboardLayout
interface DashboardLayoutProps {
  children: ReactNode;
  onLogout: () => void;
  user: User | null;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, onLogout, user }) => {
  const { theme, setTheme } = useTheme();

  return (
    <div className={`flex h-screen bg-background text-foreground ${theme}`}>
      <aside className="w-64 bg-card p-6 flex flex-col justify-between border-r border-border">
        <div>
          <div className="flex items-center space-x-2 mb-10">
            <Bell className="h-8 w-8 text-primary" />
            <h1 className="text-2xl font-bold">VoiceCare</h1>
          </div>
          <nav className="space-y-2">
            <Link to="/" className="flex items-center space-x-3 text-muted-foreground hover:text-foreground hover:bg-muted p-2 rounded-lg transition-colors">
              <Home className="h-5 w-5" />
              <span>Dashboard</span>
            </Link>
            <Link to="/settings" className="flex items-center space-x-3 text-muted-foreground hover:text-foreground hover:bg-muted p-2 rounded-lg transition-colors">
              <Settings className="h-5 w-5" />
              <span>Settings</span>
            </Link>
          </nav>
        </div>
        <div className="space-y-2">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="w-full flex items-center space-x-3 text-muted-foreground hover:text-foreground hover:bg-muted p-2 rounded-lg transition-colors"
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            <span>Toggle Theme</span>
          </button>
          {user && (
            <div className="border-t border-border pt-4">
              <div className="flex items-center space-x-3 mb-2 p-2">
                <UserIcon className="h-5 w-5 text-muted-foreground" />
                <span className="text-sm">{user.email}</span>
              </div>
              <button
                onClick={onLogout}
                className="w-full flex items-center space-x-3 text-red-500 hover:text-red-400 hover:bg-red-500/10 p-2 rounded-lg transition-colors"
              >
                <LogOut className="h-5 w-5" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  );
};

// Props for ReminderCard
interface ReminderCardProps {
  reminder: Reminder;
  onComplete: (id: string) => void;
  onDelete: (id: string) => void;
}

const ReminderCard: React.FC<ReminderCardProps> = ({ reminder, onComplete, onDelete }) => {
  return (
    <div className={`p-4 rounded-lg shadow-md border ${reminder.completed ? 'bg-muted/50 border-dashed' : 'bg-card border-border'}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className={`text-lg font-semibold ${reminder.completed ? 'line-through text-muted-foreground' : 'text-foreground'}`}>
            {reminder.text}
          </p>
          <p className="text-sm text-muted-foreground">
            {format(new Date(reminder.datetime), "MMMM d, yyyy 'at' h:mm a")}
          </p>
        </div>
        <div className="flex space-x-2">
          {!reminder.completed && (
            <button onClick={() => onComplete(reminder.id)} className="p-1.5 text-green-500 hover:text-green-400 hover:bg-green-500/10 rounded">
              <CheckCircle2 size={20} />
            </button>
          )}
          <button onClick={() => onDelete(reminder.id)} className="p-1.5 text-red-500 hover:text-red-400 hover:bg-red-500/10 rounded">
            <Trash2 size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};


function App() {
  const { user, token, loading, logout } = useAuth();
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [processingCommand, setProcessingCommand] = useState(false);
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [showAddReminderForm, setShowAddReminderForm] = useState(false);

  const API_URL = 'http://localhost:5000/api';

  const fetchReminders = useCallback(async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/reminders`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch reminders');
      const data = await response.json();
      setReminders(data.reminders || []);
    } catch (error) {
      console.error('Fetch reminders error:', error);
      toast.error((error as Error).message || 'Could not load reminders.');
    }
  }, [token]);

  useEffect(() => {
    if (user && token) {
      fetchReminders();
    } else {
      setReminders([]); // Clear reminders if no user/token
    }
  }, [user, token, fetchReminders]);

  const sendVoiceCommandToBackend = async (transcript: string) => {
    if (!transcript.trim() || !token) return;
    setProcessingCommand(true);
    setLastResponse(null);
    try {
      const response = await fetch(`${API_URL}/voice-command`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ command: transcript }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Failed to process voice command');
      
      setLastResponse(data.response || "Command processed.");
      toast.success(data.response || "Command processed successfully!");

      if (data.action === 'add_reminder_form') {
        setShowAddReminderForm(true);
      } else if (data.action === 'list_reminders' || data.action === 'reminder_added' || data.action === 'reminder_updated' || data.action === 'reminder_deleted') {
        fetchReminders(); // Refresh reminders based on backend action
      }
      // Handle other actions as needed, e.g., navigation, UI changes
    } catch (error) {
      console.error('Voice command error:', error);
      setLastResponse((error as Error).message || 'Error processing command.');
      toast.error((error as Error).message || 'Failed to process voice command.');
    } finally {
      setProcessingCommand(false);
    }
  };
  
  const handleAddReminderSuccess = () => {
    setShowAddReminderForm(false);
    fetchReminders(); // Refresh reminders after adding a new one
    toast.success("Reminder added successfully!");
  };

  const handleCompleteReminder = async (id: string) => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/reminders/${id}/complete`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to complete reminder');
      fetchReminders();
      toast.success("Reminder marked as complete!");
    } catch (error) {
      console.error('Complete reminder error:', error);
      toast.error((error as Error).message || 'Could not complete reminder.');
    }
  };

  const handleDeleteReminder = async (id: string) => {
    if (!token) return;
    try {
      const response = await fetch(`${API_URL}/reminders/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to delete reminder');
      fetchReminders();
      toast.success("Reminder deleted!");
    } catch (error) {
      console.error('Delete reminder error:', error);
      toast.error((error as Error).message || 'Could not delete reminder.');
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <Router>
        <Toaster position="top-right" richColors />
        {!user ? (
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        ) : (
          <DashboardLayout onLogout={logout} user={user as User /* Cast if user type from useAuth is generic */}>
            <Routes>
              <Route path="/" element={
                <>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-3xl font-bold">Your Reminders</h2>
                    <button 
                      onClick={() => setShowAddReminderForm(true)}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-lg flex items-center space-x-2"
                    >
                      <Bell size={18}/> 
                      <span>Add Reminder</span>
                    </button>
                  </div>

                  {/* Voice Assistant Integration Point */}
                  {/* <VoiceAssistant onTranscript={sendVoiceCommandToBackend} processing={processingCommand} /> */}
                  {/* Placeholder for Voice Assistant UI - to be refined */}
                  <div className="my-4 p-4 bg-card border border-border rounded-lg shadow">
                     <h3 className="text-lg font-semibold mb-2">Voice Assistant</h3>
                     <p className="text-sm text-muted-foreground mb-1">Click the mic and speak your command.</p>
                     <button onClick={() => sendVoiceCommandToBackend("test command please list reminders")} disabled={processingCommand} className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-md mr-2">
                        {processingCommand ? 'Processing...' : <Mic size={18}/>}
                     </button>
                     {/* This is a mock button. Actual mic input needs useSpeechRecognition hook integration here or in a dedicated component */}
                     {lastResponse && <p className="mt-2 text-sm">Assistant: {lastResponse}</p>}
                  </div>


                  {showAddReminderForm && (
                    <AddReminderForm
                      onAddSuccess={handleAddReminderSuccess}
                      onCancel={() => setShowAddReminderForm(false)}
                      userId={user.id} // Pass userId if your AddReminderForm expects it
                      token={token} // Pass token if AddReminderForm makes its own API call
                    />
                  )}

                  {reminders.length === 0 && !showAddReminderForm && (
                    <p className="text-muted-foreground">No reminders yet. Add one or use voice commands!</p>
                  )}
                  <div className="space-y-4 mt-4">
                    {reminders.map((reminder: Reminder) => ( // Explicitly type reminder here
                      <ReminderCard
                        key={reminder.id}
                        reminder={reminder}
                        onComplete={handleCompleteReminder}
                        onDelete={handleDeleteReminder}
                      />
                    ))}
                  </div>
                </>
              } />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </DashboardLayout>
        )}
      </Router>
    </ThemeProvider>
  );
}

// Wrap App with AuthProvider if it's not done at a higher level (e.g., main.tsx)
// This depends on how AuthProvider is designed. If useAuth relies on context from AuthProvider,
// App or its parent needs to be wrapped.
const AppWithProviders = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default AppWithProviders; // Or export default App; if AuthProvider is in main.tsx