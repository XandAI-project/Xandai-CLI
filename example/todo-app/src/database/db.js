/**
 * Database configuration and connection setup
 * @module database
 */

import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

/**
 * Opens a connection to the SQLite database
 * @returns {Promise<sqlite.Database>} A promise that resolves to the database instance
 */
export async function getDatabase() {
  const db = await open({
    filename: './database.sqlite',
    driver: sqlite3.Database
  });

  // Initialize database schema if it doesn't exist
  await db.exec(`
    CREATE TABLE IF NOT EXISTS todos (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      completed BOOLEAN DEFAULT FALSE,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  return db;
}

/**
 * Closes the database connection
 * @param {sqlite.Database} db - The database instance to close
 * @returns {Promise<void>}
 */
export async function closeDatabase(db) {
  if (db) {
    await db.close();
  }
}