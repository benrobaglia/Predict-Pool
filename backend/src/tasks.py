from apscheduler.schedulers.background import BackgroundScheduler
import time
import requests
import logging
from backend.src import models
from backend.src import blockchain
from backend.config import config
from datetime import datetime, timezone
import backoff
from functools import partial


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to track if scheduler is initialized
scheduler = None

@backoff.on_exception(backoff.expo, Exception, max_tries=10, jitter=backoff.full_jitter)
def fetch_price():
    """Fetch current symbol price from an API with retries using backoff"""
    try:
        symbol = config.SYMBOL
        response = requests.get(config.PRICE_API_URL + symbol, proxies=config.PROXY, timeout=5)
        response.raise_for_status()

        data = response.json()
        if 'price' in data:
            price = data['price']
            logger.info(f"Fetched {symbol} price: ${price}")
            return price
        else:
            raise ValueError("Invalid response format")
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        raise 

def process_epoch_lock_start(id):
    """Epoch lock start.

    Lock current epoch
    Get onchain holders & store to the table
    """
    logger.info(f"Locking epoch: {id}")
    models.lock_epoch(id)
    users = blockchain.get_users()
    models.insert_eligible_epoch_users(id, users)

def process_epoch_start(id):
    """Epoch start.
    
    Setting epoch to active
    """
    logger.info(f"Activating epoch: {id}")
    models.activate_epoch(id)

def process_epoch_calculating_start(id):
    """Epoch calculating.

    Setting epoch to calculating
    Calculating and pushing weights to smart contract
    """
    logger.info(f"Calculating epoch: {id}")
    models.calculating_epoch(id)

    user_stats = models.get_user_epoch_stats(id)
    
    if user_stats:
        total_correct = sum(stat['correct_predictions'] for stat in user_stats)
        if total_correct > 0:
            addresses = []
            weights = []
            
            for stat in user_stats:
                # Simple weight calculation: correct_predictions / total_correct * 100
                # This gives a percentage weight based on relative performance
                weight = int((stat['correct_predictions'] / total_correct) * 100)
                
                # Update in database
                models.update_user_epoch_stats(
                    stat['id'], 
                    {'weight': weight}
                )
                
                # Add to lists for contract update
                addresses.append(stat['user_address'])
                weights.append(weight)
            
            logger.info(f"Calculated weights for {len(addresses)} users")
            
            # Update weights on contract
            if addresses and weights:
                logger.info(f"{addresses}. {weights}. Will update blockchain")
                success = blockchain.update_user_weights(addresses, weights)
                if success:
                    logger.info("Successfully updated weights on contract")
                else:
                    logger.error("Failed to update weights on contract")
    else:
        logger.info(f"There are no user statistics for epoch {id}")

def process_epoch_completed_start(id):
    """Epoch completed.
    
    Setting epoch to complete"""
    logger.info(f"Completing epoch {id}")
    models.completing_epoch(id)

def process_round_start(id):
    """Round start.
    
    Setting round to active
    Fetching initial token price
    Storing token price to DB
    """
    logger.info(f"Activating round: {id}")
    models.activate_round(id)
    current_price = fetch_price()
    models.update_round(id, {'starting_price': current_price})


def process_round_lock_start(id):
    """Round lock start.

    Lock current round
    """
    logger.info(f"Locking round: {id}")
    models.lock_round(id)

def process_round_calculating_start(id):
    """Round calculating.

    Setting epoch to calculating
    Fetching initial token price
    Storing token price to DB
    Fetching active round
    Determing direction of token movement
    Evaluating predictions
    """
    logger.info(f"Calculating round: {id}")
    models.calculating_round(id)
    final_price = fetch_price()
    models.update_round(id, {'ending_price': final_price})
    active_round = models.get_round_by_id(id)
    direction = 'up' if float(final_price) > active_round['starting_price'] else 'down'
    models.evaluate_predictions(id, direction)
    logger.info(f"Round {id} result: {direction} (start: {active_round['starting_price']}, end: {final_price})")

def process_round_completed_start(id):
    """Round completed.
    
    Setting round to complete
    Fetching round
    Logging resulsts
    """
    logger.info(f"Completing round {id}")
    models.completing_round(id)


def refresh_scheduled_jobs():
    """Refresh the scheduler with new jobs from DB."""
    jobs = {
        "process_epoch_lock_start": models.get_epochs_lock_start,
        "process_epoch_start": models.get_epochs_process_start,
        "process_epoch_calculating_start": models.get_epochs_calculating_start,
        "process_epoch_completed_start": models.get_epochs_completed_start,
        "process_round_start": models.get_rounds_process_start,
        "process_round_lock_start": models.get_rounds_lock_start,
        "process_round_calculating_start": models.get_rounds_calculating_start,
        "process_round_completed_start": models.get_rounds_completed_start, 
    }

    for event_type, get_function in jobs.items():
        data = get_function()

        for item in data:
            id = item["id"]
            job_id = f"{event_type}_{id}"
            
            event_datetime = datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S")

            if event_type in globals():
                if callable(globals()[event_type]):
                    process_function = partial(globals()[event_type], id)

                    if not scheduler.get_job(job_id):
                        scheduler.add_job(
                            process_function, 
                            "date", 
                            run_date=event_datetime, 
                            id=job_id
                        )
                        logger.info(f"Scheduled {event_type} for id {id} at {event_datetime}")


def start_scheduler():
    """Start the scheduler with all tasks"""
    global scheduler
    
    # Only initialize the scheduler if it hasn't been initialized yet
    if scheduler is None:
        logger.info("Initializing scheduler...")
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
        
        logger.info("Starting scheduler...")
        
        # Generating epochs and rounds
        scheduler.add_job(models.generate_epochs_and_rounds, 'cron', minute=11, second=0, id='generate_epochs_and_rounds') # Will run every hour at xx:11 min

        # Dynamically building list of scheduled tasks
        scheduler.add_job(refresh_scheduled_jobs, 'cron', minute=14, id='refresh_jobs', next_run_time=datetime.now(timezone.utc)) # Will run every hour at xx:14 min

        scheduler.start()
        logger.info("Scheduler started")
    else:
        logger.info("Scheduler already initialized and running")
    
    return scheduler

def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Scheduler stopped")
    else:
        logger.info("No scheduler running to stop")
