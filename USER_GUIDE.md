# IdeAgent: Semantic RAG Search User Guide

Welcome to the IdeAgent knowledge base! This system allows you to search across movies, characters, relationships, and songs using advanced natural language processing. Instead of relying on exact keyword matches, the system understands the *emotional intent* and *semantic meaning* of your query.

## 🚀 How to Run a Search

To run a search against the database, open a terminal in this directory, ensure your virtual environment is active, and run the `rag.py` module:

```bash
python -m pipeline.rag "Your natural language query goes here"
```

### 💡 Example Queries

The system excels at matching themes, emotions, and specific character dynamics across different types of media.

**Finding songs based on movies:**
```bash
python -m pipeline.rag "Find me a song that captures the emotional intensity of Interstellar"
```

**Finding movies based on songs:**
```bash
python -m pipeline.rag "What movies feel similar to Bohemian Rhapsody?"
```

**Exploring character dynamics:**
```bash
python -m pipeline.rag "Find characters with a moral conflict similar to The Joker"
```

**Abstract emotional queries:**
```bash
python -m pipeline.rag "I want a song about feeling completely isolated and lost in a big city"
```

## 🧠 How Agentic RAG Works Under the Hood

When you submit a query, the system executes a 5-step "Agentic" Retrieval-Augmented Generation (RAG) pipeline:

1. **Intent Extraction**: The Groq LLM analyzes your prompt to see if you are referencing a specific entity (like "Interstellar") and what you are looking for (like "songs").
2. **Context Retrieval**: If you referenced a specific entity, the script fetches its *Core Emotional Logic* directly from the Supabase database.
3. **Query Generation**: The LLM translates that emotional logic into a highly dense semantic search string optimized for our embedding model.
4. **Vector Search**: We convert that search string into a 768-dimension vector and use `pgvector` to run a Cosine Similarity search against the database to find the closest matches.
5. **Final Answer Formulation**: The top 5 results are fed back into the Groq LLM, which synthesizes a conversational, human-readable recommendation explaining exactly *why* the results match your query.

## 💿 Adding New Data

If you want to add new movies or songs to the system:
1. Open `data/batch.json` and add the entity to the corresponding list.
2. Run the batch enrichment pipeline:
   ```bash
   python -m pipeline.run_batch
   ```
   *(Note: This runs slowly on purpose to respect LLM token-per-minute rate limits).*
