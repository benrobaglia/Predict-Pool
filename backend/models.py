import sqlite3
import json
import logging
from datetime import datetime, timedelta, timezone
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        start_time TIMESTAMP UNIQUE,
        end_time TIMESTAMP,
        lock_start TIMESTAMP,
        lock_end TIMESTAMP,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Adding trigger to make sure that we won't have more than one locked, active, calculating at the time 
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS enforce_uniqueness_epochs
    BEFORE UPDATE ON epochs
    FOR EACH ROW
    WHEN NEW.status IN ('active', 'locked', 'calculating')
    BEGIN
        SELECT RAISE(ABORT, 'Only one round can have status active, calculating, locked')
        FROM epochs
        WHERE status = NEW.status AND id != NEW.id;
    END
    ''')

    # Adding trigger that updates updated_at on row update
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_epochs_timestamp
    AFTER UPDATE ON epochs
    FOR EACH ROW
    BEGIN
        UPDATE epochs SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END
    ''')

    # Create rounds table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        epoch_id INTEGER,
        start_time TIMESTAMP UNIQUE,
        end_time TIMESTAMP,
        lock_start TIMESTAMP,
        lock_end TIMESTAMP,
        starting_price REAL,
        ending_price REAL,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (epoch_id) REFERENCES epochs (id)
    )
    ''')

    # Adding trigger to make sure that we won't have more than one round active, locked or calculating at the time 
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS enforce_uniqueness_rounds
    BEFORE UPDATE ON roundsatetime.now()
        WHERE status = NEW.status AND id != NEW.id;
    END
    ''')

    # Adding trigger that updates updated_at on row update
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_rounds_timestamp
    AFTER UPDATE ON rounds
    FOR EACH ROW
    BEGIN
        UPDATE rounds SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END
    ''')

    # Create user epoch table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_epoch (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_address TEXT,
        epoch_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_address) REFERENCES users (address),
        FOREIGN KEY (epoch_id) REFERENCES epochs (id),
        UNIQUE (user_address, epoch_id)
    )
    ''')

    # Adding trigger that updates updated_at on row update
    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS update_user_epoch_timestamp
    AFTER UPDATE ON user_epoch
    FOR EACH ROW
    BEGIN
        UPDATE user_epoch SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
    END
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

    generate_epochs_and_rounds()
        

