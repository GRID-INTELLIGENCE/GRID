# Getting Started with Grid

This guide will help you get up and running with the Grid unified development environment.

## Prerequisites

- Python 3.9 or higher
- Git
- pip or poetry for package management

## Installation

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd grid
   ```

2. **Run the setup script**
   ```bash
   python scripts/setup.py
   ```

3. **Activate the virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate

   # Unix/macOS
   source venv/bin/activate
   ```

4. **Start the development server**
   ```bash
   python -m src.cli.main serve
   ```

5. **Visit the API documentation**
   Open http://localhost:8000/docs in your browser

### Manual Installation

If you prefer to set up manually:

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp config/.env.example .env
   # Edit .env with your configuration
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Configuration

### Environment Variables

The main configuration is handled through environment variables in the `.env` file:

```bash
# Application
APP_NAME="My Grid App"
ENVIRONMENT="development"

# Database
DATABASE__URL="sqlite:///./app.db"
DATABASE__ECHO=false

# API
API__HOST="0.0.0.0"
API__PORT=8000
API__DEBUG=true

# Security
SECURITY__SECRET_KEY="your-secret-key-here"
SECURITY__ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Setup

The framework supports multiple databases:

- **SQLite** (default): `sqlite:///./app.db`
- **PostgreSQL**: `postgresql://user:pass@localhost/dbname`
- **MySQL**: `mysql://user:pass@localhost/dbname`

To run migrations:
```bash
python -m src.cli.main migrate
```

## Development Workflow

### Common Commands

```bash
# Start development server
python -m src.cli.main serve

# Run tests
python -m src.cli.main test

# Code formatting
python -m src.cli.main lint --fix

# Interactive shell
python -m src.cli.main shell

# Application status
python -m src.cli.main status
```

### Using Make Commands

```bash
# Install dependencies
make install

# Run development workflow
make dev

# Build Docker image
make docker-build

# Run Docker container
make docker-run
```

## Project Structure

Understanding the project structure:

```
grid/
├── src/                    # Source code
│   ├── core/              # Core framework components
│   ├── api/               # FastAPI web layer
│   ├── cli/               # Command-line interface
│   ├── database/          # Database layer
│   ├── services/          # Business logic
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── config/                # Configuration files
├── docs/                  # Documentation
├── scripts/               # Utility scripts
├── examples/              # Example projects
├── templates/             # Project templates
└── .github/               # CI/CD workflows
```

## Next Steps

1. **Explore the examples**: Check out the `examples/` directory for sample projects
2. **Read the documentation**: Visit `docs/` for detailed guides
3. **Create your first project**: Use templates in `templates/` to scaffold new projects
4. **Configure your environment**: Update `.env` for your specific needs

## Getting Help

- Check the [API documentation](http://localhost:8000/docs) when the server is running
- Review the test files for usage examples
- Look at the examples directory for complete project samples
- Check the documentation in the `docs/` folder

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9  # Unix
   netstat -ano | findstr :8000   # Windows
   ```

2. **Database connection errors**
   - Check your DATABASE__URL in .env
   - Ensure database server is running
   - Run migrations: `python -m src.cli.main migrate`

3. **Import errors**
   - Ensure virtual environment is activated
   - Install dependencies: `pip install -r requirements.txt`
   - Check PYTHONPATH includes project root

### Debug Mode

Enable debug mode by setting in your `.env`:
```bash
API__DEBUG=true
ENVIRONMENT=development
```

This will provide:
- Detailed error messages
- Debug logging
- Auto-reload on code changes
