// Express.js Routes Example
const express = require('express');
const router = express.Router();

// User routes
router.get('/api/users', (req, res) => {
  res.json({ message: 'Get all users' });
});

router.post('/api/users', (req, res) => {
  res.json({ message: 'Create user' });
});

router.get('/api/users/:id', (req, res) => {
  res.json({ message: 'Get user by ID' });
});

router.put('/api/users/:id', (req, res) => {
  res.json({ message: 'Update user' });
});

router.delete('/api/users/:id', (req, res) => {
  res.json({ message: 'Delete user' });
});

// Product routes
router.get('/api/products', (req, res) => {
  res.json({ message: 'Get all products' });
});

router.post('/api/products', (req, res) => {
  res.json({ message: 'Create product' });
});

// Order routes
router.get('/api/orders', (req, res) => {
  res.json({ message: 'Get all orders' });
});

router.post('/api/orders', (req, res) => {
  res.json({ message: 'Create order' });
});

module.exports = router;
