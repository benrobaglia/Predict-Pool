from flask import Blueprint, request, jsonify
from backend.src import models
from backend.src import blockchain
from datetime import datetime
import logging
from eth_account.messages import encode_defunct
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Helper function to verify signature
def verify_signature(message, signature, address):
    """Verify that the signature is valid for the given address"""
    try:
        # Create message hash
        message_hash = encode_defunct(text=message)
        
        # Recover signer address
        w3 = Web3()
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == address.lower()
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

# Health check endpoint
@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

# Epoch endpoints
@api_bp.route('/epochs/current', methods=['GET'])
def get_current_epoch():
    """Get current active epoch"""
    epoch = models.get_active_epoch()
    if not epoch:
        return jsonify({'error': 'No active epoch found'}), 404
    
    # Add contract data
    epoch['baseline'] = blockchain.get_epoch_baseline()
    epoch['total_supply'] = blockchain.get_epoch_total_supply()
    
    return jsonify(epoch)

@api_bp.route('/epochs/<int:epoch_id>', methods=['GET'])
def get_epoch(epoch_id):
    """Get epoch by ID"""
    epoch = models.get_epoch_by_id(epoch_id)
    if not epoch:
        return jsonify({'error': 'Epoch not found'}), 404
    
    return jsonify(epoch)

@api_bp.route('/epochs', methods=['GET'])
def get_epochs():
    """Get all epochs"""
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM epochs ORDER BY id DESC')
        epochs = cursor.fetchall()
        return jsonify(epochs)
    finally:
        conn.close()

# Round endpoints
@api_bp.route('/rounds/current', methods=['GET'])
def get_current_round():
    """Get current active round"""
    round_data = models.get_active_round()
    if not round_data:
        return jsonify({'error': 'No active round found'}), 404
    
    # Get current price
    from backend.src.tasks import fetch_price
    current_price = fetch_price()
    round_data['current_price'] = current_price
    
    return jsonify(round_data)

@api_bp.route('/rounds/<int:round_id>', methods=['GET'])
def get_round(round_id):
    """Get round by ID"""
    round_data = models.get_round_by_id(round_id)
    if not round_data:
        return jsonify({'error': 'Round not found'}), 404
    
    return jsonify(round_data)

@api_bp.route('/epochs/<int:epoch_id>/rounds', methods=['GET'])
def get_epoch_rounds(epoch_id):
    """Get all rounds for an epoch"""
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM rounds WHERE epoch_id = ? ORDER BY id DESC', (epoch_id,))
        rounds = cursor.fetchall()
        return jsonify(rounds)
    finally:
        conn.close()

# Prediction endpoints
@api_bp.route('/predictions', methods=['POST'])
def create_prediction():
    """Create a new prediction"""
    data = request.json
    
    # Validate required fields
    required_fields = ['address', 'round_id', 'direction', 'signature']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate direction
    if data['direction'] not in ['up', 'down']:
        return jsonify({'error': 'Direction must be "up" or "down"'}), 400
    
    # Verify signature
    message = f"Predict {data['direction']} for round {data['round_id']}"
    if not verify_signature(message, data['signature'], data['address']):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Check if round is active
    round_data = models.get_round_by_id(data['round_id'])
    if not round_data:
        return jsonify({'error': 'Round not found'}), 404
    
    if round_data['status'] != 'active':
        return jsonify({'error': 'Round is not active'}), 400
    
    # Check if user already made a prediction for this round
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT * FROM predictions WHERE user_address = ? AND round_id = ?',
            (data['address'], data['round_id'])
        )
        existing_prediction = cursor.fetchone()
        
        if existing_prediction:
            return jsonify({'error': 'User already made a prediction for this round'}), 400
    finally:
        conn.close()
    
    # Create prediction
    prediction_id = models.create_prediction(
        data['address'],
        data['round_id'],
        data['direction']
    )
    
    return jsonify({
        'id': prediction_id,
        'message': 'Prediction created successfully'
    }), 201

