#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${PROJECT_DIR}/data/raw/olist"
DB_NAME="${POSTGRES_DB:-enterprise_data_ai}"
ADMIN_DB="${POSTGRES_ADMIN_DB:-postgres}"

if [[ ! -d "${RAW_DIR}" ]]; then
  echo "Olist raw data directory not found: ${RAW_DIR}" >&2
  exit 1
fi

if ! psql -d "${ADMIN_DB}" -tAc "select 1 from pg_database where datname='${DB_NAME}'" | grep -q 1; then
  createdb "${DB_NAME}"
fi

psql -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${PROJECT_DIR}/scripts/01_create_olist_tables.sql"

psql -d "${DB_NAME}" -v ON_ERROR_STOP=1 <<SQL
\copy olist.customers FROM '${RAW_DIR}/olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.geolocation FROM '${RAW_DIR}/olist_geolocation_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.order_items FROM '${RAW_DIR}/olist_order_items_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.order_payments FROM '${RAW_DIR}/olist_order_payments_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.order_reviews FROM '${RAW_DIR}/olist_order_reviews_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.orders FROM '${RAW_DIR}/olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.products FROM '${RAW_DIR}/olist_products_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.sellers FROM '${RAW_DIR}/olist_sellers_dataset.csv' WITH (FORMAT csv, HEADER true, NULL '')
\copy olist.product_category_translation FROM '${RAW_DIR}/product_category_name_translation.csv' WITH (FORMAT csv, HEADER true, NULL '', ENCODING 'UTF8')

ANALYZE olist.customers;
ANALYZE olist.geolocation;
ANALYZE olist.order_items;
ANALYZE olist.order_payments;
ANALYZE olist.order_reviews;
ANALYZE olist.orders;
ANALYZE olist.products;
ANALYZE olist.sellers;
ANALYZE olist.product_category_translation;
SQL

echo "Imported Olist dataset into PostgreSQL database: ${DB_NAME}"
