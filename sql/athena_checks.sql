-- Checks to run in Athena after the job and the crawler have finished.
-- Workgroup: olist-pipeline (the one in template.yaml). Database: olist.
-- Run each query on its own. Each one says what a good answer looks like.


-- 1. Rows in each table. The order count is the number I compared with the source files.
SELECT 'orders' AS table_name, COUNT(*) AS row_count FROM olist.orders
UNION ALL SELECT 'customers', COUNT(*) FROM olist.customers
UNION ALL SELECT 'order_items', COUNT(*) FROM olist.order_items
UNION ALL SELECT 'payments', COUNT(*) FROM olist.payments
UNION ALL SELECT 'products', COUNT(*) FROM olist.products
UNION ALL SELECT 'reviews', COUNT(*) FROM olist.reviews
UNION ALL SELECT 'sellers', COUNT(*) FROM olist.sellers;


-- 2. Duplicates. Every query here should return no rows.
SELECT order_id, COUNT(*) AS copies
FROM olist.orders
GROUP BY order_id
HAVING COUNT(*) > 1;

SELECT customer_id, COUNT(*) AS copies
FROM olist.customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

SELECT product_id, COUNT(*) AS copies
FROM olist.products
GROUP BY product_id
HAVING COUNT(*) > 1;

SELECT seller_id, COUNT(*) AS copies
FROM olist.sellers
GROUP BY seller_id
HAVING COUNT(*) > 1;

SELECT order_id, order_item_id, COUNT(*) AS copies
FROM olist.order_items
GROUP BY order_id, order_item_id
HAVING COUNT(*) > 1;


-- 3. Rows that point at something missing. The count should be 0 for each.
SELECT COUNT(*) AS orders_without_customer
FROM olist.orders o
LEFT JOIN olist.customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

SELECT COUNT(*) AS items_without_order
FROM olist.order_items i
LEFT JOIN olist.orders o ON i.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS items_without_product
FROM olist.order_items i
LEFT JOIN olist.products p ON i.product_id = p.product_id
WHERE p.product_id IS NULL;

SELECT COUNT(*) AS items_without_seller
FROM olist.order_items i
LEFT JOIN olist.sellers s ON i.seller_id = s.seller_id
WHERE s.seller_id IS NULL;

SELECT COUNT(*) AS payments_without_order
FROM olist.payments p
LEFT JOIN olist.orders o ON p.order_id = o.order_id
WHERE o.order_id IS NULL;

SELECT COUNT(*) AS reviews_without_order
FROM olist.reviews r
LEFT JOIN olist.orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL;


-- 4. Missing key values. Should be 0.
SELECT COUNT(*) AS orders_missing_a_key
FROM olist.orders
WHERE order_id IS NULL OR customer_id IS NULL;


-- 5. A look at the data itself.
SELECT order_status, COUNT(*) AS orders
FROM olist.orders
GROUP BY order_status
ORDER BY orders DESC;

SELECT substr(order_purchase_timestamp, 1, 7) AS month,
       COUNT(*) AS orders
FROM olist.orders
GROUP BY 1
ORDER BY 1;