# Prediction endpoints
@api_bp.route('/predictionsv2', methods=['POST'])
def create_prediction_v2():
    """Create a new prediction"""
    data = request.json
    
    # Validate required fields
    required_fields = ['address', 'round_id', 'direction', 'signature']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Validate direction
    if data['direction'] not in ['up', 'down']:
        return jsonify({'error': 'Direction must be "up" or "down"'}), 400
    
    # Check if round is active
    round_data = models.get_round_by_id(data['round_id'])
    if not round_data:
        return jsonify({'error': 'Round not found'}), 404
    
    if round_data['status'] != 'active':
        return jsonify({'error': f'Round is not active. It is {round_data["status"]}'}), 400
    
    # Verify signature
    message = f"Predict {data['direction']} for round {data['round_id']}"
    if not verify_signature(message, data['signature'], data['address']):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Check if user can do prediction or already made a prediction for this round
    conn = models.get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT * FROM user_epoch WHERE user_address = ? AND epoch_id = ?',
            (data['address'], round_data['epoch_id'])
        )
        user = cursor.fetchone()
        if not user:  
            return jsonify({'error': 'User is not allowed to make a prediction for this round and epoch. Delegations has to be completed before epoch start.'}), 403
 
        cursor.execute(
            'SELECT * FROM predictions WHERE user_address = ? AND round_id = ?',
            (data['address'], data['round_id'])
        )
        existing_prediction = cursor.fetchone()
        
        if existing_prediction:
            return jsonify({'error': 'User already made a prediction for this round'}), 400
    finally:
        conn.close()
    
    # Create prediction
    prediction_id = models.create_prediction(
        data['address'],
        data['round_id'],
        data['direction']
    )
    
    return jsonify({
        'id': prediction_id,
        'message': 'Prediction created successfully'
    }), 201

@api_bp.route('/users/<address>/predictions', methods=['GET'])
def get_user_predictions(address):
    """Get all predictions for a user"""
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            '''
            SELECT p.*, r.starting_price, r.ending_price, r.status as round_status, e.id as epoch_id
            FROM predictions p
            JOIN rounds r ON p.round_id = r.id
            JOIN epochs e ON r.epoch_id = e.id
            WHERE p.user_address = ?
            ORDER BY p.created_at DESC
            ''',
            (address,)
        )
        predictions = cursor.fetchall()
        return jsonify(predictions)
    finally:
        conn.close()

@api_bp.route('/rounds/<int:round_id>/predictions', methods=['GET'])
def get_round_predictions(round_id):
    """Get all predictions for a round"""
    conn = models.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT * FROM predictions WHERE round_id = ?',
            (round_id,)
        )
        predictions = cursor.fetchall()
        
        # Count up/down predictions
        up_count = sum(1 for p in predictions if p['direction'] == 'up')
        down_count = sum(1 for p in predictions if p['direction'] == 'down')
        
        return jsonify({
            'predictions': predictions,
            'stats': {
                'total': len(predictions),
                'up': up_count,
                'down': down_count
            }
        })
    finally:
        conn.close()

# User stats endpoints
@api_bp.route('/users/<address>/stats', methods=['GET'])
def get_user_stats(address):
    """Get user stats for current epoch"""
    epoch = models.get_active_epoch()
    if not epoch:
        return jsonify({'error': 'No active epoch found'}), 404
    
    stats = models.get_user_stats(address, epoch['id'])
    if not stats:
        # Return empty stats if user has no activity
        stats = {
            'user_address': address,
            'epoch_id': epoch['id'],
            'correct_predictions': 0,
            'total_predictions': 0,
            'weight': 0,
            'accuracy': 0
        }
    
    # Add contract data
    stats['balance'] = blockchain.get_user_balance(address)
    stats['contract_weight'] = blockchain.get_user_weight(address)
    
    return jsonify(stats)

