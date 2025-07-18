"""Database connection management"""

import duckdb
from pathlib import Path
from typing import Optional
from .schema import initialize_schema


class DatabaseManager:
    """Manages DuckDB database connections"""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize database manager
        
        Args:
            db_path: Path to database file or ":memory:" for in-memory database
        """
        self.db_path = db_path
        self.connection: Optional[duckdb.DuckDBPyConnection] = None
    
    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection
        
        Returns:
            DuckDB connection object
        """
        if self.connection is None:
            self.connection = duckdb.connect(self.db_path)
        return self.connection
    
    def initialize_database(self) -> None:
        """Initialize database schema"""
        conn = self.get_connection()
        initialize_schema(conn)
    
    def close(self) -> None:
        """Close database connection"""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
    
    def __enter__(self) -> "DatabaseManager":
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager"""
        self.close()