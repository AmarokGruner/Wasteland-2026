# 🔄 CI/CD Pipeline - GitHub Actions

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📁 Repository Struktur für CI/CD

```
Wasteland_neu/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Continuous Integration (jeder Push)
│       ├── cd.yml              # Continuous Deployment (auf master)
│       └── code-quality.yml    # Code Quality Checks (regelmäßig)
├── Dockerfile
├── docker-compose.yml
└── ...
```

---

## 🔄 CI Pipeline (ci.yml)

**Auslöser:** Jeder Push auf jeden Branch

```yaml
name: CI - Continuous Integration

on:
  push:
    branches: [ master, feature/*, fix/* ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.13
      uses: actions/setup-python@v5
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 mypy
    
    - name: Lint with Flake8
      run: |
        # Stop the build if there are Python syntax errors or undefined names
        flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
        # Exit-zero treats 100+ style errors as clean
        flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Type check with MyPy
      run: |
        mypy app/ --ignore-missing-imports
    
    - name: Run tests with pytest
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
```

---

## 🚀 CD Pipeline (cd.yml)

**Auslöser:** Merge auf master Branch

```yaml
name: CD - Continuous Deployment

on:
  push:
    branches: [ master ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          amarokgruner/wasteland:${{ github.sha }}
          amarokgruner/wasteland:latest
    
    - name: Deploy to server via SSH
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/wasteland
          docker pull amarokgruner/wasteland:${{ github.sha }}
          docker stop wasteland || true
          docker rm wasteland || true
          docker run -d \
            --name wasteland \
            -p 8011:8011 \
            -v /opt/wasteland/data:/app/data \
            --restart unless-stopped \
            amarokgruner/wasteland:${{ github.sha }}
          docker image prune -f
```

---

## 🔍 Code Quality Checks (code-quality.yml)

**Auslöser:** Täglich um 06:00 UTC + bei Push auf master

```yaml
name: Code Quality Checks

on:
  schedule:
    - cron: '0 6 * * *'  # Täglich um 06:00 UTC
  push:
    branches: [ master ]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.13
      uses: actions/setup-python@v5
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install bandit safety
    
    - name: Security scan with Bandit
      run: |
        bandit -r app/ -ll
    
    - name: Dependency check with Safety
      run: |
        safety check
    
    - name: Generate security report
      if: failure()
      run: |
        echo "Security issues found! Check logs for details."
```

---

## 🐳 Dockerfile

```dockerfile
# Multi-stage build for smaller image
FROM python:3.13-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.13-slim

WORKDIR /app

# Copy installed dependencies
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY seeds/ ./seeds/
COPY js/ ./js/
COPY *.html ./

# Create non-root user
RUN useradd -m wasteland && chown -R wasteland:wasteland /app
USER wasteland

# Expose port
EXPOSE 8011

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')" || exit 1

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011"]
```

---

## 📦 Docker Compose (Entwicklung)

```yaml
version: '3.8'

services:
  wasteland:
    build: .
    ports:
      - "8011:8011"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-in-production}
      - DATABASE_URL=sqlite:///./data/verbrannte_zone.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8011/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - wasteland
    restart: unless-stopped
```

---

## 🔐 GitHub Secrets Konfiguration

Folgende Secrets müssen im Repository konfiguriert werden:

| Secret | Beschreibung | Beispiel |
|--------|--------------|----------|
| `DOCKER_USERNAME` | Docker Hub Username | `amarokgruner` |
| `DOCKER_PASSWORD` | Docker Hub Password/Token | `ghp_xxx...` |
| `SERVER_HOST` | Server IP/Domain | `10.68.42.10` |
| `SERVER_USER` | SSH User | `fabian` |
| `SSH_PRIVATE_KEY` | SSH Private Key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SECRET_KEY` | JWT Secret Key (Production) | Zufällige 64+ Zeichen |

---

## 📊 Pipeline Status prüfen

```bash
# Letzte Pipeline-Ausführung auf GitHub ansehen
gh run list --repo AmarokGruner/Wasteland-2026

# Details einer spezifischen Pipeline
gh run view <run-id> --repo AmarokGruner/Wasteland-2026

# Logs einer Pipeline ansehen
gh run log <run-id> --repo AmarokGruner/Wasteland-2026
```

---

## 🎯 Best Practices

1. **Tests vor Merge:** Keine PR ohne bestandene Tests
2. **Code Coverage:** Mindestens 80% Testabdeckung anstreben
3. **Security Scans:** Regelmäßige Abhängigkeiten-Prüfung
4. **Docker Images:** Immer mit SHA-Tag versionen (`:abc123`)
5. **Rollback:** Alte Docker Images behalten für schnellen Rollback

---

**CI/CD Pipeline stellt sicher, dass jeder Code auf master testbar und deploybar ist!**