@api_bp.route('/users/<address>/stats/<int:epoch_id>', methods=['GET'])
def get_user_epoch_stats(address, epoch_id):
    """Get user stats for a specific epoch"""
    stats = models.get_user_stats(address, epoch_id)
    if not stats:
        return jsonify({'error': 'Stats not found'}), 404
    
    return jsonify(stats)

# Leaderboard endpoint
@api_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard for current epoch"""
    epoch = models.get_active_epoch()
    if not epoch:
        return jsonify({'error': 'No active epoch found'}), 404
    
    leaderboard = models.get_leaderboard(epoch['id'])
    return jsonify(leaderboard)

@api_bp.route('/leaderboard/<int:epoch_id>', methods=['GET'])
def get_epoch_leaderboard(epoch_id):
    """Get leaderboard for a specific epoch"""
    epoch = models.get_epoch_by_id(epoch_id)
    if not epoch:
        return jsonify({'error': 'Epoch not found'}), 404
    
    leaderboard = models.get_leaderboard(epoch_id)
    return jsonify(leaderboard)

# Contract data endpoints
@api_bp.route('/contract/info', methods=['GET'])
def get_contract_info():
    """Get contract information"""
    return jsonify({
        'total_mon': blockchain.get_total_mon(),
        'epoch_baseline': blockchain.get_epoch_baseline(),
        'epoch_total_supply': blockchain.get_epoch_total_supply()
    })


@api_bp.route('/rewards/apy', methods=['GET'])
def get_all_rewards():
    """Get rewards and APY for all users at the end of an epoch"""
    # Check for unknown parameters
    allowed_params = ['display_scale_factor']
    unknown_params = [param for param in request.args.keys() if param not in allowed_params]
    if unknown_params:
        return jsonify({'error': f'Unknown parameter(s): {", ".join(unknown_params)}'}), 400
    
    # Get display_scale_factor from query parameters if provided
    display_scale_factor = request.args.get('display_scale_factor', 10)
    try:
        display_scale_factor = int(display_scale_factor)
        if display_scale_factor <= 0:
            return jsonify({'error': 'display_scale_factor must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid display_scale_factor format'}), 400
    
    # Calculate rewards and APY for all users
    all_rewards_data = blockchain.calculate_users_rewards_and_apy(display_scale_factor)
    
    if 'error' in all_rewards_data:
        return jsonify({'error': all_rewards_data['error']}), 500
    
    # Get the most recent completed epoch
    conn = models.get_db_connection()
    cursor = conn.cursor()
    epoch_id = None
    try:
        cursor.execute(
            'SELECT id FROM epochs WHERE status = "completed" ORDER BY id DESC LIMIT 1'
        )
        latest_completed = cursor.fetchone()
        if latest_completed:
            epoch_id = latest_completed['id']
    finally:
        conn.close()
    
    # Format the response
    result = {
        'epoch_id': epoch_id,
        'users': {}
    }
    
    # Add user stats for each user
    for address, rewards in all_rewards_data.items():
        user_data = {
            'rewards': rewards['rewards'],
            'apy': rewards['apy'],
            'annualized_apy': rewards['annualized_apy'],
            'display_apy': rewards['display_apy']
        }
        
        # Get user stats if epoch_id is available
        if epoch_id:
            stats = models.get_user_stats(address, epoch_id)
            if stats:
                user_data.update({
                    'correct_predictions': stats['correct_predictions'],
                    'total_predictions': stats['total_predictions'],
                    'accuracy': stats.get('accuracy', 0),
                    'weight': stats['weight']
                })
        
        result['users'][address] = user_data
    
    # Add total rewards information
    if all_rewards_data and len(all_rewards_data) > 0:
        # All users have the same epoch_rewards value, so just get it from the first user
        first_user = next(iter(all_rewards_data))
        result['epoch_rewards'] = all_rewards_data[first_user]['epoch_rewards']
    
    return jsonify(result)
