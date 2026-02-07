# User Management Setup

## Initial User Creation

To create the initial admin user, use environment variables for security:

```bash
# Set environment variables
export INITIAL_USER_EMAIL="admin@yourdomain.com"
export INITIAL_USER_PASSWORD="your_secure_password"
export INITIAL_USER_FIRST_NAME="Your"
export INITIAL_USER_LAST_NAME="Name"

# Run the script
python scripts/create_initial_user.py
```

## Alternative: API Endpoint User Creation

For initial setup or development environments, you can also create users directly via the REST API.

### Prerequisites

- aiproxysrv server must be running (`python server.py` or via Docker)
- API accessible at `http://localhost:8000` (development) or your production URL

### Method 1: Using Swagger UI (Recommended for Development)

1. **Open Swagger UI:**
   - Development: `http://localhost:8000/docs`
   - Production: `https://your-domain/docs`

2. **Navigate to User Management:**
   - Find the `/api/v1/user/create` endpoint in the "User Authentication and Management" section
   - Click "Try it out"

3. **Fill in User Details:**
   ```json
   {
     "email": "admin@yourdomain.com",
     "password": "your_secure_password",
     "first_name": "Admin",
     "last_name": "User"
   }
   ```

4. **Execute Request:**
   - Click "Execute"
   - Check response for success confirmation

### Method 2: Using cURL

```bash
curl -X POST "http://localhost:8000/api/v1/user/create" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "your_secure_password",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

### Method 3: Using HTTP Client (Postman, Insomnia, etc.)

**URL:** `POST http://localhost:8000/api/v1/user/create`

**Headers:**
```
Content-Type: application/json
```

**Body (JSON):**
```json
{
  "email": "admin@yourdomain.com",
  "password": "your_secure_password",
  "first_name": "Admin",
  "last_name": "User"
}
```

### Expected Response

**Success (201):**
```json
{
  "success": true,
  "message": "User created successfully",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "admin@yourdomain.com"
}
```

**Error (400/409/500):**
```json
{
  "success": false,
  "error": "Email already exists"
}
```

### Important Notes

- ⚠️ **Development Only**: API user creation without authentication is intended for initial setup
- ⚠️ **Production Security**: In production with token authentication, only admin users can create new users
- 🔒 **Password Requirements**: Minimum 4 characters (consider longer passwords for security)
- 📧 **Email Validation**: Valid email format required
- 🚫 **Duplicate Prevention**: Email addresses must be unique

### Additional User Management Endpoints

Once you have created users, these endpoints are also available:

- `POST /api/v1/user/login` - User authentication
- `GET /api/v1/user/list` - List all users (admin only)
- `GET /api/v1/user/profile/{user_id}` - Get user profile
- `PUT /api/v1/user/edit/{user_id}` - Update user information
- `PUT /api/v1/user/password/{user_id}` - Change password
- `POST /api/v1/user/password-reset` - Admin password reset

### Security Notes

- **Never** hardcode credentials in source code
- Use strong passwords (minimum 8 characters, mixed case, numbers, symbols)
- Change default credentials immediately after first login
- Use environment variables or secure configuration management

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INITIAL_USER_EMAIL` | Yes | - | Admin user email address |
| `INITIAL_USER_PASSWORD` | Yes | - | Admin user password |
| `INITIAL_USER_FIRST_NAME` | No | "Admin" | User's first name |
| `INITIAL_USER_LAST_NAME` | No | "User" | User's last name |

### Example

```bash
# Create admin user
INITIAL_USER_EMAIL="admin@mycompany.com" \
INITIAL_USER_PASSWORD="MySecurePassword123!" \
INITIAL_USER_FIRST_NAME="System" \
INITIAL_USER_LAST_NAME="Administrator" \
python scripts/create_initial_user.py
```