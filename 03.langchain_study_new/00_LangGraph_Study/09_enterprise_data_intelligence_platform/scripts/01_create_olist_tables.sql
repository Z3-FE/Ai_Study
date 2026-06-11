DROP SCHEMA IF EXISTS olist CASCADE;
CREATE SCHEMA olist;

CREATE TABLE olist.customers (
    customer_id text PRIMARY KEY,
    customer_unique_id text NOT NULL,
    customer_zip_code_prefix integer,
    customer_city text,
    customer_state text
);

CREATE TABLE olist.geolocation (
    geolocation_zip_code_prefix integer,
    geolocation_lat numeric(12, 8),
    geolocation_lng numeric(12, 8),
    geolocation_city text,
    geolocation_state text
);

CREATE TABLE olist.orders (
    order_id text PRIMARY KEY,
    customer_id text,
    order_status text,
    order_purchase_timestamp timestamp,
    order_approved_at timestamp,
    order_delivered_carrier_date timestamp,
    order_delivered_customer_date timestamp,
    order_estimated_delivery_date timestamp
);

CREATE TABLE olist.order_items (
    order_id text,
    order_item_id integer,
    product_id text,
    seller_id text,
    shipping_limit_date timestamp,
    price numeric(12, 2),
    freight_value numeric(12, 2)
);

CREATE TABLE olist.order_payments (
    order_id text,
    payment_sequential integer,
    payment_type text,
    payment_installments integer,
    payment_value numeric(12, 2)
);

CREATE TABLE olist.order_reviews (
    review_id text,
    order_id text,
    review_score integer,
    review_comment_title text,
    review_comment_message text,
    review_creation_date timestamp,
    review_answer_timestamp timestamp
);

CREATE TABLE olist.products (
    product_id text PRIMARY KEY,
    product_category_name text,
    product_name_length integer,
    product_description_length integer,
    product_photos_qty integer,
    product_weight_g integer,
    product_length_cm integer,
    product_height_cm integer,
    product_width_cm integer
);

CREATE TABLE olist.sellers (
    seller_id text PRIMARY KEY,
    seller_zip_code_prefix integer,
    seller_city text,
    seller_state text
);

CREATE TABLE olist.product_category_translation (
    product_category_name text PRIMARY KEY,
    product_category_name_english text
);

COMMENT ON SCHEMA olist IS 'Olist ecommerce dataset imported from Kaggle for the enterprise data intelligence platform.';
COMMENT ON TABLE olist.orders IS 'Order-level facts: status and lifecycle timestamps.';
COMMENT ON TABLE olist.order_items IS 'Order item facts: product, seller, price, and freight value.';
COMMENT ON TABLE olist.order_payments IS 'Payment facts: payment type, installments, and amount.';
COMMENT ON TABLE olist.order_reviews IS 'Customer review facts: score, title, message, and review timestamps.';
COMMENT ON TABLE olist.customers IS 'Customer dimension with anonymized IDs and location fields.';
COMMENT ON TABLE olist.products IS 'Product dimension. The source CSV uses the typo lenght; this table stores the corrected column name length.';
COMMENT ON TABLE olist.sellers IS 'Seller dimension with location fields.';
COMMENT ON TABLE olist.geolocation IS 'Zip-code-level latitude and longitude data.';
COMMENT ON TABLE olist.product_category_translation IS 'Product category Portuguese to English translation table.';
