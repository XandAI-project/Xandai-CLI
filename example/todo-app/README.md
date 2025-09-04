git clone <repository-url>
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables by copying `.env.example` to `.env` and configuring values as needed.

4. Start the server:
   ```bash
   npm start
   ```

## Usage

The API is available at `http://localhost:3000`.

### Example Requests

- **Get all todos**:
  ```bash
  curl http://localhost:3000/todos
  ```

- **Create a new todo**:
  ```bash
  curl -X POST http://localhost:3000/todos \
    -H "Content-Type: application/json" \
    -d '{"title": "New Todo", "completed": false}'
  ```

## API Endpoints

| Method | Endpoint         | Description              |
|--------|------------------|--------------------------|
| GET    | `/todos`         | Get all todos            |
| GET    | `/todos/:id`     | Get a specific todo      |
| POST   | `/todos`         | Create a new todo        |
| PUT    | `/todos/:id`     | Update a todo            |
| DELETE | `/todos/:id`     | Delete a todo            |

## Project Structure