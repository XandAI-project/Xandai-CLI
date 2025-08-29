# Flask Development Rules

## Project Structure
```
flask_app/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── utils/
├── migrations/
├── tests/
├── config.py
├── requirements.txt
└── run.py
```

## Application Factory Pattern
- Use application factory for creating Flask app
- Configure app based on environment
- Register blueprints in factory function
- Initialize extensions in factory

## Database
- Use Flask-SQLAlchemy for ORM
- Use Flask-Migrate for database migrations
- Define models in separate files
- Use relationship() for foreign keys

## Routes and Blueprints
- Use blueprints to organize routes
- Group related routes in blueprints
- Use descriptive route names
- Handle HTTP methods explicitly

## Templates
- Use Jinja2 templating engine
- Create base template for common elements
- Use template inheritance
- Escape user input to prevent XSS

## Security
- Use Flask-WTF for form handling and CSRF protection
- Validate all user input
- Use Flask-Login for user authentication
- Hash passwords with bcrypt or similar
- Use HTTPS in production

## Configuration
- Use environment variables for sensitive data
- Create separate config classes for different environments
- Use Flask-Migrate for database schema changes
- Store configuration in config.py

## Error Handling
- Create custom error pages (404, 500)
- Log errors appropriately
- Use try-catch for database operations
- Provide meaningful error messages

## Testing
- Use pytest for testing
- Test all routes and functions
- Use test database for testing
- Mock external dependencies

## Performance
- Use caching for expensive operations
- Optimize database queries
- Use pagination for large datasets
- Compress static files

## Deployment
- Use WSGI server (Gunicorn) for production
- Set up proper logging
- Use environment variables for configuration
- Implement health check endpoints
