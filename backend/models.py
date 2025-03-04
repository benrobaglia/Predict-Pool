import sqlite3
import json
from datetime import datetime
import config

def dict_factory(cursor, row):
    """Convert database row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = dict_factory
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        address TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create epochs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS epochs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        status TEXT
    )
    ''')
    
    # Create rounds table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epoch_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        starting_price REAL,
        ending_price REAL,
        status TEXT,
        FOREIGN KEY (epoch_id) REFERENCES epochs (id)
    )
    ''')
    
    # Create predictions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_address TEXT,
        round_id INTEGER,
        direction TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_correct BOOLEAN,
        FOREIGN KEY (user_address) REFERENCES users (address),
        FOREIGN KEY (round_id) REFERENCES rounds (id)
    )
    ''')
    
    # Create user_epoch_stats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_epoch_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_address TEXT,
        epoch_id INTEGER,
        correct_predictions INTEGER DEFAULT 0,
        total_predictions INTEGER DEFAULT 0,
        weight REAL DEFAULT 0,
        FOREIGN KEY (user_address) REFERENCES users (address),
        FOREIGN KEY (epoch_id) REFERENCES epochs (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize with an epoch and round if none exist
    if get_active_epoch() is None:
        now = datetime.now()
        from datetime import timedelta
        epoch_end = now + timedelta(days=config.EPOCH_DURATION_DAYS)
        epoch_id = create_epoch(
            now.strftime('%Y-%m-%d %H:%M:%S'),
            epoch_end.strftime('%Y-%m-%d %H:%M:%S'),
            'active'
        )
        
        # Create first round
        from datetime import timedelta
        round_end = now + timedelta(hours=config.ROUND_DURATION_HOURS)
        create_round(
            epoch_id,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            round_end.strftime('%Y-%m-%d %H:%M:%S'),
            0.0  # Will be updated by price fetcher
        )

# User functions
def create_user(address):
    """Create a new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT OR IGNORE INTO users (address) VALUES (?)',
            (address,)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_user(address):
    """Get user by address"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM users WHERE address = ?', (address,))
        return cursor.fetchone()
    finally:
        conn.close()

# Epoch functions
def create_epoch(start_time, end_time, status):
    """Create a new epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO epochs (start_time, end_time, status) VALUES (?, ?, ?)',
            (start_time, end_time, status)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_active_epoch():
    """Get the current active epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM epochs WHERE status = "active" ORDER BY id DESC LIMIT 1')
        return cursor.fetchone()
    finally:
        conn.close()

def get_epoch_by_id(epoch_id):
    """Get epoch by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM epochs WHERE id = ?', (epoch_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def update_epoch(epoch_id, data):
    """Update epoch data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        values = list(data.values())
        values.append(epoch_id)
        
        cursor.execute(
            f'UPDATE epochs SET {set_clause} WHERE id = ?',
            values
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

# Round functions
def create_round(epoch_id, start_time, end_time, starting_price):
    """Create a new round"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO rounds (epoch_id, start_time, end_time, starting_price, status) VALUES (?, ?, ?, ?, ?)',
            (epoch_id, start_time, end_time, starting_price, 'active')
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_active_round():
    """Get the current active round"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM rounds WHERE status = "active" ORDER BY id DESC LIMIT 1')
        return cursor.fetchone()
    finally:
        conn.close()

def get_round_by_id(round_id):
    """Get round by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM rounds WHERE id = ?', (round_id,))
        return cursor.fetchone()
    finally:
        conn.close()

