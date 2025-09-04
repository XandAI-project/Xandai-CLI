const express = require('express');
const router = express.Router();
const Todo = require('../models/todo');

/**
 * Get all todos
 * @route GET /todos
 * @returns {Array} - Array of todo objects
 */
router.get('/', async (req, res) => {
  try {
    const todos = await Todo.getAll();
    res.json(todos);
  } catch (error) {
    res.status(500).json({ error: error.message });
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
    const todo = await Todo.getById(req.params.id);
    if (!todo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(todo);
  } catch (error) {
    res.status(500).json({ error: error.message });
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
    const { title, completed = false } = req.body;
    if (!title) {
      return res.status(400).json({ error: 'Title is required' });
    }
    
    const newTodo = await Todo.create({ title, completed });
    res.status(201).json(newTodo);
  } catch (error) {
    res.status(500).json({ error: error.message });
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
    const { title, completed } = req.body;
    const updatedTodo = await Todo.update(req.params.id, { title, completed });
    if (!updatedTodo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(updatedTodo);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * Delete a todo
 * @route DELETE /todos/:id
 * @param {string} id - Todo ID
 * @returns {Object} - Deletion result
 */
router.delete('/:id', async (req, res) => {
  try {
    const deleted = await Todo.delete(req.params.id);
    if (!deleted) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json({ message: 'Todo deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;