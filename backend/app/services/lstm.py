from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LSTMConfig:
    sequence_length: int = 20
    hidden_size: int = 32
    num_layers: int = 1
    dropout: float = 0.0
    epochs: int = 20
    learning_rate: float = 1e-3
    batch_size: int = 32
    seed: int = 42

    def __post_init__(self) -> None:
        if self.sequence_length < 2:
            raise ValueError("sequence_length must be at least 2")
        if self.hidden_size < 1 or self.num_layers < 1:
            raise ValueError("hidden_size and num_layers must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if self.epochs < 1 or self.batch_size < 1:
            raise ValueError("epochs and batch_size must be positive")
        if not np.isfinite(self.learning_rate) or self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive and finite")


def make_sequences(
    frame: pd.DataFrame,
    features: list[str],
    target: str = "target_5d_up",
    sequence_length: int = 20,
) -> tuple[np.ndarray, np.ndarray]:
    if sequence_length < 2:
        raise ValueError("sequence_length must be at least 2")
    if not features:
        raise ValueError("features must not be empty")
    missing = [column for column in [*features, target] if column not in frame.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    values = frame[[*features, target]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("features and target must be finite")
    if len(values) <= sequence_length:
        raise ValueError("frame must contain more rows than sequence_length")
    x = np.stack(
        [values[i - sequence_length:i, :-1] for i in range(sequence_length, len(values))]
    )
    y = values[sequence_length:, -1].astype(np.float32)
    return x.astype(np.float32), y


def chronological_sequence_split(
    x: np.ndarray,
    y: np.ndarray,
    train_ratio: float = 0.7,
    validation_ratio: float = 0.15,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("x and y must have equal length and at least 3 observations")
    if not 0 < train_ratio < 1 or not 0 <= validation_ratio < 1 or train_ratio + validation_ratio >= 1:
        raise ValueError("invalid chronological split ratios")
    n = len(x)
    a = max(1, int(n * train_ratio))
    b = max(a + 1, int(n * (train_ratio + validation_ratio)))
    if b >= n:
        b = n - 1
    if a >= b:
        raise ValueError("split leaves no validation data")
    return (x[:a], y[:a]), (x[a:b], y[a:b]), (x[b:], y[b:])


def train_lstm(
    train_x: np.ndarray,
    train_y: np.ndarray,
    validation_x: np.ndarray,
    validation_y: np.ndarray,
    config: LSTMConfig = LSTMConfig(),
) -> dict[str, object]:
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise RuntimeError("PyTorch is required for the LSTM experiment") from exc

    if train_x.ndim != 3 or validation_x.ndim != 3:
        raise ValueError("sequence arrays must be 3-dimensional")
    if train_x.shape[1:] != validation_x.shape[1:]:
        raise ValueError("train and validation sequence shapes must match")
    if len(train_x) != len(train_y) or len(validation_x) != len(validation_y):
        raise ValueError("sequence and target lengths must match")
    if len(train_x) < 2 or len(validation_x) < 1:
        raise ValueError("insufficient train/validation observations")

    torch.manual_seed(config.seed)
    model = nn.LSTM(
        input_size=train_x.shape[2],
        hidden_size=config.hidden_size,
        num_layers=config.num_layers,
        dropout=config.dropout if config.num_layers > 1 else 0.0,
        batch_first=True,
    )
    head = nn.Linear(config.hidden_size, 1)
    optimizer = torch.optim.Adam(
        list(model.parameters()) + list(head.parameters()),
        lr=config.learning_rate,
    )
    loss_fn = nn.BCEWithLogitsLoss()

    x_tensor = torch.from_numpy(train_x)
    y_tensor = torch.from_numpy(train_y).view(-1, 1)
    vx_tensor = torch.from_numpy(validation_x)
    vy_tensor = torch.from_numpy(validation_y).view(-1, 1)

    history: list[dict[str, float]] = []
    for _ in range(config.epochs):
        model.train()
        head.train()
        order = torch.arange(len(x_tensor))
        total_loss = 0.0
        for start in range(0, len(order), config.batch_size):
            batch = order[start:start + config.batch_size]
            optimizer.zero_grad()
            output, _ = model(x_tensor[batch])
            logits = head(output[:, -1, :])
            loss = loss_fn(logits, y_tensor[batch])
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(batch)

        model.eval()
        head.eval()
        with torch.no_grad():
            val_logits = head(model(vx_tensor)[0][:, -1, :])
            val_loss = float(loss_fn(val_logits, vy_tensor))
        history.append(
            {
                "train_loss": total_loss / len(order),
                "validation_loss": val_loss,
            }
        )

    with torch.no_grad():
        probabilities = torch.sigmoid(head(model(vx_tensor)[0][:, -1, :])).cpu().numpy().ravel()

    predictions = (probabilities >= 0.5).astype(int)
    accuracy = float((predictions == validation_y.astype(int)).mean())
    return {
        "history": history,
        "validation_accuracy": accuracy,
        "mean_validation_probability": float(probabilities.mean()),
        "final_validation_loss": history[-1]["validation_loss"],
        "sequence_length": config.sequence_length,
        "hidden_size": config.hidden_size,
        "epochs": config.epochs,
        "seed": config.seed,
    }