def update_round(round_id, data):
    """Update round data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        values = list(data.values())
        values.append(round_id)
        
        cursor.execute(
            f'UPDATE rounds SET {set_clause} WHERE id = ?',
            values
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

# Prediction functions
def create_prediction(user_address, round_id, direction):
    """Create a new prediction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Ensure user exists
        create_user(user_address)
        
        # Get epoch_id for this round
        cursor.execute('SELECT epoch_id FROM rounds WHERE id = ?', (round_id,))
        round_data = cursor.fetchone()
        epoch_id = round_data['epoch_id']
        
        # Create prediction
        cursor.execute(
            'INSERT INTO predictions (user_address, round_id, direction) VALUES (?, ?, ?)',
            (user_address, round_id, direction)
        )
        prediction_id = cursor.lastrowid
        
        # Ensure user_epoch_stats entry exists
        cursor.execute(
            '''
            INSERT OR IGNORE INTO user_epoch_stats (user_address, epoch_id, correct_predictions, total_predictions)
            VALUES (?, ?, 0, 0)
            ''',
            (user_address, epoch_id)
        )
        
        # Increment total_predictions
        cursor.execute(
            '''
            UPDATE user_epoch_stats
            SET total_predictions = total_predictions + 1
            WHERE user_address = ? AND epoch_id = ?
            ''',
            (user_address, epoch_id)
        )
        
        conn.commit()
        return prediction_id
    finally:
        conn.close()

def evaluate_predictions(round_id, correct_direction):
    """Evaluate predictions for a round"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get epoch_id for this round
        cursor.execute('SELECT epoch_id FROM rounds WHERE id = ?', (round_id,))
        round_data = cursor.fetchone()
        epoch_id = round_data['epoch_id']
        
        # Mark predictions as correct/incorrect
        cursor.execute(
            '''
            UPDATE predictions
            SET is_correct = (direction = ?)
            WHERE round_id = ?
            ''',
            (correct_direction, round_id)
        )
        
        # Get all predictions for this round
        cursor.execute(
            '''
            SELECT user_address, is_correct
            FROM predictions
            WHERE round_id = ?
            ''',
            (round_id,)
        )
        predictions = cursor.fetchall()
        
        # Update user_epoch_stats for correct predictions
        for prediction in predictions:
            if prediction['is_correct']:
                cursor.execute(
                    '''
                    UPDATE user_epoch_stats
                    SET correct_predictions = correct_predictions + 1
                    WHERE user_address = ? AND epoch_id = ?
                    ''',
                    (prediction['user_address'], epoch_id)
                )
        
        conn.commit()
    finally:
        conn.close()

# Stats functions
def get_user_stats(user_address, epoch_id):
    """Get user stats for an epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            SELECT *
            FROM user_epoch_stats
            WHERE user_address = ? AND epoch_id = ?
            ''',
            (user_address, epoch_id)
        )
        stats = cursor.fetchone()
        
        if stats:
            # Calculate accuracy
            if stats['total_predictions'] > 0:
                stats['accuracy'] = stats['correct_predictions'] / stats['total_predictions']
            else:
                stats['accuracy'] = 0
        
        return stats
    finally:
        conn.close()

def get_user_epoch_stats(epoch_id):
    """Get all user stats for an epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            SELECT *
            FROM user_epoch_stats
            WHERE epoch_id = ?
            ''',
            (epoch_id,)
        )
        return cursor.fetchall()
    finally:
        conn.close()

def update_user_epoch_stats(stats_id, data):
    """Update user epoch stats"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
        values = list(data.values())
        values.append(stats_id)
        
        cursor.execute(
            f'UPDATE user_epoch_stats SET {set_clause} WHERE id = ?',
            values
        )
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def get_leaderboard(epoch_id):
    """Get leaderboard for an epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            SELECT user_address, correct_predictions, total_predictions, weight
            FROM user_epoch_stats
            WHERE epoch_id = ?
            ORDER BY correct_predictions DESC, total_predictions DESC
            ''',
            (epoch_id,)
        )
        leaderboard = cursor.fetchall()
        
        # Calculate accuracy for each entry
        for entry in leaderboard:
            if entry['total_predictions'] > 0:
                entry['accuracy'] = entry['correct_predictions'] / entry['total_predictions']
            else:
                entry['accuracy'] = 0
        
        return leaderboard
    finally:
        conn.close()
