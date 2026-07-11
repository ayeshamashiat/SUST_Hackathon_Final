# What-if Simulator

`POST /simulate/scenario` writes simulated demand into the same transaction, synchronization, forecast, and alert pipeline used by the background simulator. It does not fabricate forecast or alert responses.

The generated effects are immediately available through `GET /aggregate/forecast` and `GET /alerts`.

## Example scenarios

### bKash Eid cash-out pressure

```json
POST /simulate/scenario
{
  "provider": "bkash",
  "demand_multiplier": 2.5,
  "duration_minutes": 45,
  "transaction_rate": 3,
  "cash_out_ratio": 0.9
}
```

### Nagad balanced demand

```json
POST /simulate/scenario
{
  "provider": "nagad",
  "demand_multiplier": 1.2,
  "duration_minutes": 30,
  "transaction_rate": 2,
  "cash_out_ratio": 0.55
}
```

`provider` must be one of `bkash`, `nagad`, or `rocket`. `demand_multiplier`, `duration_minutes`, and `transaction_rate` must be positive; `cash_out_ratio` is between 0 and 1.
