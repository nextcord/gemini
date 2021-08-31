CREATE TABLE IF NOT EXISTS Infractions (
    id                  SERIAL PRIMARY KEY,
    member_id           BIGINT NOT NULL,
    member_name         VARCHAR(255) NOT NULL,
    staff_id            BIGINT NOT NULL,
    staff_name          VARCHAR(255) NOT NULL,
    infr_type           INT NOT NULL,
    reason              TEXT NOT NULL,
    created             TIMESTAMP NOT NULL,
    expires             TIMESTAMP,
    expired             BOOLEAN NOT NULL DEFAULT FALSE
);
