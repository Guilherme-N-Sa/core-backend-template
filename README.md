# Django Application Template with AWS Infrastructure

A production-ready Django template with automated deployment to AWS, featuring Docker containerization, CI/CD workflows, and best practices for Python development.

## Features

- Django 5.0+ with REST framework
- PostgreSQL database integration
- Docker and Docker Compose setup for development and production
- GitHub Actions for CI/CD
- Automated semantic versioning based on branch names
- AWS infrastructure setup (ECR + Lightsail)
- OpenAI integration ready
- Code quality tools (Black, isort, flake8, pre-commit)
- Poetry for dependency management

## Quick Start

### Local Development

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Copy environment files:
   ```bash
   cp .env.example .env
   ```

3. Start the development environment:
   ```bash
   docker-compose -f docker-compose.local.yml up --build
   ```

The API will be available at `http://localhost:8000`

### Production Deployment

1. Configure GitHub repository secrets:
   ```
   AWS_ACCESS_KEY_ID          # AWS IAM access key with ECR and Lightsail permissions
   AWS_SECRET_ACCESS_KEY      # AWS IAM secret key
   AWS_REGION                 # AWS region (e.g., us-east-1)
   ECR_REPOSITORY             # ECR repository name (e.g., my-app/backend)
   ECR_REGISTRY               # ECR registry URL (e.g., {account}.dkr.ecr.{region}.amazonaws.com)
   LIGHTSAIL_USER             # Lightsail instance SSH user
   LIGHTSAIL_IP               # Lightsail instance public IP
   LIGHTSAIL_SSH_KEY          # SSH private key for Lightsail instance
   DOCKER_COMPOSE_FILE        # Docker compose file to use (e.g., docker-compose.dev.yml)
   ```

2. Configure environment variables in your Lightsail instance:
   ```
   POSTGRES_DB               # Database name
   POSTGRES_USER             # Database user
   POSTGRES_PASSWORD         # Database password
   SECRET_KEY                # Django secret key
   DEBUG                     # Set to 0 in production
   ALLOWED_HOSTS             # Comma-separated list of allowed hosts
   CSRF_TRUSTED_ORIGINS      # Comma-separated list of trusted origins
   OPENAI_API_KEY            # Optional: If using OpenAI integration
   ```

## Development Workflow

### Branch Naming Convention

The repository uses semantic versioning based on branch names:

- `major/*` or `breaking/*`: Breaking changes (1.0.0 → 2.0.0)
- `feature/*`, `minor/*`, or `chore/*`: New features (1.0.0 → 1.1.0)
- `fix/*`, `patch/*`, `hotfix/*`, `bugfix/*`, `dependency/*`, or `deps/*`: Bug fixes (1.0.0 → 1.0.1)

### Available Make Commands

```bash
make up              # Start development environment
make down            # Stop development environment
make build           # Build containers
make refresh         # Rebuild and restart containers
make bash-api        # Access API container shell
make psql            # Access PostgreSQL shell
make migrate         # Run database migrations
make django-shell    # Access Django shell
make test            # Run tests
make lint            # Run code quality checks
make logs            # View all container logs
make logs-api        # View API container logs
make logs-db         # View database container logs
```

## Project Structure

```
├── .github/workflows/    # GitHub Actions workflows
├── src/                 # Django project source code
│   ├── apps/           # Django applications
│   ├── core/           # Project settings and configuration
│   └── scripts/        # Utility scripts
├── docker-compose.local.yml  # Local development configuration
├── docker-compose.dev.yml    # Production configuration
├── Dockerfile          # Container definition
├── pyproject.toml      # Python dependencies and tools configuration
└── makefile           # Development utility commands
```

## API Documentation

The API is built using Django REST framework and includes:

- Authentication using Session Authentication
- Default pagination (10 items per page)
- Protected endpoints requiring authentication

Access the browsable API at `http://localhost:8000/api/`

## Contributing

1. Fork the repository
2. Create a new branch following the naming convention
3. Make your changes
4. Run tests and linting:
   ```bash
   make test && make lint
   ```
5. Submit a Pull Request

## License

MIT License

Copyright (c) 2024 Guilherme Niclewicz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Author

Created and maintained by [Guilherme Niclewicz](https://github.com/Guilherme-N-Sa)

If you find this project useful, please consider giving it a star ⭐️
