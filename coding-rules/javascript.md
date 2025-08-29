# JavaScript Development Rules

## Code Style
- Use ES6+ features (const/let, arrow functions, destructuring)
- Use semicolons consistently
- Use single quotes for strings
- Use 2 spaces for indentation
- Use camelCase for variables and functions
- Use PascalCase for constructors and classes

## Modern JavaScript Features
- Prefer const over let, let over var
- Use arrow functions for short functions
- Use template literals for string interpolation
- Use destructuring for object and array assignments
- Use spread operator for array/object operations
- Use async/await over promises when possible

## Error Handling
- Always handle async operations with try-catch
- Use proper error types
- Log errors with context
- Validate function parameters
- Handle edge cases explicitly

## Function Design
- Keep functions small and focused
- Use pure functions when possible
- Avoid nested callbacks (callback hell)
- Use meaningful parameter names
- Return consistent data types

## Object and Array Operations
- Use array methods (map, filter, reduce) over loops
- Use Object.assign() or spread for object copying
- Avoid mutating original arrays/objects
- Use Set and Map for appropriate use cases

## Asynchronous Code
- Use async/await for asynchronous operations
- Handle promise rejections
- Use Promise.all() for concurrent operations
- Use proper error boundaries

## Performance
- Avoid global variables
- Use event delegation for event handling
- Minimize DOM manipulations
- Use debouncing for frequent events
- Lazy load resources when appropriate

## Testing
- Write unit tests for all functions
- Use Jest or similar testing framework
- Mock external dependencies
- Test edge cases and error conditions
- Maintain good test coverage

## Code Organization
- Use modules (import/export)
- Group related functionality
- Use consistent file naming
- Separate concerns (data, view, logic)
- Keep configuration separate

## Documentation
- Use JSDoc for function documentation
- Write clear comments for complex logic
- Document API interfaces
- Maintain up-to-date README
