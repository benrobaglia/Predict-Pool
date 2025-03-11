# PredictPool API Documentation

This document provides detailed information about the API endpoints available in the PredictPool backend.

## Base URL

All API endpoints are prefixed with `/api`.

## Authentication

Some endpoints require authentication using Ethereum signatures. For these endpoints, you need to:

1. Create a message string according to the endpoint's requirements
2. Sign the message using your Ethereum private key
3. Include the signature and your Ethereum address in the request

## Endpoints

### Health Check

#### `GET /api/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-03-11T22:30:00.000Z"
}
```

### Epochs

#### `GET /api/epochs/current`

Get the current active epoch.

**Response:**
```json
{
  "id": 123,
  "start_time": "2025-03-11 22:00:00",
  "end_time": "2025-03-11 22:10:00",
  "lock_start": "2025-03-11 21:59:50",
  "lock_end": "2025-03-11 22:00:00",
  "status": "active",
  "created_at": "2025-03-11 21:00:00",
  "updated_at": "2025-03-11 22:00:00",
  "baseline": 1000000000000000000,
  "total_supply": 2000000000000000000
}
```

#### `GET /api/epochs/<epoch_id>`

Get a specific epoch by ID.

**Parameters:**
- `epoch_id`: The ID of the epoch to retrieve

**Response:**
```json
{
  "id": 123,
  "start_time": "2025-03-11 22:00:00",
  "end_time": "2025-03-11 22:10:00",
  "lock_start": "2025-03-11 21:59:50",
  "lock_end": "2025-03-11 22:00:00",
  "status": "active",
  "created_at": "2025-03-11 21:00:00",
  "updated_at": "2025-03-11 22:00:00"
}
```

#### `GET /api/epochs`

Get all epochs.

**Response:**
```json
[
  {
    "id": 123,
    "start_time": "2025-03-11 22:00:00",
    "end_time": "2025-03-11 22:10:00",
    "lock_start": "2025-03-11 21:59:50",
    "lock_end": "2025-03-11 22:00:00",
    "status": "active",
    "created_at": "2025-03-11 21:00:00",
    "updated_at": "2025-03-11 22:00:00"
  },
  {
    "id": 122,
    "start_time": "2025-03-11 21:50:00",
    "end_time": "2025-03-11 22:00:00",
    "lock_start": "2025-03-11 21:49:50",
    "lock_end": "2025-03-11 21:50:00",
    "status": "completed",
    "created_at": "2025-03-11 21:00:00",
    "updated_at": "2025-03-11 22:00:00"
  }
]
```

### Rounds

#### `GET /api/rounds/current`

Get the current active round.

**Response:**
```json
{
  "id": 456,
  "epoch_id": 123,
  "start_time": "2025-03-11 22:00:00",
  "end_time": "2025-03-11 22:01:00",
  "lock_start": "2025-03-11 22:00:30",
  "lock_end": "2025-03-11 22:01:00",
  "starting_price": 100.50,
  "ending_price": null,
  "status": "active",
  "created_at": "2025-03-11 21:00:00",
  "updated_at": "2025-03-11 22:00:00",
  "current_price": 101.25
}
```

#### `GET /api/rounds/<round_id>`

Get a specific round by ID.

**Parameters:**
- `round_id`: The ID of the round to retrieve

**Response:**
```json
{
  "id": 456,
  "epoch_id": 123,
  "start_time": "2025-03-11 22:00:00",
  "end_time": "2025-03-11 22:01:00",
  "lock_start": "2025-03-11 22:00:30",
  "lock_end": "2025-03-11 22:01:00",
  "starting_price": 100.50,
  "ending_price": null,
  "status": "active",
  "created_at": "2025-03-11 21:00:00",
  "updated_at": "2025-03-11 22:00:00"
}
```

#### `GET /api/epochs/<epoch_id>/rounds`

Get all rounds for an epoch.

**Parameters:**
- `epoch_id`: The ID of the epoch to retrieve rounds for

**Response:**
```json
[
  {
    "id": 456,
    "epoch_id": 123,
    "start_time": "2025-03-11 22:00:00",
    "end_time": "2025-03-11 22:01:00",
    "lock_start": "2025-03-11 22:00:30",
    "lock_end": "2025-03-11 22:01:00",
    "starting_price": 100.50,
    "ending_price": null,
    "status": "active",
    "created_at": "2025-03-11 21:00:00",
    "updated_at": "2025-03-11 22:00:00"
  },
  {
    "id": 457,
    "epoch_id": 123,
    "start_time": "2025-03-11 22:01:00",
    "end_time": "2025-03-11 22:02:00",
    "lock_start": "2025-03-11 22:01:30",
    "lock_end": "2025-03-11 22:02:00",
    "starting_price": null,
    "ending_price": null,
    "status": "scheduled",
    "created_at": "2025-03-11 21:00:00",
    "updated_at": "2025-03-11 21:00:00"
  }
]
```

### Predictions

#### `POST /api/predictionsv2`

Create a new prediction. This endpoint requires authentication.

**Request Body:**
```json
{
  "address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
  "round_id": 456,
  "direction": "up",
  "signature": "0x..."
}
```

**Notes:**
- `direction` must be either "up" or "down"
- `signature` must be a valid signature of the message "Predict up for round 456" (or "down" depending on your prediction)
- The user must be eligible to make predictions for the epoch that contains this round
- The round must be active

**Response:**
```json
{
  "id": 789,
  "message": "Prediction created successfully"
}
```

#### `GET /api/users/<address>/predictions`

Get all predictions for a user.

**Parameters:**
- `address`: The Ethereum address of the user

**Response:**
```json
[
  {
    "id": 789,
    "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
    "round_id": 456,
    "direction": "up",
    "created_at": "2025-03-11 22:00:15",
    "is_correct": null,
    "starting_price": 100.50,
    "ending_price": null,
    "round_status": "active",
    "epoch_id": 123
  },
  {
    "id": 788,
    "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
    "round_id": 455,
    "direction": "down",
    "created_at": "2025-03-11 21:59:15",
    "is_correct": true,
    "starting_price": 101.50,
    "ending_price": 100.75,
    "round_status": "completed",
    "epoch_id": 122
  }
]
```

#### `GET /api/rounds/<round_id>/predictions`

Get all predictions for a round.

**Parameters:**
- `round_id`: The ID of the round to retrieve predictions for

**Response:**
```json
{
  "predictions": [
    {
      "id": 789,
      "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
      "round_id": 456,
      "direction": "up",
      "created_at": "2025-03-11 22:00:15",
      "is_correct": null
    },
    {
      "id": 790,
      "user_address": "0x209ebD2cA4d5FfF84356948D75fD73883361F49B",
      "round_id": 456,
      "direction": "down",
      "created_at": "2025-03-11 22:00:20",
      "is_correct": null
    }
  ],
  "stats": {
    "total": 2,
    "up": 1,
    "down": 1
  }
}
```

### User Stats

#### `GET /api/users/<address>/stats`

Get user stats for the current epoch.

**Parameters:**
- `address`: The Ethereum address of the user

**Response:**
```json
{
  "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
  "epoch_id": 123,
  "correct_predictions": 3,
  "total_predictions": 5,
  "weight": 60,
  "accuracy": 0.6,
  "balance": 1000000000000000000,
  "contract_weight": 60
}
```

#### `GET /api/users/<address>/stats/<epoch_id>`

Get user stats for a specific epoch.

**Parameters:**
- `address`: The Ethereum address of the user
- `epoch_id`: The ID of the epoch to retrieve stats for

**Response:**
```json
{
  "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
  "epoch_id": 122,
  "correct_predictions": 7,
  "total_predictions": 10,
  "weight": 70,
  "accuracy": 0.7
}
```

### Leaderboard

#### `GET /api/leaderboard`

Get leaderboard for the current epoch.

**Response:**
```json
[
  {
    "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
    "correct_predictions": 3,
    "total_predictions": 5,
    "weight": 60,
    "accuracy": 0.6
  },
  {
    "user_address": "0x209ebD2cA4d5FfF84356948D75fD73883361F49B",
    "correct_predictions": 2,
    "total_predictions": 5,
    "weight": 40,
    "accuracy": 0.4
  }
]
```

#### `GET /api/leaderboard/<epoch_id>`

Get leaderboard for a specific epoch.

**Parameters:**
- `epoch_id`: The ID of the epoch to retrieve the leaderboard for

**Response:**
```json
[
  {
    "user_address": "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5",
    "correct_predictions": 7,
    "total_predictions": 10,
    "weight": 70,
    "accuracy": 0.7
  },
  {
    "user_address": "0x209ebD2cA4d5FfF84356948D75fD73883361F49B",
    "correct_predictions": 3,
    "total_predictions": 10,
    "weight": 30,
    "accuracy": 0.3
  }
]
```

### Contract Data

#### `GET /api/contract/info`

Get contract information.

**Response:**
```json
{
  "total_mon": 1000000000000000000,
  "epoch_baseline": 900000000000000000,
  "epoch_total_supply": 2000000000000000000
}
```

#### `GET /api/rewards/apy`

Get rewards and APY for all users.

**Query Parameters:**
- `display_scale_factor` (optional): Scale factor for display APY (default: 10)

**Response:**
```json
{
  "epoch_id": 122,
  "users": {
    "0x7B77E94C864E7D965a6E2DD4942DE0dF7072f9F5": {
      "rewards": 60000000000000000,
      "apy": 6.0,
      "annualized_apy": 315360.0,
      "display_apy": 3153600.0,
      "correct_predictions": 7,
      "total_predictions": 10,
      "accuracy": 0.7,
      "weight": 70
    },
    "0x209ebD2cA4d5FfF84356948D75fD73883361F49B": {
      "rewards": 40000000000000000,
      "apy": 4.0,
      "annualized_apy": 210240.0,
      "display_apy": 2102400.0,
      "correct_predictions": 3,
      "total_predictions": 10,
      "accuracy": 0.3,
      "weight": 30
    }
  },
  "epoch_rewards": 100000000000000000
}
```

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid signature
- `403 Forbidden`: User not allowed to perform the action
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses have the following format:

```json
{
  "error": "Error message"
}
```

## Rate Limiting

There are currently no rate limits implemented, but excessive requests may be throttled in the future.