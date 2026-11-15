CREATE DATABASE IF NOT EXISTS inventorypro
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE inventorypro;

CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_name VARCHAR(150) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(30)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE,
    phone VARCHAR(30)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category_id INT NOT NULL,
    supplier_id INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 5,
    CONSTRAINT fk_products_category FOREIGN KEY (category_id)
        REFERENCES categories(category_id) ON DELETE RESTRICT,
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    CONSTRAINT chk_products_price CHECK (price >= 0),
    CONSTRAINT chk_products_quantity CHECK (quantity >= 0),
    CONSTRAINT chk_products_reorder CHECK (reorder_level >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_sales_customer FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sale_items (
    sale_item_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_sale_items_sale FOREIGN KEY (sale_id)
        REFERENCES sales(sale_id) ON DELETE CASCADE,
    CONSTRAINT fk_sale_items_product FOREIGN KEY (product_id)
        REFERENCES products(product_id) ON DELETE RESTRICT,
    CONSTRAINT chk_sale_items_qty CHECK (quantity > 0),
    CONSTRAINT chk_sale_items_price CHECK (unit_price >= 0),
    UNIQUE KEY uq_sale_product (sale_id, product_id)
) ENGINE=InnoDB;
