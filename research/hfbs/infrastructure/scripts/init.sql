-- ============================================================
-- HFBS — PostgreSQL Init Script
-- Создаёт две базы: основная (hfbs_db) и аналитическая (hfbs_analytics)
-- ============================================================

-- Основная база уже создана через POSTGRES_DB
-- Создаём аналитическую базу
CREATE DATABASE hfbs_analytics;
GRANT ALL PRIVILEGES ON DATABASE hfbs_analytics TO hfbs;
