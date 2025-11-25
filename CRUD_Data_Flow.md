# CRUD Data Flow with SQLite

This document outlines the data flow for CRUD (Create, Read, Update, Delete) operations in a web application using SQLite database. The flow follows the pattern: Request → Route → Validation → Database Action → Response.

## Level 1 Data Flow Diagram (DFD)

```
+-------------+      +------------+      +--------------+      +-----------------+      +------------+
|             |      |            |      |              |      |                 |      |            |
|   Client    |----->|   Route    |----->|  Validation  |----->|  Database Layer |----->|  Response  |
|  (Browser)  |      |  (Flask)   |      |              |      |     (SQLite)    |      |   (JSON/   |
|             |<-----|            |<-----|              |<-----|                 |<-----|   HTML)    |
+-------------+      +------------+      +--------------+      +-----------------+      +------------+
```

## Detailed Data Flow

### 1. Request
- **Source**: Client (Browser, Mobile App, etc.)
- **Methods**:
  - `GET`: Retrieve data (Read)
  - `POST`: Create new data
  - `PUT/PATCH`: Update existing data
  - `DELETE`: Remove data
- **Data**: JSON, Form Data, URL Parameters

### 2. Route
- **Purpose**: Receives and routes the request to the appropriate handler
- **Components**:
  - URL Patterns (e.g., `/api/items`)
  - HTTP Methods (GET, POST, etc.)
  - Route Handlers (Controller functions)

### 3. Validation
- **Input Validation**:
  - Check required fields
  - Data type validation
  - Data format/sanitization
  - Business rules enforcement
- **Authentication/Authorization**:
  - Verify user credentials
  - Check permissions

### 4. Database Action (SQLite)

#### Create (INSERT)
```python
# Example using SQLite in Python
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    INSERT INTO items (name, description, created_at)
    VALUES (?, ?, ?)
''', (name, description, datetime.now()))
conn.commit()
```

#### Read (SELECT)
```python
# Retrieve all items
cursor.execute('SELECT * FROM items')
items = cursor.fetchall()

# Retrieve single item
cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
item = cursor.fetchone()
```

#### Update (UPDATE)
```python
cursor.execute('''
    UPDATE items 
    SET name = ?, description = ?, updated_at = ?
    WHERE id = ?
''', (new_name, new_description, datetime.now(), item_id))
conn.commit()
```

#### Delete (DELETE)
```python
cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
conn.commit()
```

### 5. Response
- **Success**:
  - 200 OK (for successful GET, PUT, DELETE)
  - 201 Created (for successful POST)
  - Response body with requested data or confirmation
- **Error**:
  - 400 Bad Request (validation failed)
  - 401 Unauthorized
  - 404 Not Found
  - 500 Internal Server Error

## Error Handling
- Database connection errors
- Constraint violations (e.g., unique constraints)
- Data validation failures
- Authentication/Authorization failures

## Security Considerations
- Use parameterized queries to prevent SQL injection
- Validate all user inputs
- Implement proper authentication and authorization
- Use HTTPS for all communications
- Sanitize data before displaying to users

## Performance Considerations
- Use transactions for multiple related operations
- Create appropriate indexes for frequently queried columns
- Close database connections properly
- Consider connection pooling for high-traffic applications

## Example Flow (Create Operation)

1. **Request**:
   ```
   POST /api/items
   Content-Type: application/json
   
   {
       "name": "New Item",
       "description": "A new item description"
   }
   ```

2. **Route Handling**:
   ```python
   @app.route('/api/items', methods=['POST'])
   def create_item():
       data = request.get_json()
       # Validation and processing continues...
   ```

3. **Database Action**:
   - Validate input data
   - Insert new record into SQLite
   - Return success/error response

4. **Response**:
   ```
   HTTP/1.1 201 Created
   Content-Type: application/json
   
   {
       "id": 1,
       "name": "New Item",
       "description": "A new item description",
       "created_at": "2025-11-25T06:37:00Z"
   }
   ```
