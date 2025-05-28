import sqlite3

class Database:
    def __init__(self, db_file):
        """
        Initialize the database connection.
        :param db_file: File path for the SQLite database
        """
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """
        Create necessary tables for storing blockchain data.
        """
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY,
            index INTEGER,
            previous_hash TEXT,
            hash TEXT,
            data TEXT
        )
        """)
        self.connection.commit()

    def save_block(self, block):
        """
        Save a block to the database.
        :param block: Block object
        """
        self.cursor.execute("""
        INSERT INTO blocks (index, previous_hash, hash, data) 
        VALUES (?, ?, ?, ?)
        """, (block.index, block.previous_hash, block.hash, str(block.transactions)))
        self.connection.commit()

    def load_blocks(self):
        """
        Load all blocks from the database.
        """
        self.cursor.execute("SELECT * FROM blocks")
        return self.cursor.fetchall()