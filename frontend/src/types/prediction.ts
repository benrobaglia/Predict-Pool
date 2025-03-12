export interface Round {
  id: number;
  epoch_id: number;
  status:
    | "expired"
    | "active"
    | "next"
    | "later"
    | "completed"
    | "calculating"
    | "locked"
    | "scheduled";
  starting_price: number;
  ending_price: number;
  start_time: string;
  end_time: string;
  lock_start: string;
  lock_end: string;
}

export interface Epoch {
  id: number;
  status: string;
  start_time: string;
  end_time: string;
  lock_start: string;
  lock_end: string;
  baseline: number;
  total_supply: number;
  created_at: string;
  updated_at: string;
}

export interface Prediction {
  address: string;
  round_id: number;
  direction: "up" | "down";
  signature: string;
}

export interface PredictionWithDetails extends Prediction {
  created_at: string;
  ending_price: number;
  starting_price: number;
  is_correct: number;
  round_status: string;
  epoch_id: number;
}
