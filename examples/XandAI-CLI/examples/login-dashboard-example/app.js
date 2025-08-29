const express = require('express');
const bcrypt = require('bcrypt');
const session = require('express-session');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false
}));
app.use(express.static(path.join(__dirname, 'public')));

// Mock user database
const users = [];

// Routes

// Serve login page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'login.html'));
});

// Serve register page
app.get('/register', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'register.html'));
});

// Serve dashboard page
app.get('/dashboard', (req, res) => {
  if (!req.session.userId) {
    return res.redirect('/');
  }
  res.sendFile(path.join(__dirname, 'public', 'dashboard.html'));
});

// Register endpoint
app.post('/register', async (req, res) => {
  const { username, password } = req.body;
  
  // Check if user already exists
  const existingUser = users.find(user => user.username === username);
  if (existingUser) {
    return res.status(400).json({ error: 'Username already exists' });
  }
  
  // Hash password
  const hashedPassword = await bcrypt.hash(password, 10);
  
  // Save user
  const newUser = { id: users.length + 1, username, password: hashedPassword };
  users.push(newUser);
  
  res.status(201).json({ message: 'User registered successfully' });
});

// Login endpoint
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  
  // Find user
  const user = users.find(u => u.username === username);
  if (!user) {
    return res.status(400).json({ error: 'Invalid credentials' });
  }
  
  // Check password
  const validPassword = await bcrypt.compare(password, user.password);
  if (!validPassword) {
    return res.status(400).json({ error: 'Invalid credentials' });
  }
  
  // Set session
  req.session.userId = user.id;
  
  res.json({ message: 'Login successful', redirect: '/dashboard' });
});

// Logout endpoint
app.post('/logout', (req, res) => {
  req.session.destroy();
  res.json({ message: 'Logged out successfully' });
});

// Dashboard data endpoint
app.get('/api/dashboard-data', (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  // Mock dashboard data
  const dashboardData = {
    username: users.find(u => u.id === req.session.userId)?.username,
    stats: {
      totalTasks: 24,
      completedTasks: 18,
      pendingTasks: 6
    },
    recentActivity: [
      { id: 1, action: 'Task completed', time: '2 hours ago' },
      { id: 2, action: 'New task assigned', time: '5 hours ago' },
      { id: 3, action: 'Project updated', time: '1 day ago' }
    ]
  };
  
  res.json(dashboardData);
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});