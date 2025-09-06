const sqlite3 = require('sqlite3').verbose();
const path = require('path');

/**
 * Database class for managing SQLite connections and operations
 */
class Database {
  constructor() {
    this.dbPath = path.join(__dirname, 'todoapp.db');
    this.db = new sqlite3.Database(this.dbPath);
    this.init();
  }

  /**
   * Initialize database with required tables
   * @private
   */
  init() {
    const createTodosTable = `
      CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        completed BOOLEAN DEFAULT false,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`;

    this.db.run(createTodosTable, (err) => {
      if (err) {
        console.error('Error creating todos table:', err.message);
      } else {
        console.log('Todos table ready');
      }
    });
  }

  /**
   * Get all todos
   * @returns {Promise<Array>} Array of todo objects
   */
  async getAllTodos() {
    return new Promise((resolve, reject) => {
      const query = 'SELECT * FROM todos ORDER BY created_at DESC';
      this.db.all(query, [], (err, rows) => {
        if (err) {
          reject(err);
        } else {
          resolve(rows);
        }
      });
    });
  }

  /**
   * Get a todo by ID
   * @param {number} id - Todo ID
   * @returns {Promise<Object>} Todo object
   */
  async getTodoById(id) {
    return new Promise((resolve, reject) => {
      const query = 'SELECT * FROM todos WHERE id = ?';
      this.db.get(query, [id], (err, row) => {
        if (err) {
          reject(err);
        } else {
          resolve(row);
        }
      });
    });
  }

  /**
   * Create a new todo
   * @param {Object} todo - Todo data
   * @returns {Promise<Object>} Created todo object
   */
  async createTodo(todo) {
    return new Promise((resolve, reject) => {
      const query = `
        INSERT INTO todos (title, description, completed)
        VALUES (?, ?, ?)
      `;
      const params = [todo.title, todo.description || '', todo.completed || false];

      this.db.run(query, params, function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id: this.lastID, ...todo });
        }
      });
    });
  }

  /**
   * Update a todo
   * @param {number} id - Todo ID
   * @param {Object} todo - Todo data to update
   * @returns {Promise<Object>} Updated todo object
   */
  async updateTodo(id, todo) {
    return new Promise((resolve, reject) => {
      const query = `
        UPDATE todos
        SET title = ?, description = ?, completed = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
      `;
      const params = [todo.title, todo.description || '', todo.completed || false, id];

      this.db.run(query, params, function(err) {
        if (err) {
          reject(err);
        } else {
          resolve({ id, ...todo });
        }
      });
    });
  }

  /**
   * Delete a todo
   * @param {number} id - Todo ID
   * @returns {Promise<number>} Number of affected rows
   */
  async deleteTodo(id) {
    return new Promise((resolve, reject) => {
      const query = 'DELETE FROM todos WHERE id = ?';
      this.db.run(query, [id], function(err) {
        if (err) {
          reject(err);
        } else {
          resolve(this.changes);
        }
      });
    });
  }

  /**
   * Close database connection
   */
  close() {
    this.db.close((err) => {
      if (err) {
        console.error('Error closing database:', err.message);
      } else {
        console.log('Database connection closed');
      }
    });
  }
}

// Create database instance
const database = new Database();

/**
 * Connect to database - compatibility function for server.js
 * @returns {Promise<void>}
 */
async function connectToDatabase() {
  // Database is already connected in constructor, this is just a compatibility function
  return Promise.resolve();
}

// Export both the database instance and the connect function
module.exports = database;
module.exports.connectToDatabase = connectToDatabase;

// Export the database methods for use in routes
module.exports.getAllTodos = database.getAllTodos.bind(database);
module.exports.getTodoById = database.getTodoById.bind(database);
module.exports.createTodo = database.createTodo.bind(database);
module.exports.updateTodo = database.updateTodo.bind(database);
module.exports.deleteTodo = database.deleteTodo.bind(database);
