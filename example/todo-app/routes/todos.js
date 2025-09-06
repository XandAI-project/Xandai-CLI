const express = require('express');
const router = express.Router();
const {
  getAllTodos,
  getTodoById,
  createTodo,
  updateTodo,
  deleteTodo
} = require('../database');

/**
 * Get all todos
 * @route GET /todos
 * @returns {Array} - Array of todo objects
 */
router.get('/', async (req, res) => {
  try {
    const todos = await getAllTodos();
    res.json(todos);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch todos' });
  }
});

/**
 * Get a single todo by ID
 * @route GET /todos/:id
 * @param {string} id - Todo ID
 * @returns {Object} - Todo object
 */
router.get('/:id', async (req, res) => {
  try {
    const todo = await getTodoById(req.params.id);
    if (!todo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(todo);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch todo' });
  }
});

/**
 * Create a new todo
 * @route POST /todos
 * @param {Object} req.body - Todo data
 * @returns {Object} - Created todo object
 */
router.post('/', async (req, res) => {
  try {
    const newTodo = await createTodo(req.body);
    res.status(201).json(newTodo);
  } catch (error) {
    res.status(400).json({ error: 'Failed to create todo' });
  }
});

/**
 * Update a todo
 * @route PUT /todos/:id
 * @param {string} id - Todo ID
 * @param {Object} req.body - Updated todo data
 * @returns {Object} - Updated todo object
 */
router.put('/:id', async (req, res) => {
  try {
    const updatedTodo = await updateTodo(req.params.id, req.body);
    if (!updatedTodo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(updatedTodo);
  } catch (error) {
    res.status(400).json({ error: 'Failed to update todo' });
  }
});

/**
 * Delete a todo
 * @route DELETE /todos/:id
 * @param {string} id - Todo ID
 * @returns {Object} - Deletion confirmation
 */
router.delete('/:id', async (req, res) => {
  try {
    const deleted = await deleteTodo(req.params.id);
    if (!deleted) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json({ message: 'Todo deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete todo' });
  }
});

module.exports = router;
