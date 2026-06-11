SELECT
    'customers' AS table_name,
    count(*) AS row_count
FROM olist.customers
UNION ALL
SELECT 'geolocation', count(*) FROM olist.geolocation
UNION ALL
SELECT 'order_items', count(*) FROM olist.order_items
UNION ALL
SELECT 'order_payments', count(*) FROM olist.order_payments
UNION ALL
SELECT 'order_reviews', count(*) FROM olist.order_reviews
UNION ALL
SELECT 'orders', count(*) FROM olist.orders
UNION ALL
SELECT 'products', count(*) FROM olist.products
UNION ALL
SELECT 'sellers', count(*) FROM olist.sellers
UNION ALL
SELECT 'product_category_translation', count(*) FROM olist.product_category_translation
ORDER BY table_name;

SELECT
    coalesce(t.product_category_name_english, p.product_category_name, 'unknown') AS category,
    round(sum(oi.price), 2) AS sales_amount,
    count(DISTINCT oi.order_id) AS order_count
FROM olist.order_items AS oi
LEFT JOIN olist.products AS p
    ON p.product_id = oi.product_id
LEFT JOIN olist.product_category_translation AS t
    ON t.product_category_name = p.product_category_name
GROUP BY 1
ORDER BY sales_amount DESC
LIMIT 10;
