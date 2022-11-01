CREATE DATABASE IF NOT EXISTS newsfeeds_db;
CREATE DATABASE IF NOT EXISTS keys_db;

USE newsfeeds_db;

CREATE TABLE IF NOT EXISTS old_ids (
    user_id INT,
    newsfeed_id INT
);

USE keys_db;

CREATE TABLE IF NOT EXISTS activation_keys (
    activation_key TINYTEXT,
    key_type TINYTEXT,
    key_days INT
);