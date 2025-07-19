"""Database schema definitions"""

import duckdb


def initialize_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Initialize database schema
    
    Args:
        conn: DuckDB connection object
    """
    # Create conversations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id VARCHAR PRIMARY KEY,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            topic VARCHAR,
            outcome VARCHAR,
            metadata JSON
        )
    """)
    
    # Create messages table with vector embeddings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id VARCHAR PRIMARY KEY,
            conversation_id VARCHAR,
            role VARCHAR,
            content TEXT,
            timestamp TIMESTAMP,
            metadata JSON,
            embedding FLOAT[384],  -- 384-dimensional embedding vector
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)
    
    # Create feedbacks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id VARCHAR PRIMARY KEY,
            conversation_id VARCHAR,
            message_id VARCHAR,
            feedback_type VARCHAR,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id),
            FOREIGN KEY (message_id) REFERENCES messages(id)
        )
    """)
    
    # Create analysis_results table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id VARCHAR PRIMARY KEY,
            conversation_id VARCHAR,
            analysis_type VARCHAR,
            findings JSON,
            recommendations JSON,
            confidence FLOAT,
            created_at TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)
    
    # Create indexes for performance
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_started_at 
        ON conversations(started_at)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
        ON messages(conversation_id)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
        ON messages(timestamp)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedbacks_conversation_id 
        ON feedbacks(conversation_id)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedbacks_type 
        ON feedbacks(feedback_type)
    """)
    
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_results_type 
        ON analysis_results(analysis_type)
    """)
    
    # Create vector index for embeddings (requires DuckDB extension)
    try:
        conn.execute("LOAD 'spatial';")
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_embedding 
            ON messages USING HNSW (embedding)
        """)
    except Exception:
        # HNSW index may not be available in all DuckDB versions
        pass
    
    conn.commit()