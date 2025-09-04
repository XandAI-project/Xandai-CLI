/**
 * Todo model for managing todo items
 * @module TodoModel
 */

import { db } from '../database/db.js';

/**
 * Creates a new todo item
 * @param {Object} todoData - The todo data to create
 * @param {string} todoData.title - The title of the todo
 * @param {string} todoData.description - The description of the todo
 * @param {boolean} todoData.completed - The completion status of the todo
 * @returns {Promise<Object>} The created todo item
 */
export async function createTodo(todoData) {
  try {
    const query = `
      INSERT INTO todos (title, description, completed)
      VALUES (?, ?, ?)
      RETURNING *
    `;
    
    const values = [
      todoData.title,
      todoData.description || '',
      todoData.completed || false
    ];
    
    const result = await db.execute(query, values);
    return result.rows[0];
  } catch (error) {
    throw new Error(`Failed to create todo: ${error.message}`);
  }
}

/**
 * Gets all todo items
 * @returns {Promise<Array>} Array of todo items
 */
export async function getAllTodos() {
  try {
    const query = 'SELECT * FROM todos ORDER BY created_at DESC';
    const result = await db.execute(query);
    return result.rows;
  } catch (error) {
    throw new Error(`Failed to fetch todos: ${error.message}`);
  }
}

/**
 * Gets a todo item by ID
 * @param {number} id - The ID of the todo item
 * @returns {Promise<Object|null>} The todo item or null if not found
 */
export async function getTodoById(id) {
  try {
    const query = 'SELECT * FROM todos WHERE id = ?';
    const result = await db.execute(query, [id]);
    return result.rows[0] || null;
  } catch (error) {
    throw new Error(`Failed to fetch todo: ${error.message}`);
  }
}

/**
 * Updates a todo item
 * @param {number} id - The ID of the todo item
 * @param {Object} updateData - The data to update
 * @returns {Promise<Object|null>} The updated todo item or null if not found
 */
export async function updateTodo(id, updateData) {
  try {
    const fields = [];
    const values = [];
    
    if (updateData.title !== undefined) {
      fields.push('title = ?');
      values.push(updateData.title);
    }
    
    if (updateData.description !== undefined) {
      fields.push('description = ?');
      values.push(updateData.description);
    }
    
    if (updateData.completed !== undefined) {
      fields.push('completed = ?');
      values.push(updateData.completed);
    }
    
    if (fields.length === 0) {
      return null;
    }
    
    values.push(id);
    const query = `UPDATE todos SET ${fields.join(', ')} WHERE id = ? RETURNING *`;
    
    const result = await db.execute(query, values);
    return result.rows[0] || null;
  } catch (error) {
    throw new Error(`Failed to update todo: ${error.message}`);
  }
}

/**
 * Deletes a todo item
 * @param {number} id - The ID of the todo item
 * @returns {Promise<boolean>} True if deleted, false otherwise
 */
export async function deleteTodo(id) {
  try {
    const query = 'DELETE FROM todos WHERE id = ? RETURNING id';
    const result = await db.execute(query, [id]);
    return result.rows.length > 0;
  } catch (error) {
    throw new Error(`Failed to delete todo: ${error.message}`);
  }
}