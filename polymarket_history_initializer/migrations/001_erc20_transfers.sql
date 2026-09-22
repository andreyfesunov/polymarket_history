CREATE TABLE erc20_transfers (
    id BIGSERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_hash TEXT NOT NULL,
    log_index INTEGER NOT NULL,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount NUMERIC(78, 0) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (token, transaction_hash, log_index)
);

CREATE INDEX erc20_transfers_sender_idx ON erc20_transfers (sender);
CREATE INDEX erc20_transfers_recipient_idx ON erc20_transfers (recipient);
