/**
 * Main JavaScript file for the Todo application
 * Handles all client-side functionality including CRUD operations
 */

/**
 * Fetches todos from the server and renders them to the DOM
 * @returns {Promise<void>}
 */
async function fetchTodos() {
    try {
        const response = await fetch('/api/todos');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const todos = await response.json();
        renderTodos(todos);
    } catch (error) {
        console.error('Error fetching todos:', error);
        document.getElementById('todo-list').innerHTML = '<p>Error loading todos. Please try again.</p>';
    }
}

/**
 * Renders the list of todos to the DOM
 * @param {Array} todos - Array of todo objects
 */
function renderTodos(todos) {
    const todoList = document.getElementById('todo-list');
    if (!todoList) return;

    if (todos.length === 0) {
        todoList.innerHTML = '<p>No todos found. Add a new todo to get started!</p>';
        return;
    }

    todoList.innerHTML = todos.map(todo => `
        <div class="todo-item" data-id="${todo.id}">
            <span class="${todo.completed ? 'completed' : ''}">${todo.title}</span>
            <div class="todo-actions">
                <button class="toggle-btn" onclick="toggleTodo(${todo.id})">${todo.completed ? 'Undo' : 'Complete'}</button>
                <button class="delete-btn" onclick="deleteTodo(${todo.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

/**
 * Adds a new todo to the server
 * @param {string} text - The text of the new todo
 * @returns {Promise<void>}
 */
async function addTodo(text) {
    if (!text.trim()) return;

    try {
        const response = await fetch('/api/todos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: text, description: '', completed: false })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const newTodo = await response.json();
        fetchTodos(); // Refresh the todo list
        document.getElementById('todo-input').value = ''; // Clear input
    } catch (error) {
        console.error('Error adding todo:', error);
        alert('Failed to add todo. Please try again.');
    }
}

/**
 * Toggles the completion status of a todo
 * @param {number} id - The ID of the todo to toggle
 * @returns {Promise<void>}
 */
async function toggleTodo(id) {
    try {
        // First get the current todo to know its current completed status
        const getTodoResponse = await fetch(`/api/todos/${id}`);
        if (!getTodoResponse.ok) {
            throw new Error(`HTTP error! status: ${getTodoResponse.status}`);
        }
        const currentTodo = await getTodoResponse.json();

        // Toggle the completed status
        const response = await fetch(`/api/todos/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: currentTodo.title,
                description: currentTodo.description || '',
                completed: !currentTodo.completed
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        fetchTodos(); // Refresh the todo list
    } catch (error) {
        console.error('Error toggling todo:', error);
        alert('Failed to update todo. Please try again.');
    }
}

/**
 * Deletes a todo from the server
 * @param {number} id - The ID of the todo to delete
 * @returns {Promise<void>}
 */
async function deleteTodo(id) {
    if (!confirm('Are you sure you want to delete this todo?')) return;

    try {
        const response = await fetch(`/api/todos/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        fetchTodos(); // Refresh the todo list
    } catch (error) {
        console.error('Error deleting todo:', error);
        alert('Failed to delete todo. Please try again.');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Load todos on page load
    fetchTodos();

    // Handle form submission for adding new todos
    const form = document.getElementById('todo-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('todo-input');
            addTodo(input.value);
        });
    }

    // Allow adding todos with Enter key
    const input = document.getElementById('todo-input');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addTodo(input.value);
            }
        });
    }
});

// Expose functions to global scope for inline event handlers
window.toggleTodo = toggleTodo;
window.deleteTodo = deleteTodo;
