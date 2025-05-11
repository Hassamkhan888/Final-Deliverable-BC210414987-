CREATE DATABASE restaurant_db;
USE restaurant_db;

CREATE TABLE IF NOT EXISTS customer_info_cache (
    session_id VARCHAR(255) PRIMARY KEY,
    customer_name VARCHAR(100),
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    status ENUM('Pending','Confirmed','Preparing','On the way','Delivered','Cancelled') NOT NULL DEFAULT 'Pending',
    estimated_time VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB AUTO_INCREMENT=1000;


CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    food_item VARCHAR(100) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `menu_items` (
  `item_id` INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each menu item
  `name` VARCHAR(50) NOT NULL UNIQUE,        -- Name of the menu item (e.g., "pepsi")
  `price` DECIMAL(10,2) NOT NULL,            -- Price of the item
  `in_stock` BOOLEAN DEFAULT TRUE,           -- Availability status (TRUE if in stock)
  `category` ENUM('Appetizers','Main Course','Desserts','Beverages') NOT NULL,  -- Item category
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Date and time the item was added to the menu
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `menu_items` (`name`, `price`, `category`, `in_stock`) VALUES

('pepsi', 100, 'Beverages', 1),
('chicken_biryani', 400, 'Main Course', 1),
('samosa', 80, 'Appetizers', 0),
('chocolate_lava', 300, 'Desserts', 1),
('beef_burger', 350, 'Main Course', 1),
('mutton_karahi', 500, 'Main Course', 1),
('garlic_naan', 70, 'Main Course', 1),
('seekh_kebab', 300, 'Main Course', 1),
('haleem', 350, 'Main Course', 1),
('nihari', 450, 'Main Course', 1),
('paya', 400, 'Main Course', 1),
('chapli_kebab', 250, 'Main Course', 1),
('kheer', 180, 'Desserts', 1),
('jalebi', 150, 'Desserts', 1),
('lassi', 120, 'Beverages', 1),
('rooh_afza', 90, 'Beverages', 1),
('zinger_burger', 380, 'Main Course', 1),
('fish_fry', 450, 'Main Course', 1),
('malai_boti', 380, 'Main Course', 1),
('rasmalai', 200, 'Desserts', 1),
('fruit_chat', 180, 'Appetizers', 1),
('pakora', 100, 'Appetizers', 1),
('shami_kebab', 220, 'Main Course', 1);


CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    customer_name VARCHAR(100),
    phone VARCHAR(20),
    user_message TEXT NOT NULL,
    issue_category VARCHAR(50) NOT NULL,
    status ENUM('open','in_progress','resolved','closed') DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    guests INT NOT NULL,
    reservation_date DATE NOT NULL,
    reservation_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS customer_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255),
    customer_name VARCHAR(100),
    phone VARCHAR(20),
    feedback_text TEXT NOT NULL,
    source_platform VARCHAR(50) DEFAULT 'chatbot',
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_feedback_session (session_id)
) ENGINE=InnoDB;




select * From reservations;
Select * From support_tickets;
Select * From menu_items;
SELECT * FROM orders;
SELECT * FROM order_items;
Select * from customer_feedback;


