# AskDuka — Database, Ingestion & Vector Retrieval

AskDuka is an AI-powered WhatsApp business assistant designed to help businesses manage and query their business information through a conversational interface.

This README documents the work completed by **Member 2**, covering the database layer, document ingestion pipeline, chunking, embeddings, and vector retrieval foundation.

It also documents the development process, including problems encountered, approaches that were changed or removed, and the final implementation.

---

## Table of Contents

- [Member 2 Responsibility](#member-2-responsibility)
- [Final Architecture](#final-architecture)
- [Technology Stack](#technology-stack)
- [Local Development Setup](#local-development-setup)
- [Project Structure](#project-structure)
- [Database Layer](#database-layer)
- [Database Schema](#database-schema)
- [pgvector](#pgvector)
- [Document Ingestion](#document-ingestion)
- [Document Parsing](#document-parsing)
- [Text Chunking](#text-chunking)
- [Embeddings](#embeddings)
- [Document Embeddings](#document-embeddings)
- [Query Embeddings](#query-embeddings)
- [Embedding Validation](#embedding-validation)
- [Vector Retrieval](#vector-retrieval)
- [Repository Layer](#repository-layer)
- [Database Models](#database-models)
- [Migration System](#migration-system)
- [Development Journey](#development-journey)
- [Initial Embedding Approach](#initial-embedding-approach)
- [Why the Embedding Approach Changed](#why-the-embedding-approach-changed)
- [The 1024 → 384 Problem](#the-1024--384-problem)
- [Retrieval Test Failure](#retrieval-test-failure)
- [Embedding Test Failure](#embedding-test-failure)
- [Temporary OpenAI/Ollama Experiments](#temporary-openaiollama-experiments)
- [RAG Tests Removed](#rag-tests-removed)
- [Other Out-of-Scope Components](#other-out-of-scope-components)
- [Requirements Cleanup](#requirements-cleanup)
- [Configuration Cleanup](#configuration-cleanup)
- [Security and Configuration Cleanup](#security-and-configuration-cleanup)
- [Testing](#testing)
- [Final Test Result](#final-test-result)
- [Final Validation](#final-validation)
- [What Member 2 Delivers](#what-member-2-delivers)
- [What Is NOT Included](#what-is-not-included)
- [Lessons Learned](#lessons-learned)
- [Future Integration](#future-integration)
- [Final Status](#final-status)

---

# Member 2 Responsibility

Member 2 is responsible for the **data and retrieval foundation** of AskDuka.

The implemented responsibilities are:

1. PostgreSQL database setup
2. `pgvector` integration
3. SQLAlchemy database models
4. Database connection management
5. Repository/data-access layer
6. Database migrations
7. Document parsing
8. Text chunking
9. Local sentence-transformer embeddings
10. Vector storage
11. Vector similarity search
12. Retrieval tests
13. Ingestion pipeline tests

The goal was to provide the rest of the team with a reliable foundation from which later application layers can retrieve relevant business information.

---

# Final Architecture

The current Member 2 pipeline is:

```text
Business Document
       │
       ▼
    Parser
       │
       ▼
   Plain Text
       │
       ▼
    Chunker
       │
       ▼
 Document Chunks
       │
       ▼
Sentence Transformer
       │
       ▼
384-Dimensional Embeddings
       │
       ▼
PostgreSQL + pgvector
       │
       ▼
Vector Similarity Search
       │
       ▼
Relevant Document Chunks
```

The retrieval layer intentionally stops at returning relevant chunks.

LLM generation and final answer generation are handled by other members of the project.

---

# Technology Stack

| Component | Technology |
|---|---|
| Database Provider | Neon |
| Database | PostgreSQL |
| Vector Database | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| PostgreSQL Driver | `psycopg[binary]` |
| PDF Parsing | pypdf |
| Embeddings | Sentence Transformers |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimension | 384 |
| Numerical Processing | NumPy |
| Testing | pytest |
| Configuration | python-dotenv |
| Python | Python 3.12+ |

---

# Local Development Setup

## Requirements

Before running the project locally, make sure the following are installed:

- Python 3.12+
- Git
- Access to the team's shared Neon PostgreSQL database

---

## Clone the Repository

```bash
git clone https://github.com/nnamanimerit94/askduka.git
cd askduka
```

---

## Create and Activate a Virtual Environment

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

---

## Install Dependencies

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Then install the project itself in editable mode:

```bash
pip install -e .
```

Editable installation allows imports such as:

```python
from backend.app.db.models import ...
```

to work correctly when commands are run from the repository root.

---

## Environment Configuration

Create a local `.env` file:

```bash
touch .env
```

Add the database configuration provided by the project team:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

The project uses the team's shared **Neon PostgreSQL** database.

### Important

Do not commit `.env` to Git.

Do not share database credentials publicly.

The repository contains `.env.example` as a safe configuration template.

---

## Run Database Migration

Always run the migration from the repository root:

```bash
python database/run_migration.py
```

Expected output:

```text
Running migration: 001_initial_schema.sql
Completed: 001_initial_schema.sql
All migrations completed successfully.
```

---

## Run Tests

Run the complete test suite:

```bash
pytest -v
```

All tests should pass before submitting changes.

---

# Project Structure

```text
askduka/
│
├── backend/
│   ├── __init__.py
│   │
│   └── app/
│       ├── __init__.py
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── models.py
│       │   └── repository.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── chunker.py
│       │   ├── embeddings.py
│       │   ├── parser.py
│       │   └── service.py
│       │
│       └── retrieval.py
│
├── database/
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   │
│   └── run_migration.py
│
├── tests/
│   ├── fixtures/
│   │   ├── askduka_sample_catalog.pdf
│   │   └── sample_catalog.txt
│   │
│   ├── test_chunker.py
│   ├── test_database.py
│   ├── test_embeddings.py
│   ├── test_parser.py
│   ├── test_repository.py
│   ├── test_retrieval.py
│   ├── test_retrieval_service.py
│   └── test_service.py
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# Database Layer

The database uses PostgreSQL with the `pgvector` extension.

The database contains three main entities:

```text
businesses
     │
     ▼
documents
     │
     ▼
document_chunks
```

A business can have multiple documents.

A document can contain multiple chunks.

Each chunk can have an embedding that represents the semantic meaning of that chunk.

---

# Database Schema

## Businesses

The `businesses` table stores business information.

```sql
CREATE TABLE businesses (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Documents

The `documents` table stores uploaded business documents.

Important fields include:

- `business_id`
- `filename`
- `file_type`
- `status`
- timestamps

Each document belongs to a business.

The relationship is protected by a foreign key.

---

## Document Chunks

The `document_chunks` table stores smaller pieces of documents.

Each chunk contains:

- the document ID
- chunk index
- chunk text
- embedding
- metadata
- creation timestamp

The embedding column is:

```sql
embedding VECTOR(384)
```

A unique constraint prevents duplicate chunk indexes within the same document:

```sql
UNIQUE (document_id, chunk_index)
```

---

# pgvector

The PostgreSQL `vector` extension is enabled through:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

An HNSW index is also created for vector similarity search:

```sql
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks
    USING hnsw (embedding vector_cosine_ops);
```

This provides the database foundation for efficient semantic retrieval.

---

# Document Ingestion

The ingestion pipeline is responsible for transforming uploaded documents into searchable chunks.

The pipeline is:

```text
Input File
   │
   ▼
 Parser
   │
   ▼
Extracted Text
   │
   ▼
 Chunker
   │
   ▼
 Chunks
   │
   ▼
Embeddings
   │
   ▼
Database
```

The ingestion service coordinates these individual components.

---

# Document Parsing

The parser supports document text extraction.

PDF documents are handled using:

```text
pypdf
```

Plain text files can also be processed.

The purpose of the parser is to convert source documents into text before chunking.

This separation is important because parsing and chunking solve different problems:

- **Parser:** extracts text from the original document.
- **Chunker:** divides extracted text into manageable pieces.

---

# Text Chunking

Large documents should not be stored or embedded as one huge block of text.

The chunker divides extracted text into smaller pieces.

Each chunk receives an index:

```text
Chunk 0
Chunk 1
Chunk 2
Chunk 3
...
```

The chunk index is stored in the database so the original order can be preserved.

This makes it possible to retrieve relevant sections without processing an entire document every time.

---

# Embeddings

## Final Embedding Model

The project uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The model produces:

```text
384-dimensional embeddings
```

Therefore:

```text
Embedding Dimension = 384
```

This decision was made because the team wanted a solution that:

- runs locally
- does not require an external embedding API
- does not require an API key
- has no per-request embedding cost
- is simple to deploy
- is suitable for semantic retrieval

---

# Document Embeddings

Document chunks are converted into vectors using the model's document encoder.

Conceptually:

```text
"Jollof Rice - ₦2,500"
          │
          ▼
Sentence Transformer
          │
          ▼
[0.12, -0.03, 0.45, ... 384 values]
```

The resulting vector is stored alongside the chunk.

---

# Query Embeddings

When a user searches for something, the query is also converted into a 384-dimensional embedding.

For example:

```text
"How much is Jollof Rice?"
```

becomes a vector.

The query vector is then compared against stored document vectors.

This allows the system to search based on semantic similarity rather than requiring an exact text match.

---

# Embedding Validation

The implementation validates the expected embedding dimension.

A query embedding that does not contain exactly 384 values is rejected.

This protects the database from receiving vectors with the wrong dimensionality.

Empty queries are also rejected.

---

# Vector Retrieval

The retrieval layer uses PostgreSQL + pgvector to find the most semantically similar document chunks.

Cosine distance is used for comparison.

The repository performs the similarity calculation using pgvector:

```sql
1 - (dc.embedding <=> CAST(:query_embedding AS vector))
```

The result is treated as a similarity score.

Higher similarity means the stored chunk is more semantically related to the query.

---

# Repository Layer

The repository provides the data-access interface between application code and PostgreSQL.

It contains operations for:

- creating businesses
- creating documents
- creating document chunks
- retrieving businesses
- retrieving documents
- retrieving chunks
- updating document status
- performing vector similarity searches

This keeps database-specific operations separated from the rest of the application.

---

# Database Models

SQLAlchemy models represent the database tables in Python.

The main models are:

```text
Business
Document
DocumentChunk
```

The `DocumentChunk` model contains the vector field:

```text
VECTOR(384)
```

A small custom SQLAlchemy type is used to represent the PostgreSQL `pgvector` type without introducing unnecessary dependencies.

---

# Migration System

Database migrations are stored under:

```text
database/migrations/
```

The initial migration creates:

- the `vector` extension
- businesses table
- documents table
- document chunks table
- foreign keys
- constraints
- indexes

The migration runner:

```text
database/run_migration.py
```

loads SQL migration files and executes them against the configured PostgreSQL database.

The project uses a lightweight custom SQL migration runner rather than Alembic.

The initial migration was also made safe to execute repeatedly by using:

```sql
CREATE TABLE IF NOT EXISTS
```

and:

```sql
CREATE INDEX IF NOT EXISTS
```

This prevents the migration runner from failing simply because the initial database objects already exist.

---

# Development Journey

This implementation went through several iterations before reaching the final design.

The development process was not completely linear.

Several approaches were tested, problems were encountered, and some implementations were removed after the team clarified responsibilities.

Documenting this is important because the final code does not show every decision that happened during development.

---

# Initial Embedding Approach

The initial implementation used an external embedding provider.

The original approach used:

```text
Voyage AI
```

The initial embedding configuration used:

```text
1024 dimensions
```

The database therefore initially contained:

```text
VECTOR(1024)
```

This worked as an early experiment, but the team later decided that embeddings should use a local Sentence Transformer instead.

---

# Why the Embedding Approach Changed

The project moved away from the external embedding API because the team wanted:

- local embeddings
- no embedding API costs
- no external embedding API dependency
- simpler local development
- reproducible embeddings
- a known 384-dimensional vector format

The final model became:

```text
sentence-transformers/all-MiniLM-L6-v2
```

with:

```text
384 dimensions
```

---

# The 1024 → 384 Problem

Changing the embedding model introduced a database compatibility problem.

The existing database contained:

```text
VECTOR(1024)
```

while the new model generated:

```text
VECTOR(384)
```

These dimensions are not interchangeable.

The old test embeddings in the development database were removed, and the database column was changed to:

```text
VECTOR(384)
```

The schema was then aligned with the new embedding model.

This was an important lesson:

> The database vector dimension must always match the embedding model being used by the application.

---

# Retrieval Test Failure

After changing from 1024-dimensional vectors to 384-dimensional vectors, one of the retrieval tests initially failed.

The test fixture still contained 1024-dimensional vectors.

The problem was fixed by updating the test vectors to 384 dimensions.

For example:

```python
[1.0] + [0.0] * 383
```

represents a 384-dimensional vector.

After correcting the test data, the retrieval tests passed.

---

# Embedding Test Failure

The embedding tests also had to be updated when the implementation moved to Sentence Transformers.

The production implementation uses NumPy output before converting the result to Python lists.

The tests were therefore updated to use NumPy-based fake model outputs.

This allowed the tests to verify the application's behavior without repeatedly loading or executing the real model during every test case.

---

# Temporary OpenAI/Ollama Experiments

During development, temporary experiments were performed with:

```text
OpenAI
Ollama
```

These were used while exploring possible generation/RAG approaches.

They were not part of Member 2's final responsibility.

After the team clarified the separation of responsibilities, the temporary implementations were removed.

Removed temporary components included:

```text
backend/app/llm.py
backend/app/rag.py
test_openai_connection.py
test_rag_real.py
```

The associated LLM test was also removed.

This keeps the Member 2 branch focused on the database, ingestion, embedding, and retrieval foundation.

---

# RAG Tests Removed

The original test suite contained:

```text
tests/test_rag.py
```

That test depended on:

```python
from backend.app import rag
```

The `rag.py` implementation had already been removed because RAG orchestration belongs to another member.

Running the full test suite therefore produced:

```text
ImportError: cannot import name 'rag'
```

Instead of recreating `rag.py` simply to satisfy the test, the RAG test was removed from the Member 2 branch.

This preserved the team's separation of responsibilities.

---

# Other Out-of-Scope Components

The project also contained:

```text
context_builder.py
retrieval_filter.py
```

and their associated tests.

These components relate to higher-level retrieval/RAG orchestration rather than the database and vector retrieval foundation assigned to Member 2.

They were therefore removed from this branch.

The final Member 2 branch contains the lower-level retrieval functionality required by the rest of the application.

---

# Requirements Cleanup

The original dependency file contained dependencies from multiple experiments and project layers.

It included packages associated with:

- Voyage AI
- OpenAI
- Ollama-related experiments
- LangChain
- other temporary work

The dependency list was cleaned so that the Member 2 branch directly declares the dependencies needed for its implementation.

Final direct requirements:

```text
SQLAlchemy==2.0.52
psycopg[binary]==3.3.5
python-dotenv==1.2.3
pypdf==6.18.0
sentence-transformers==6.0.1
numpy==2.5.3
pytest==9.1.1
```

The `binary` extra for psycopg provides a packaged PostgreSQL client implementation, reducing the need for a separately installed system `libpq` dependency during local development.

There is one dependency file at the repository root:

```text
requirements.txt
```

The project does not maintain a separate backend requirements file.

---

# Configuration Cleanup

The original environment configuration contained settings related to the old embedding provider and temporary LLM experiments.

The example environment was cleaned.

The final `.env.example` contains:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

No real secrets are included.

The actual database credentials are kept only in the developer's local `.env` file.

The team uses the shared Neon PostgreSQL database.

---

# Security and Configuration Cleanup

The actual `.env` file contains local configuration and is intentionally excluded from Git.

The `.gitignore` includes:

```text
.env
.venv/
__pycache__/
.pytest_cache/
*.py[cod]
.coverage
.vscode/
```

This prevents local secrets and development artifacts from being committed.

During development, API credentials belonging to temporary experiments were exposed in a terminal output.

Those credentials should be considered compromised and must be revoked or rotated.

They are not included in the final project files.

---

# Testing

The Member 2 implementation contains tests for:

```text
Database connection
Parser
Chunker
Embeddings
Repository
Retrieval
Ingestion service
Retrieval service
```

Test fixtures include:

```text
tests/fixtures/sample_catalog.txt
tests/fixtures/askduka_sample_catalog.pdf
```

The PDF fixture was verified as a valid PDF document.

---

# Final Test Result

The complete test suite was executed using:

```bash
pytest -v
```

Final result:

```text
30 passed
```

This confirms that the current Member 2 implementation passes the complete test suite available in the branch.

---

# Final Validation

Before preparing the branch for the pull request, the following checks were performed.

## Old Embedding/Provider References

The repository was scanned for:

```text
voyage
openai
ollama
1024
VECTOR(1024)
```

No unwanted references remained in the Member 2 implementation, database, tests, requirements, or example environment.

---

## Tests

The complete test suite was executed using:

```bash
pytest -v
```

Result:

```text
30 passed
```

---

## Migration

The database migration was executed using:

```bash
python database/run_migration.py
```

Result:

```text
Running migration: 001_initial_schema.sql
Completed: 001_initial_schema.sql
All migrations completed successfully.
```

---

## Shared Neon Database Validation

The project was configured locally to use the team's shared Neon PostgreSQL database.

The database connection was verified successfully using:

```sql
SELECT 1;
```

The migration was then executed against the shared Neon database:

```bash
python database/run_migration.py
```

The complete test suite was subsequently executed against the Neon database:

```bash
pytest -v
```

Result:

```text
30 passed
```

This confirms that the current Member 2 implementation works successfully against the team's shared Neon PostgreSQL database.

---

## PDF Fixture

The sample PDF was checked and confirmed to be:

```text
PDF document, version 1.4, 1 page
```

---

# What Member 2 Delivers

The completed Member 2 contribution provides the project with:

```text
                 AskDuka
                    │
                    ▼
             Document Upload
                    │
                    ▼
                 Parser
                    │
                    ▼
                Chunker
                    │
                    ▼
          Sentence Transformer
                    │
                    ▼
              384-D Vector
                    │
                    ▼
          PostgreSQL + pgvector
                    │
                    ▼
          Semantic Vector Search
                    │
                    ▼
          Relevant Document Chunks
```

The output of the retrieval layer can then be consumed by the higher-level application/RAG layer owned by other team members.

---

# What Is NOT Included

The following are intentionally outside this Member 2 implementation:

- LLM generation
- Claude API integration
- OpenAI generation
- Ollama generation
- Prompt orchestration
- Final answer generation
- RAG response generation
- WhatsApp integration
- User interface
- Admin dashboard
- Authentication

These responsibilities belong to other parts of the project.

---

# Lessons Learned

## 1. Embedding Dimensions Matter

Changing an embedding model can require database changes.

If the model generates 384 dimensions, the database vector column must also support 384 dimensions.

---

## 2. Test Data Must Match Production Assumptions

A retrieval test using 1024-dimensional vectors is incompatible with a 384-dimensional production model.

Test fixtures must evolve with the implementation.

---

## 3. Local Embeddings Can Simplify Development

Using Sentence Transformers means embeddings can be generated locally without an external embedding API.

This reduces external dependencies and API costs.

---

## 4. Separation of Responsibilities Matters

It was tempting to keep RAG and LLM code inside the same branch simply because it interacted with retrieval.

However, separating:

```text
Database
Ingestion
Embeddings
Retrieval
```

from:

```text
RAG
LLM
Generation
```

makes team development cleaner.

---

## 5. Temporary Experiments Should Eventually Be Removed

During development, several approaches were tested.

Not every experiment belongs in the final implementation.

Removing abandoned experiments keeps the production code easier to understand and prevents unused dependencies from accumulating.

---

## 6. Database Migrations Should Be Treated Carefully

Database changes can affect existing data and application compatibility.

The vector-dimension change was handled carefully because existing embeddings were based on the old dimensionality.

Database migrations should always be considered together with the application code that consumes the database.

---

## 7. Database Provider Changes Should Be Validated

The team initially developed against a PostgreSQL-compatible environment and later standardized on Neon.

The implementation did not require code changes for the provider switch.

The local environment was updated to use the shared Neon PostgreSQL database, followed by:

```bash
python database/run_migration.py
```

and:

```bash
pytest -v
```

Both completed successfully.

This confirms that the database layer and retrieval foundation operate correctly against the team's shared database environment.

---

# Future Integration

Member 2's output is designed to be consumed by the rest of AskDuka.

A future higher-level flow can use:

```text
User Question
      │
      ▼
Query Embedding
      │
      ▼
Vector Retrieval
      │
      ▼
Relevant Chunks
      │
      ▼
RAG / Context Layer
      │
      ▼
LLM
      │
      ▼
Final Answer
```

Member 2 owns the foundation up to:

```text
Relevant Chunks
```

The remaining steps can be implemented independently by the appropriate team members.

---

# Final Status

**Member 2 implementation: COMPLETE**

## Completed

- [x] PostgreSQL database schema
- [x] Neon PostgreSQL integration
- [x] pgvector extension
- [x] SQLAlchemy models
- [x] Database connection
- [x] Repository layer
- [x] Database migration
- [x] PDF parsing
- [x] Text parsing
- [x] Text chunking
- [x] Sentence Transformer embeddings
- [x] 384-dimensional vectors
- [x] Vector storage
- [x] Cosine similarity retrieval
- [x] Retrieval tests
- [x] Ingestion tests
- [x] Embedding tests
- [x] Configuration cleanup
- [x] Dependency cleanup
- [x] Temporary LLM/RAG experiments removed
- [x] Out-of-scope tests removed
- [x] Security configuration cleanup
- [x] Shared Neon database validation
- [x] Full test suite passing

## Final Test Result

```text
30 passed
```

The Member 2 branch has been validated against the team's shared Neon PostgreSQL database and is ready for integration with the remaining AskDuka components.