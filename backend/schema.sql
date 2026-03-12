CREATE DATABASE IF NOT EXISTS trailmark CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE trailmark;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(191) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_email_role (email, role)
);

-- 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  interests JSON,
  budget_level VARCHAR(50) DEFAULT 'medium',
  travel_style VARCHAR(50) DEFAULT 'balanced',
  group_type VARCHAR(50) DEFAULT 'solo',
  fitness_level VARCHAR(50) DEFAULT 'medium',
  age_group VARCHAR(50) DEFAULT 'adult',
  has_children BOOLEAN DEFAULT FALSE,
  price_sensitivity FLOAT DEFAULT 0.5,
  cultural_preferences JSON,
  refined_interests JSON,
  preferred_categories JSON,
  budget_info JSON,
  fitness_info JSON,
  pace_preference VARCHAR(50) DEFAULT 'balanced',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_profiles_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 行程表
CREATE TABLE IF NOT EXISTS trips (
  id VARCHAR(100) NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  city VARCHAR(100) NOT NULL,
  title VARCHAR(255),
  days INT DEFAULT 3,
  start_date DATE,
  end_date DATE,
  status VARCHAR(50) DEFAULT 'Planning',
  itinerary JSON,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_trips_user_id (user_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
