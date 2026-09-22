CREATE TABLE erc1155_transfers (
    id BIGSERIAL PRIMARY KEY,
    contract TEXT NOT NULL,
    token_id NUMERIC(78, 0) NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_hash TEXT NOT NULL,
    log_index INTEGER NOT NULL,
    operator TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount NUMERIC(78, 0) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (contract, transaction_hash, log_index, token_id)
);

CREATE INDEX erc1155_transfers_sender_idx ON erc1155_transfers (sender);
CREATE INDEX erc1155_transfers_recipient_idx ON erc1155_transfers (recipient);
