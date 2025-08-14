# TechMart AI Assistant

A sophisticated enterprise-grade RAG (Retrieval-Augmented Generation) customer service system for electronics retail. Combines structured database queries with vector-based document retrieval to deliver intelligent, contextual responses in both Arabic and English with real-time streaming capabilities.

## Demo

<video controls width="720" style="max-width:100%; height:auto;">
  <source src="assets/Demo.mp4" type="video/mp4">
  Your browser doesn't support embedded videos. 
  Here’s a <a href="assets/demo.mp4">direct link</a>.
</video>


## Architecture Overview

This application implements a **hybrid RAG architecture** that intelligently combines multiple data sources:

- **Structured Data Retrieval**: Real-time product, service, and store information from PostgreSQL
- **Unstructured Data Search**: Document-based knowledge retrieval using Pinecone vector database
- **AI Generation**: GPT-4 powered response synthesis with streaming support
- **Multilingual Processing**: Native Arabic and English language detection and response generation

```mermaid
graph TB
    A[User Query] --> B[Language Detection]
    B --> C[Query Analysis & Intent Recognition]
    C --> D[Structured Data Query]
    C --> E[Vector Search]
    D --> F[PostgreSQL Database]
    E --> G[Pinecone Vector Store]
    F --> H[RAG Response Generator]
    G --> H
    H --> I[GPT-4 Synthesis]
    I --> J[Streaming Response]
    J --> K[Vue.js Frontend]
```

## Technology Stack

### Backend Infrastructure
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**: OpenAI GPT-4, OpenAI Embeddings (text-embedding-3-large)
- **Vector Database**: Pinecone (serverless, cosine similarity)
- **Traditional Database**: PostgreSQL 16+ with SQLAlchemy ORM
- **Caching**: Redis (session management, optional)
- **Document Processing**: PyPDF, LangChain text splitters

### Frontend Application
- **Framework**: Vue.js 3 with Composition API
- **Build Tool**: Vite
- **State Management**: Pinia
- **HTTP Client**: Axios with interceptors
- **Real-time Features**: Server-Sent Events (SSE) for streaming

### Infrastructure & DevOps
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: SQLAlchemy with Alembic
- **Environment Management**: python-dotenv
- **API Documentation**: FastAPI automatic OpenAPI/Swagger

## Key Features

### Advanced RAG Implementation
- **Hybrid Retrieval**: Combines structured database queries with vector similarity search
- **Intent Recognition**: GPT-4 powered query analysis and entity extraction
- **Context Fusion**: Intelligent merging of multiple data sources for comprehensive responses
- **Confidence Scoring**: Multi-factor confidence assessment based on data quality and retrieval success

### Real-time Streaming
- **Token-level Streaming**: Server-Sent Events (SSE) for real-time response generation
- **Progressive Enhancement**: Responses build progressively with typing indicators
- **Stream Error Handling**: Graceful fallback mechanisms for connection issues

### Multilingual Support
- **Language Detection**: Automatic Arabic/English detection with customizable thresholds
- **Bilingual Responses**: Context-aware language selection for responses
- **RTL Support**: Full right-to-left text support in frontend

### Enterprise Data Management
- **Product Catalog**: Complete inventory with specifications, pricing, and availability
- **Service Offerings**: Installation, support, and warranty services
- **Supplier Relations**: Supply chain and procurement information
- **Document Intelligence**: PDF ingestion with intelligent chunking and embedding

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- OpenAI API key
- Pinecone API key

### 1. Clone and Setup Environment
```bash
git clone <repository-url>
cd techmart-ai-assistant

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
```

### 2. Start Infrastructure Services
```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Wait for databases to be ready
sleep 10
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed database with sample data
python scripts/database/seed_database.py

# Start FastAPI server
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend/store-assistant-ui

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

## RAG System Components

### Query Processing Pipeline
1. **Language Detection**: Automatic Arabic/English identification
2. **Intent Analysis**: GPT-4 powered query understanding and entity extraction
3. **Dual Retrieval**: Parallel structured and unstructured data retrieval
4. **Response Synthesis**: Context-aware response generation with streaming

### Data Sources Integration
```python
# Structured data from PostgreSQL
products_found = await query_products(entities, intent, db)
services_found = await query_services(entities, db)
store_info = await query_store_info(db)

