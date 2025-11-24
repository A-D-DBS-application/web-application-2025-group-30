import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './pages/Dashboard';
import ManagerPanel from './pages/ManagerPanel';
import CalendarView from './components/CalendarView';
import EventForm from './components/EventForm';
import AvailabilityForm from './components/AvailabilityForm';
import ShiftList from './components/ShiftList';
import './styles/globals.css';

const App: React.FC = () => {
  return (
    <Router>
      <Switch>
        <Route path="/" exact component={Login} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/manager" component={ManagerPanel} />
        <Route path="/calendar" component={CalendarView} />
        <Route path="/event-form" component={EventForm} />
        <Route path="/availability" component={AvailabilityForm} />
        <Route path="/shifts" component={ShiftList} />
      </Switch>
    </Router>
  );
};

export default App;