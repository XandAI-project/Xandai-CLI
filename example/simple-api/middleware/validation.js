const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

/**
 * Authentication middleware to verify JWT tokens
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 * @returns {Object} Response with 401 status if token invalid
 */
const authentication = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'default_secret', (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
};

/**
 * Validation middleware for video creation
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 * @returns {Object} Response with 400 status if validation fails
 */
const validateVideoCreation = (req, res, next) => {
  const { title, views, likes } = req.body;

  // Check required fields
  if (!title || typeof title !== 'string' || title.trim() === '') {
    return res.status(400).json({
      error: 'Title is required and must be a non-empty string'
    });
  }

  if (views === undefined || typeof views !== 'number' || views < 0) {
    return res.status(400).json({
      error: 'Views are required and must be a non-negative number'
    });
  }

  if (likes === undefined || typeof likes !== 'number' || likes < 0) {
    return res.status(400).json({
      error: 'Likes are required and must be a non-negative number'
    });
  }

  next();
};

/**
 * Validation middleware for video updates
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 * @returns {Object} Response with 400 status if validation fails
 */
const validateVideoUpdate = (req, res, next) => {
  const { title, views, likes } = req.body;

  // Check if at least one field is provided for update
  if (!title && !views && !likes) {
    return res.status(400).json({
      error: 'At least one field (title, views, or likes) must be provided for update'
    });
  }

  // Validate title if provided
  if (title !== undefined && (typeof title !== 'string' || title.trim() === '')) {
    return res.status(400).json({
      error: 'Title must be a non-empty string if provided'
    });
  }

  // Validate views if provided
  if (views !== undefined && (typeof views !== 'number' || views < 0)) {
    return res.status(400).json({
      error: 'Views must be a non-negative number if provided'
    });
  }

  // Validate likes if provided
  if (likes !== undefined && (typeof likes !== 'number' || likes < 0)) {
    return res.status(400).json({
      error: 'Likes must be a non-negative number if provided'
    });
  }

  next();
};

/**
 * Error handling middleware
 * @param {Object} err - Error object
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 * @returns {Object} Response with error details
 */
const errorHandler = (err, req, res, next) => {
  console.error(err.stack);

  // Handle validation errors
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      error: 'Validation failed',
      details: err.message
    });
  }

  // Handle JWT errors
  if (err.name === 'JsonWebTokenError') {
    return res.status(401).json({
      error: 'Invalid token'
    });
  }

  // Default error response
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
};

module.exports = {
  authentication,
  validateVideoCreation,
  validateVideoUpdate,
  errorHandler
};