# Unstructured data from Pinecone
vector_results = await vector_service.search_similar(
    query_text=enhanced_query,
    top_k=max_results,
    filter_dict=metadata_filter
)

# Hybrid response generation
response = await generate_hybrid_response(
    structured_data, unstructured_data, query_analysis
)
```

### Vector Database Schema
- **Embedding Model**: OpenAI text-embedding-3-large (1024 dimensions)
- **Similarity Metric**: Cosine similarity
- **Metadata Fields**: source, language, category, document_type, chunk_index
- **Chunking Strategy**: RecursiveCharacterTextSplitter with overlap

## API Endpoints

### Chat Interface
```http
POST /channels/webchat/message
Content-Type: application/json

{
  "text": "What's the price of iPhone 15?",
  "session_id": "optional-session-id",
  "locale": "en"
}
```

### Streaming Chat
```http
POST /channels/webchat/message/stream
Content-Type: application/json

{
  "text": "Tell me about your products",
  "session_id": "optional-session-id", 
  "locale": "auto"
}
```

### Document Management
```http
POST /documents/upload
Content-Type: multipart/form-data

file: [PDF file]
```

## Database Schema

### Core Models
- **Products**: SKU, specifications, pricing, inventory
- **Services**: Installation, support, warranty offerings
- **Suppliers**: Vendor information and relationships
- **Documents**: Metadata for ingested documents
- **Conversations**: Chat history and analytics

### Sample Data
The system includes comprehensive sample data for a TechMart electronics store:
- 9 products across smartphones, laptops, home appliances
- 7 service offerings including installation and support
- 5 suppliers with realistic contact information
- Store location with operating hours and delivery zones

## Development & Testing

### Testing Scripts
```bash
# Test Pinecone integration
python scripts/testing/test_pinecone.py

# Test document ingestion
python scripts/testing/test_document_ingestion.py

# Test complete RAG pipeline
python scripts/testing/test_rag_service.py

# Test web chat functionality
python scripts/testing/test_web_chat.py
```

### Debug Tools
- **Arabic Language Debug**: `scripts/testing/debug_arabic.py`
- **RAG Step-by-Step Debug**: `scripts/testing/debug_rag_issue.py`
- **API Upload Testing**: `scripts/testing/test_upload_api.py`

## Configuration

### Environment Variables
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
MAX_TOKENS=4000

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_CLOUD=aws
PINECONE_REGION=us-east-1
PINECONE_INDEX=store-assistant
EMBED_DIM=1024

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/store_assistant
REDIS_URL=redis://localhost:6379/0

# RAG Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
SIMILARITY_THRESHOLD=0.75
```

### Docker Deployment
```bash
# Production deployment
docker-compose up -d

# Access services
# PostgreSQL: localhost:5432
# Redis: localhost:6379
# PgAdmin: localhost:5050
```

## Performance & Scalability

### Optimizations
- **Vector Search**: Pinecone serverless with auto-scaling
- **Database**: PostgreSQL with proper indexing on products and services
- **Caching**: Redis for session management and frequent queries
- **Streaming**: Chunked response delivery for improved UX

### Monitoring
- **Confidence Scoring**: Multi-factor assessment of response quality
- **Query Analytics**: Intent classification and response time tracking
- **Error Handling**: Graceful fallbacks with detailed logging

## Deployment

### Production Requirements
- **Compute**: 2+ CPU cores, 4GB+ RAM
- **Storage**: 20GB+ for databases and logs
- **Network**: HTTPS with proper CORS configuration
- **Monitoring**: Application logs and performance metrics

### Security Considerations
- **API Keys**: Secure storage of OpenAI and Pinecone credentials
- **Database**: Encrypted connections and proper access controls
- **CORS**: Configured for production domains
- **Rate Limiting**: Implemented at API gateway level

## Troubleshooting

### Common Issues
1. **Vector Search Returns No Results**
   - Check Pinecone index status and API credits
   - Verify embedding model consistency
   - Review similarity threshold settings

2. **Arabic Language Detection Issues**
   - Adjust language detection thresholds
   - Check system prompt Arabic content
   - Verify UTF-8 encoding support

3. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Check connection string format
   - Verify network accessibility

### Debug Commands
```bash
# Check system status
python scripts/testing/debug_rag_issue.py

# Test language detection
python scripts/testing/debug_arabic.py

# Validate API endpoints
python scripts/testing/test_webhook_fix.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
