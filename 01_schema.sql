-- ============================================
-- مشروع بيانات الاتصالات المصرية (Egypt Telecom)
-- قاعدة بيانات معدلة ومنظمة لإنشاء Diagrams
-- ============================================

-- إنشاء قاعدة البيانات الجديدة
CREATE DATABASE EgyptTelecomAnalysis;
GO

USE EgyptTelecomAnalysis;
GO

-- ============================================
-- 1. جدول ملخص المحافظات (يُنشأ أولاً)
-- ============================================
CREATE TABLE GovernorateSummary (
    governorate_en VARCHAR(50) PRIMARY KEY,
    governorate_ar NVARCHAR(50) NOT NULL,
    avg_d_kbps INT,
    avg_u_kbps INT,
    avg_lat_ms DECIMAL(6,1),
    avg_d_mbps DECIMAL(6,1),
    avg_u_mbps DECIMAL(6,1),
    total_tests INT,
    total_devices INT,
    tile_count INT,

    CONSTRAINT UQ_Governorate_AR UNIQUE (governorate_ar)
);
GO

-- ============================================
-- 2. جدول NetworkTiles
-- ============================================
CREATE TABLE NetworkTiles (
    tile_id INT IDENTITY(1,1) PRIMARY KEY,
    governorate_en VARCHAR(50) NOT NULL,
    avg_d_kbps INT,
    avg_u_kbps INT,
    avg_lat_ms DECIMAL(6,1),
    tests INT,
    devices INT,
    governorate_ar NVARCHAR(50),
    tile_lat DECIMAL(9,6),
    tile_lon DECIMAL(9,6),

    CONSTRAINT FK_NetworkTiles_Governorate
        FOREIGN KEY (governorate_en) 
        REFERENCES GovernorateSummary(governorate_en)
);
GO

-- ============================================
-- 3. جدول العملاء
-- ============================================
CREATE TABLE Customers (
    customer_id VARCHAR(10) PRIMARY KEY,
    operator VARCHAR(20),
    phone_prefix INT,
    governorate NVARCHAR(50),
    region VARCHAR(10),
    age INT,
    age_group VARCHAR(10),
    gender VARCHAR(10),
    plan_type VARCHAR(10),
    customer_segment VARCHAR(20),
    tenure_months INT,
    network_type VARCHAR(5),
    data_bundle VARCHAR(30),
    data_used_GB DECIMAL(10,2),
    voice_minutes INT,
    sms_count INT,
    monthly_revenue_EGP DECIMAL(10,2),
    recharge_frequency INT,
    device_tier VARCHAR(30),
    complaints_count INT,
    satisfaction_score INT,
    churn INT,
    registration_date DATE
);
GO
