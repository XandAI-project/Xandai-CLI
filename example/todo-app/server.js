const express = require('express');
const path = require('path');
const todoRoutes = require('./routes/todos');
const { connectToDatabase } = require('./database');

/**
 * Express application instance
 * @type {import('express').Application}
 */
const app = express();

/**
 * Start the server on specified port
 * @param {number} port - Port number to listen on
 * @returns {Promise<void>}
 */
async function startServer(port = 3000) {
  try {
    // Connect to database
    await connectToDatabase();

    // Setup middleware and routes
    setupMiddleware(app);
    setupRoutes(app);

    // Start server
    app.listen(port, () => {
      console.log(`Server running on http://localhost:${port}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

/**
 * Setup middleware for the application
 * @param {import('express').Application} app - Express application instance
 * @returns {void}
 */
function setupMiddleware(app) {
  // Parse JSON bodies
  app.use(express.json());

  // Serve static files from public directory
  app.use(express.static(path.join(__dirname, 'public')));

  // Parse URL-encoded bodies
  app.use(express.urlencoded({ extended: true }));
}

/**
 * Setup routes for the application
 * @param {import('express').Application} app - Express application instance
 * @returns {void}
 */
function setupRoutes(app) {
  // API routes
  app.use('/api/todos', todoRoutes);

  // Serve index.html for all other routes (for SPA)
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
  });
}

// Export the app instance for testing or external use
module.exports = { app, startServer, setupMiddleware, setupRoutes };

// Start the server if this file is run directly
if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  startServer(PORT);
}
