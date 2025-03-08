from apscheduler.schedulers.background import BackgroundScheduler
import time
import requests
import logging
import models
import blockchain
import config
from datetime import datetime, timedelta
import backoff
from functools import partial


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})

@backoff.on_exception(backoff.expo, Exception, max_tries=10, jitter=backoff.full_jitter)
def fetch_price():
    """Fetch current symbol price from an API with retries using backoff"""
    try:
        symbol = "ETHUSDT"  # Replace with MON when available
        response = requests.get(config.PRICE_API_URL + symbol, timeout=5)
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

def process_round_end():
    """Process the end of a round"""
    logger.info("Checking for round end...")
    
    # Get current active round
    active_round = models.get_active_round()

    if not active_round:
        logger.warning("No active round found")
        return
    
    # Parse end_time string to datetime
    end_time = datetime.strptime(active_round['end_time'], '%Y-%m-%d %H:%M:%S')
    
    # Check if round should end
    if datetime.now() >= end_time:
        logger.info(f"Processing end of round {active_round['id']}")
        
        # Get final price
        final_price = fetch_price()
        if final_price is None:
            logger.error("Failed to fetch price for round end")
            return
        
        # Update round with final price
        models.update_round(active_round['id'], {
            'ending_price': final_price,
            'status': 'completed'
        })
        
        # Determine correct direction
        direction = 'up' if final_price > active_round['starting_price'] else 'down'
        logger.info(f"Round {active_round['id']} result: {direction} (start: {active_round['starting_price']}, end: {final_price})")
        
        # Evaluate predictions
        models.evaluate_predictions(active_round['id'], direction)
        
        # Create new round if within epoch
        current_epoch = models.get_epoch_by_id(active_round['epoch_id'])
        epoch_end_time = datetime.strptime(current_epoch['end_time'], '%Y-%m-%d %H:%M:%S')
        
        if datetime.now() < epoch_end_time:
            # Create new round
            now = datetime.now()
            round_end = now + timedelta(minutes=config.ROUND_DURATION_MINUTES)
            
            # Ensure round doesn't extend past epoch end
            if round_end > epoch_end_time:
                round_end = epoch_end_time
            
            new_round_id = models.create_round(
                current_epoch['id'],
                now.strftime('%Y-%m-%d %H:%M:%S'),
                round_end.strftime('%Y-%m-%d %H:%M:%S'),
                final_price
            )
            logger.info(f"Created new round {new_round_id} with starting price ${final_price}")
        else:
            logger.info("Epoch is ending, not creating a new round")

def process_epoch_end():
    """Process the end of an epoch"""
    logger.info("Checking for epoch end...")
    
    # Get current active epoch
    active_epoch = models.get_epoch_by_id(models.get_active_epoch()['id'])
    if not active_epoch:
        logger.warning("No active epoch found")
        return
    
    # Parse end_time string to datetime
    end_time = datetime.strptime(active_epoch['end_time'], '%Y-%m-%d %H:%M:%S')
    
    # Check if epoch should end
    if datetime.now() >= end_time:
        logger.info(f"Processing end of epoch {active_epoch['id']}")
        
        # Mark epoch as completed
        models.update_epoch(active_epoch['id'], {'status': 'completed'})
        
        # Calculate user weights
        user_stats = models.get_user_epoch_stats(active_epoch['id'])
        
        # Normalize weights
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
                success = blockchain.update_user_weights(addresses, weights)
                if success:
                    logger.info("Successfully updated weights on contract")
                else:
                    logger.error("Failed to update weights on contract")
        else:
            logger.warning("No correct predictions in this epoch")
        
        # Create new epoch
        now = datetime.now()
        epoch_end = now + timedelta(minutes=config.EPOCH_DURATION_MINUTES)
        
        new_epoch_id = models.create_epoch(
            now.strftime('%Y-%m-%d %H:%M:%S'),
            epoch_end.strftime('%Y-%m-%d %H:%M:%S'),
            'active'
        )
        logger.info(f"Created new epoch {new_epoch_id}")
        
        # Create first round in new epoch
        current_price = fetch_price()
        if current_price:
            round_end = now + timedelta(minutes=config.ROUND_DURATION_MINUTES)
            new_round_id = models.create_round(
                new_epoch_id,
                now.strftime('%Y-%m-%d %H:%M:%S'),
                round_end.strftime('%Y-%m-%d %H:%M:%S'),
                current_price
            )
            logger.info(f"Created first round {new_round_id} in new epoch with starting price ${current_price}")
        
        # Update epoch on contract
        success = blockchain.update_epoch()
        if success:
            logger.info("Successfully updated epoch on contract")
        else:
            logger.error("Failed to update epoch on contract")

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
    #open round from epoch I guess is needed or not, because I will 

def process_epoch_calculating_start(id):
    """Epoch calculating.

    Setting epoch to calculating
    Also pushing weights to smart contract
    """
    logger.info(f"Calculating epoch: {id}")
    models.calculating_epoch(id)
    # add weights pushing to chain

def process_epoch_completed_start(id):
    """Epoch completed.
    
    Setting epoch to complete"""
    logger.info(f"Completing epoch {id}")
    models.completing_epoch(id)


def refresh_scheduled_jobs():
    """Refresh the scheduler with new jobs from DB."""
    jobs = {
        "process_epoch_lock_start": models.get_epochs_lock_start,
        "process_epoch_start": models.get_epochs_process_start,
        "process_epoch_calculating_start": models.get_epochs_calculating_start,
        "process_epoch_completed_start": models.get_epochs_completed_start,
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
    logger.info("Starting scheduler...")

    #generating epochs and rounds
    #just for example added every 10 mins, it should run once per day
    scheduler.add_job(models.generate_epochs_and_rounds, 'cron',  minute='*/10', second=0, id='generate_epochs_and_rounds')
    #scheduler.add_job(models.generate_epochs_and_rounds, 'cron', hour=0, minute=0, second=25, id='daily_generate_epochs_and_rounds') # later change to this

    # Dynamically building list of scheduled tasks
    scheduler.add_job(refresh_scheduled_jobs, 'cron', minute='*/1', id='refresh_jobs') 
    #scheduler.add_job(refresh_scheduled_jobs, 'interval', minutes=60, id='refresh_jobs')  # later change to this







    # Fetch price every 30 seconds. It doesn't matters how often we will fetch it, because on round/epoch end we'll fetch the price + frontend should do the calls to get the price directly to Binance
    #scheduler.add_job(fetch_price, 'interval', seconds=30, id='fetch_price', next_run_time=datetime.now())
    
    # Check for round end every 10 minutes
    #scheduler.add_job(process_round_end, 'interval', seconds=10, id='process_round', next_run_time=datetime.now())
    #scheduler.add_job(process_round_end, 'cron', second=0, id='process_round')
    #scheduler.add_job(lock_bidding, 'cron', second=40, id='lock_bidding')

    #scheduler.add_job(process_epoch_end, 'cron',  minute='*/10', second=0, id='process_epoch')

    # Check for epoch end every hour
    #scheduler.add_job(process_epoch_end, 'interval', seconds=10, id='process_epoch', next_run_time=datetime.now())
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    return scheduler

def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
