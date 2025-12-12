# ModelReuseCLI 🤖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

A comprehensive CLI and API for evaluating the trustworthiness, quality, and reusability of pre-trained machine learning models, datasets, and code repositories. This tool helps developers make informed decisions about incorporating external ML artifacts into their projects.

## 🚀 Features

### Core Capabilities
- **Multi-Modal Analysis**: Evaluate models, datasets, and code repositories from various platforms
- **Comprehensive Scoring**: 10+ metrics including licensing, performance claims, code quality, and more
- **Platform Support**: GitHub, GitLab, Hugging Face Hub, and custom URLs
- **REST API**: Full-featured FastAPI backend with authentication and artifact management
- **Scalable Infrastructure**: AWS DynamoDB integration with Docker containerization

### Supported Metrics
- **📏 Size Score**: Platform compatibility analysis (Raspberry Pi, Jetson Nano, Desktop, AWS)
- **⚡ Performance Claims**: Evaluation of model performance documentation
- **📄 License Compliance**: Legal compatibility assessment with LGPLv2.1
- **🔧 Ramp-Up Time**: Learning curve and adoption difficulty
- **👥 Bus Factor**: Developer dependency risk analysis
- **🧪 Code Quality**: Static analysis and best practices evaluation
- **📊 Dataset Quality**: Data completeness and documentation assessment
- **🔗 Dataset-Code Matching**: Coherence between training data and implementation

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js** (for JavaScript analysis)
- **Docker** (for containerized deployment)
- **AWS Account** (for DynamoDB and deployment)

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ECE461ProjTeam/ModelReuseCLI.git
cd ModelReuseCLI
```

### 2. Install Dependencies
```bash
./run install
```

### 3. Environment Configuration
Create a `.env` file in the project root:

```bash
# Required: LLM API Configuration (choose one)
GEN_AI_STUDIO_API_KEY=your_purdue_genai_key    # Recommended
GEMINI_API_KEY=your_gemini_key                 # Alternative

# Optional: Enhanced Rate Limits
GITHUB_TOKEN=your_github_token
HF_TOKEN=your_huggingface_token

# AWS Configuration (for production deployment)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
```

## 🎯 Quick Start

### CLI Usage
Analyze a list of URLs from a file:
```bash
./run input.txt
```

**Input file format** (CSV):
```
https://github.com/user/repo,https://huggingface.co/datasets/data,https://huggingface.co/model
https://github.com/another/repo,,https://huggingface.co/another-model
```

### API Server
Start the FastAPI server:
```bash
python -m uvicorn apis.fast_api:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at: `http://localhost:8000/docs`

### Example API Usage
```python
import requests

# Register an artifact
response = requests.post("http://localhost:8000/artifacts", json={
    "queries": [{
        "name": "bert-base-uncased",
        "types": ["model"]
    }]
})

# Rate a model
model_id = response.json()["artifacts"][0]["id"]
rating = requests.get(f"http://localhost:8000/artifact/model/{model_id}/rate")
print(rating.json())
```

## 📊 Output Format

### CLI Output
```json
{
  "name": "bert-base-uncased",
  "category": "MODEL",
  "net_score": 0.75,
  "ramp_up_time": 0.8,
  "bus_factor": 0.6,
  "performance_claims": 0.9,
  "license": 1.0,
  "size_score": {
    "raspberry_pi": 0.52,
    "jetson_nano": 0.37,
    "desktop_pc": 0.30,
    "aws_server": 0.21
  },
  "code_quality": 0.85,
  "dataset_quality": 0.90
}
```

### Latency Metrics
All operations include timing information:
```json
{
  "net_score_latency": 15000,
  "ramp_up_time_latency": 2500,
  "license_latency": 8000
}
```

## 🏗️ Architecture

### Project Structure
```
ModelReuseCLI/
├── apis/                   # API layer
│   ├── fast_api.py        # FastAPI server
│   ├── gemini.py          # Gemini LLM integration
│   ├── purdue_genai.py    # Purdue GenAI integration
│   └── hf_client.py       # Hugging Face API client
├── metrics/               # Evaluation algorithms
│   ├── size_score.py      # Platform compatibility scoring
│   ├── license.py         # License compliance analysis
│   ├── performance_claims.py
│   └── ...
├── utils/                 # Utilities
│   ├── url_parser.py      # URL classification and parsing
│   ├── logger.py          # Logging configuration
│   └── env_check.py       # Environment validation
├── tests/                 # Test suite
├── model.py              # Data models
└── main.py               # CLI entry point
```

### Core Components
- **URL Parser**: Intelligent classification of GitHub, GitLab, and Hugging Face URLs
- **Metric Engine**: Parallel execution of evaluation algorithms
- **LLM Integration**: AI-powered analysis using Gemini or Purdue GenAI
- **Storage Layer**: DynamoDB for artifact persistence and caching
- **Authentication**: JWT-based API security with rate limiting

## 🧪 Testing

### Run Test Suite
```bash
# All tests
python -m pytest tests/

# Specific test categories
python -m pytest tests/test_metrics_separate.py    # Metric algorithms
python -m pytest tests/test_url_parser_integration.py  # URL parsing
python -m pytest tests/test_main.py               # CLI functionality
```

### Environment Testing
```bash
python -m pytest tests/test_environment.py
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build container
docker build -t modelreuse-api .

# Run with environment variables
docker run -p 8000:8000 --env-file .env modelreuse-api
```

### AWS ECS Deployment
The application is configured for AWS ECS with:
- **DynamoDB**: Artifact storage and caching
- **Secrets Manager**: Secure API key management
- **CloudWatch**: Logging and monitoring
- **Application Load Balancer**: Traffic distribution

See deployment documentation in `/docs` for detailed setup instructions.

## 📈 Performance & Scalability

- **Parallel Processing**: Metrics calculated concurrently for optimal performance
- **Caching**: DynamoDB caching reduces redundant API calls
- **Rate Limiting**: Built-in protection against API abuse
- **Async Operations**: FastAPI async/await for high concurrency

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Make your changes and add tests
5. Ensure all tests pass: `python -m pytest`
6. Submit a pull request

### Code Standards
- **Python**: PEP 8 compliance
- **Type Hints**: Required for all new code
- **Testing**: Minimum 80% code coverage
- **Documentation**: Docstrings for all public functions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Contributors

- **Mikhail Golovenchits** - Core Architecture
- **Vatsal Dudhaiya** - Metrics Implementation
- **Murad Ibrahimov** - API Development
- **Jake Scherer** - Testing & Quality Assurance
- **Yahya Quadri** - DevOps & Deployment
- **Emily Miller** - Frontend Integration
- **Logan Kay** - Structural Development
- **Noah Grzegorek** - AWS Integration

## 📚 Documentation

- **API Documentation**: Available at `/docs` when server is running
- **Architecture Guide**: `/docs/architecture.md`
- **Deployment Guide**: `/docs/deployment.md`
- **Contributing Guidelines**: `CONTRIBUTING.md`

## 🆘 Support

For questions, bug reports, or feature requests:
- **Issues**: [GitHub Issues](https://github.com/ECE461ProjTeam/ModelReuseCLI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ECE461ProjTeam/ModelReuseCLI/discussions)

---

**Made with ❤️ by the ECE 461 Project Team**