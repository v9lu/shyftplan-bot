CREATE DATABASE IF NOT EXISTS keys_db;
CREATE DATABASE IF NOT EXISTS newsfeeds_db;
CREATE DATABASE IF NOT EXISTS sp_users_db;
CREATE DATABASE IF NOT EXISTS users_db;

USE keys_db;

CREATE TABLE IF NOT EXISTS activation_keys (
    activation_key TINYTEXT,
    key_type TINYTEXT,
    key_days INT
);

USE newsfeeds_db;

CREATE TABLE IF NOT EXISTS old_ids (
    user_id INT,
    newsfeed_id INT
);

USE sp_users_db;

CREATE TABLE IF NOT EXISTS sp_users_subscriptions (
    sp_uid INT NOT NULL PRIMARY KEY,
    subscription TINYTEXT DEFAULT NULL,
    expire DATETIME DEFAULT NULL,
    used_trial BOOL DEFAULT 0
);

USE users_db;

CREATE TABLE IF NOT EXISTS users_configs (
    user_id INT NOT NULL PRIMARY KEY,
    sp_email TINYTEXT DEFAULT NULL,
    sp_token TINYTEXT DEFAULT NULL,
    sp_eid INT DEFAULT NULL,
    sp_uid INT DEFAULT NULL,
    prog_status BOOL NOT NULL DEFAULT 1,
    prog_open_shifts BOOL NOT NULL DEFAULT 1,
    prog_shift_offers BOOL NOT NULL DEFAULT 1,
    prog_news BOOL NOT NULL DEFAULT 0,
    prog_sleep FLOAT(3, 2) NOT NULL DEFAULT 5,
    shifts MEDIUMTEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS users_statistics (
    user_id INT NOT NULL PRIMARY KEY,
    shifted_shifts INT DEFAULT 0,
    shifted_hours FLOAT(8, 2) DEFAULT 0,
    earned FLOAT(9, 2) DEFAULT 0
);