def generate_epochs_and_rounds():
    logger.info("Generating future epochs and rounds")
    epochs = []
    num_epochs = int(24*60*60/config.EPOCH_DURATION_SECONDS) #calculating number of epochs to be enough for 36 hours
    current_start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    for _ in range(num_epochs):
        epoch_end_time = current_start_time + timedelta(seconds=config.EPOCH_DURATION_SECONDS)

        lock_start_time = current_start_time - timedelta(seconds=config.EPOCH_LOCK_SECONDS)
        lock_end_time = current_start_time
            
        epochs.append((
            current_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            epoch_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            lock_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            lock_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled'
        ))
        current_start_time = epoch_end_time
    
    logger.info(f"Generated {len(epochs)} epochs")
    for epoch in epochs:
        epoch_id = insert_epoch(epoch[0],epoch[1],epoch[2],epoch[3],epoch[4])
        if epoch_id != 0:
            round_starts = datetime.strptime(epoch[0], "%Y-%m-%d %H:%M:%S") # epoch_start
            epoch_end = datetime.strptime(epoch[1], "%Y-%m-%d %H:%M:%S")
            round_duration = timedelta(seconds=config.EPOCH_DURATION_SECONDS//config.ROUNDS_COUNT)
            rounds = [] 
            for i in range(config.ROUNDS_COUNT):
                lockdown_start_seconds = int(round_duration.total_seconds() * (1-config.ROUND_LOCK_PERCENTAGE)) 
                lockdown_start = round_starts + timedelta(seconds=lockdown_start_seconds)
                
                lockdown_end = round_starts + round_duration  # Lockdown ends when the round ends
                
                round_end = lockdown_start
                
                # If it's the last round, ensure it ends at epoch_ends
                if i == config.ROUNDS_COUNT - 1:
                    lockdown_end = epoch_end

                rounds.append((
                    epoch_id,
                    round_starts.strftime('%Y-%m-%d %H:%M:%S'),
                    round_end.strftime('%Y-%m-%d %H:%M:%S'),
                    lockdown_start.strftime('%Y-%m-%d %H:%M:%S'),
                    lockdown_end.strftime('%Y-%m-%d %H:%M:%S'),
                    0,
                    0,
                    'scheduled'
                ))

                round_starts = lockdown_end 
            logger.info(f"For epoch {epoch_id} generated {len(rounds)} rounds")
            insert_rounds(rounds)


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

def insert_epoch(start_time, end_time, lock_start, lock_end, status):
    """Insert epoch, ignoring conflicts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO epochs (start_time, end_time, lock_start, lock_end, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(start_time) DO NOTHING
            """,
            (start_time, end_time, lock_start, lock_end, status)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def insert_rounds(rounds_data):
    """Insert rounds"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.executemany(
            'INSERT INTO rounds (epoch_id, start_time, end_time, lock_start, lock_end, starting_price, ending_price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            rounds_data
        )
        conn.commit()
    finally:
        conn.close()


def DELETE_create_epoch(start_time, end_time, status):
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
def DELETE_create_round(epoch_id, start_time, end_time, starting_price):
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
        logger.info(f"Found {len(predictions)} for round {round_id}")
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

def get_epochs_lock_start():
    """Get epochs lock start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, lock_start as time 
            from epochs
            where lock_start > current_timestamp
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()

def align_epoch_status(id, from_status, to_status):
    """Helper function that aligns statuses. In prod no alignment should be needed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE epochs 
            SET status = ? 
            WHERE status = ?
            ''', 
            (to_status, from_status)
        )
        conn.commit()
        count = cursor.rowcount
        if count > 0:
            logger.warning(f"Aligned from {from_status} to {to_status} for {count} records. This is due to id {id}. Ideally in prod alignment shouldn't be needed")
        return cursor.rowcount
    finally:
        conn.close()
                
def align_round_status(id, from_status, to_status):
    """Helper function that aligns statuses. In prod no alignment should be needed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''
            UPDATE rounds 
            SET status = ? 
            WHERE status = ?
            ''', 
            (to_status, from_status)
        )
        conn.commit()
        count = cursor.rowcount
        if count > 0:
            logger.warning(f"Aligned from {from_status} to {to_status} for {count} records. This is due to id {id}. Ideally in prod alignment shouldn't be needed")
        return cursor.rowcount
    finally:
        conn.close()
                

def lock_epoch(id):
    """Lock epoch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_epoch_status(id, "locked", "aligned") # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE epochs 
            SET status = 'locked' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Epoch {id} locked. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()


def activate_epoch(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_epoch_status(id, "active", "aligned")  # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE epochs 
            SET status = 'active' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Epoch {id} activated. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()   

def calculating_epoch(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_epoch_status(id, "calculating", "aligned")  # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE epochs 
            SET status = 'calculating' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Epoch {id} calculating. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()   

def completing_epoch(id):
    conn = get_db_connection()
    cursor = conn.cursor()   
    try:
        cursor.execute(
            '''
            UPDATE epochs 
            SET status = 'completed' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Epoch {id} completed. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()   

def activate_round(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_round_status(id, "active", "aligned")  # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE rounds 
            SET status = 'active' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Round {id} activated. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()   


def lock_round(id):
    """Lock round"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_round_status(id, "locked", "aligned") # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE rounds 
            SET status = 'locked' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Rounds {id} locked. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()

def calculating_round(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        align_round_status(id, "calculating", "aligned")  # If in prod we will see warnings here means something is off, because statuses should be aligned even without this
        cursor.execute(
            '''
            UPDATE rounds 
            SET status = 'calculating' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Round {id} calculating. Rowcount: {cursor.rowcount}")
    finally:
        conn.close()   

def completing_round(id):
    conn = get_db_connection()
    cursor = conn.cursor()   
    try:
        cursor.execute(
            '''
            UPDATE rounds 
            SET status = 'completed' 
            WHERE id = ?
            ''', 
            (id,)
        )
        conn.commit()
        logger.info(f"Round {id} completed. Rowcount: {cursor.rowcount}")
    finally:
        conn.close() 

def get_epochs_process_start():
    """Get epochs process start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, start_time as time 
            from epochs
            where start_time > current_timestamp
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_epochs_calculating_start():
    """Get epochs calculating start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, end_time as time 
            from epochs
            where end_time > current_timestamp
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_epochs_completed_start():
    """Get epochs completed start with added seconds"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''
            SELECT id, datetime(end_time, ?) AS time
            FROM epochs
            WHERE datetime(end_time, ?) > current_timestamp
            ''',
            (f"+{config.EPOCH_CALCULATING_SECONDS} seconds", f"+{config.EPOCH_CALCULATING_SECONDS} seconds")
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_rounds_process_start():
    """Get rounds process start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, start_time as time 
            from rounds
            where start_time > current_timestamp
            order by id
            limit 200
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_rounds_lock_start():
    """Get rounds lock start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, lock_start as time 
            from rounds
            where lock_start > current_timestamp
            order by id
            limit 200
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_rounds_calculating_start():
    """Get rounds calculating start with added seconds"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''
            SELECT id, datetime(lock_end, ?) AS time
            FROM rounds
            WHERE datetime(lock_end, ?) > current_timestamp
            order by id
            limit 200
            ''',
            (f"-{config.ROUND_CALCULATING_SECONDS} seconds", f"-{config.ROUND_CALCULATING_SECONDS} seconds")
        )
        return cursor.fetchall()
    finally:
        conn.close()

def get_rounds_completed_start():
    """Get rounds completed start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            select id, lock_end as time 
            from rounds
            where lock_end > current_timestamp
            order by id
            limit 200
            '''
        )
        return cursor.fetchall()
    finally:
        conn.close()


def insert_eligible_epoch_users(id, users):
    """Inserting users that can make prediction for particular epoch."""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    logger.info(f"Inserting {len(users)} users to user_epoch for epoch {id}")
    try:
        cursor.executemany(
            'INSERT OR IGNORE INTO users (address) VALUES (?)',
            [(user,) for user in users]  
        )

        user_data = [(user, id) for user in users]

        cursor.executemany(
            'INSERT OR IGNORE INTO user_epoch (user_address, epoch_id) VALUES (?, ?)',
            user_data
        )

        conn.commit()
    finally:
        conn.close()



