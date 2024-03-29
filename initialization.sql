CREATE DATABASE IF NOT EXISTS keys_db;
CREATE DATABASE IF NOT EXISTS repeats_db;
CREATE DATABASE IF NOT EXISTS sp_users_db;
CREATE DATABASE IF NOT EXISTS users_db;

USE keys_db;

CREATE TABLE IF NOT EXISTS activation_keys (
    activation_key TINYTEXT,
    key_type TINYTEXT,
    key_days INT
);

USE repeats_db;

CREATE TABLE IF NOT EXISTS old_ids (
    user_id INT,
    item_id INT
);

USE sp_users_db;

CREATE TABLE IF NOT EXISTS sp_users_subscriptions (
    sp_uid INT NOT NULL PRIMARY KEY,
    subscription TINYTEXT DEFAULT NULL,
    expire DATETIME DEFAULT NULL,
    is_notified BOOL DEFAULT NULL,
    used_trial_btn BOOL DEFAULT 0,
    used_trial BOOL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sp_users_configs (
    sp_uid INT NOT NULL PRIMARY KEY,
    prog_status BOOL NOT NULL DEFAULT 0,
    prog_open_shifts BOOL NOT NULL DEFAULT 1,
    prog_shift_offers BOOL NOT NULL DEFAULT 1,
    prog_news BOOL NOT NULL DEFAULT 0,
    bike_status BOOL NOT NULL DEFAULT 1,
    ebike_status BOOL NOT NULL DEFAULT 1,
    scooter_status BOOL NOT NULL DEFAULT 0,
    car_status BOOL NOT NULL DEFAULT 0,
    prog_sleep FLOAT(3, 2) NOT NULL DEFAULT 5,
    prog_cutoff_time TINYINT NOT NULL DEFAULT 1,
    selection_mode BOOL NOT NULL DEFAULT 0,
    shifts MEDIUMTEXT
);

USE users_db;

CREATE TABLE IF NOT EXISTS users_auth (
    user_id BIGINT NOT NULL PRIMARY KEY,
    sp_email TINYTEXT DEFAULT NULL,
    sp_token TINYTEXT DEFAULT NULL,
    sp_eid INT DEFAULT NULL,
    sp_uid INT DEFAULT NULL,
    trusted BOOL DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS users_statistics (
    user_id BIGINT NOT NULL PRIMARY KEY,
    shifted_shifts INT DEFAULT 0,
    shifted_hours FLOAT(8, 2) DEFAULT 0,
    earned FLOAT(9, 2) DEFAULT 0
);
