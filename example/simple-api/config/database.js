/**
 * Database configuration and connection management
 * @module database
 */

const mongoose = require('mongoose');
require('dotenv').config();

/**
 * MongoDB connection string from environment variables
 * @type {string}
 */
const MONGODB_URI = process.env.DB_URI || 'mongodb://localhost:27017/videoapi';

/**
 * Connects to MongoDB database
 * @async
 * @returns {Promise<void>}
 * @throws {Error} If connection fails
 */
async function connectDB() {
  try {
    const conn = await mongoose.connect(MONGODB_URI, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error('Database connection error:', error);
    process.exit(1);
  }
}

/**
 * Closes MongoDB database connection
 * @async
 * @returns {Promise<void>}
 */
async function closeDB() {
  try {
    await mongoose.connection.close();
    console.log('MongoDB connection closed');
  } catch (error) {
    console.error('Error closing database connection:', error);
  }
}

/**
 * Gets the current MongoDB connection instance
 * @returns {Connection} Mongoose connection instance
 */
function getConnection() {
  return mongoose.connection;
}

module.exports = {
  connectDB,
  closeDB,
  getConnection,
};
