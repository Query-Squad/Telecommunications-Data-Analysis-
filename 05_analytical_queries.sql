USE EgyptTelecomAnalysis;
GO


-- ============================================
-- التأكد من نجاح استيراد البيانات
-- ============================================
SELECT COUNT(*) AS total_customers FROM Customers;
SELECT COUNT(*) AS total_tiles FROM NetworkTiles;
SELECT COUNT(*) AS total_governorates FROM GovernorateSummary;
GO

-- ============================================
-- استعلامات تحليلية بسيطة
-- ============================================

-- عدد العملاء لكل شركة اتصالات
SELECT operator, COUNT(*) AS total_customers
FROM Customers
GROUP BY operator
ORDER BY total_customers DESC;
GO

-- متوسط الإيراد الشهري لكل فئة عملاء
SELECT customer_segment, AVG(monthly_revenue_EGP) AS avg_revenue
FROM Customers
GROUP BY customer_segment
ORDER BY avg_revenue DESC;
GO

-- نسبة العملاء اللي عملوا churn لكل محافظة
SELECT governorate,
       COUNT(*) AS total_customers,
       SUM(churn) AS churned_customers,
       CAST(SUM(churn) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS churn_rate_percent
FROM Customers
GROUP BY governorate
ORDER BY churn_rate_percent DESC;
GO

-- سرعة التحميل والرفع لكل محافظة (من جدول الملخص)
SELECT governorate_en, avg_d_mbps, avg_u_mbps, avg_lat_ms
FROM GovernorateSummary
ORDER BY avg_d_mbps DESC;
GO
USE EgyptTelecomAnalysis;
GO

-- المحافظات الموجودة في NetworkTiles لكنها غير موجودة في GovernorateSummary
SELECT DISTINCT nt.governorate_en AS Missing_Governorate
FROM NetworkTiles nt
LEFT JOIN GovernorateSummary gs ON nt.governorate_en = gs.governorate_en
WHERE gs.governorate_en IS NULL;

USE EgyptTelecomAnalysis;
GO

-- ============================================
-- 1. تحليل Churn (أهم جزء في التليكوم)
-- ============================================

-- churn rate حسب الـ Operator
SELECT 
    operator,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned,
    CAST(SUM(churn) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS churn_rate_percent,
    AVG(tenure_months) AS avg_tenure
FROM Customers 
GROUP BY operator
ORDER BY churn_rate_percent DESC;

-- churn rate حسب الفئة العمرية
SELECT 
    age_group,
    COUNT(*) AS total,
    SUM(churn) AS churned,
    CAST(SUM(churn)*100.0/COUNT(*) AS DECIMAL(5,2)) AS churn_rate
FROM Customers
GROUP BY age_group
ORDER BY churn_rate DESC;

-- churn حسب نوع الشبكة (Network Type)
SELECT 
    network_type,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned,
    AVG(monthly_revenue_EGP) AS avg_revenue
FROM Customers
GROUP BY network_type
ORDER BY churned DESC;

-- ============================================
-- 2. تحليل الإيرادات
-- ============================================

-- أعلى 10 عملاء من حيث الإيراد الشهري
SELECT TOP 10 
    customer_id, operator, governorate, 
    monthly_revenue_EGP, data_used_GB, voice_minutes
FROM Customers
ORDER BY monthly_revenue_EGP DESC;

-- متوسط الإيراد حسب نوع الجهاز (Device Tier)
SELECT 
    device_tier,
    COUNT(*) AS customer_count,
    AVG(monthly_revenue_EGP) AS avg_revenue,
    AVG(data_used_GB) AS avg_data_usage
FROM Customers
GROUP BY device_tier
ORDER BY avg_revenue DESC;

-- إجمالي الإيراد الشهري لكل شركة
SELECT 
    operator,
    COUNT(*) AS customers,
    SUM(monthly_revenue_EGP) AS total_monthly_revenue,
    AVG(monthly_revenue_EGP) AS avg_revenue_per_customer
FROM Customers
GROUP BY operator
ORDER BY total_monthly_revenue DESC;

-- ============================================
-- 3. تحليل الاستخدام (Usage)
-- ============================================

-- متوسط استخدام الداتا والمكالمات حسب الـ Age Group
SELECT 
    age_group,
    AVG(data_used_GB) AS avg_data_GB,
    AVG(voice_minutes) AS avg_voice_min,
    AVG(sms_count) AS avg_sms,
    AVG(monthly_revenue_EGP) AS avg_revenue
FROM Customers
GROUP BY age_group
ORDER BY avg_data_GB DESC;

-- العملاء اللي بيستهلكوا داتا عالية جداً
SELECT 
    customer_id, operator, governorate, data_used_GB, 
    data_bundle, monthly_revenue_EGP
FROM Customers
WHERE data_used_GB > 20
ORDER BY data_used_GB DESC;

-- ============================================
-- 4. تحليل حسب المحافظة (مع ربط الشبكة)
-- ============================================

-- جودة الشبكة + نسبة Churn لكل محافظة
SELECT 
    g.governorate_en,
    g.avg_d_mbps AS download_mbps,
    g.avg_u_mbps AS upload_mbps,
    g.avg_lat_ms AS latency,
    COUNT(c.customer_id) AS total_customers,
    SUM(c.churn) AS churned,
    CAST(SUM(c.churn)*100.0/COUNT(c.customer_id) AS DECIMAL(5,2)) AS churn_rate
FROM GovernorateSummary g
LEFT JOIN Customers c ON g.governorate_ar = c.governorate
GROUP BY g.governorate_en, g.avg_d_mbps, g.avg_u_mbps, g.avg_lat_ms
ORDER BY churn_rate DESC;

-- ============================================
-- 5. استعلامات إضافية مفيدة
-- ============================================

-- توزيع العملاء حسب نوع الخطة (Prepaid / Postpaid)
SELECT 
    plan_type,
    customer_segment,
    COUNT(*) AS count,
    AVG(tenure_months) AS avg_tenure_months
FROM Customers
GROUP BY plan_type, customer_segment
ORDER BY count DESC;

-- العملاء اللي عندهم شكاوى كتير
SELECT 
    operator, governorate,
    AVG(complaints_count) AS avg_complaints,
    AVG(satisfaction_score) AS avg_satisfaction
FROM Customers
GROUP BY operator, governorate
HAVING AVG(complaints_count) > 2
ORDER BY avg_complaints DESC;

-- تأثير مدة الاشتراك (Tenure) على Churn
SELECT 
    CASE 
        WHEN tenure_months <= 6 THEN '0-6 months'
        WHEN tenure_months <= 12 THEN '7-12 months'
        WHEN tenure_months <= 24 THEN '13-24 months'
        ELSE '24+ months'
    END AS tenure_group,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned,
    CAST(SUM(churn)*100.0/COUNT(*) AS DECIMAL(5,2)) AS churn_rate
FROM Customers
GROUP BY 
    CASE 
        WHEN tenure_months <= 6 THEN '0-6 months'
        WHEN tenure_months <= 12 THEN '7-12 months'
        WHEN tenure_months <= 24 THEN '13-24 months'
        ELSE '24+ months'
    END
ORDER BY churn_rate DESC;

-- أكثر 5 محافظات من حيث عدد العملاء
SELECT TOP 5 
    governorate,
    COUNT(*) AS customer_count,
    AVG(monthly_revenue_EGP) AS avg_revenue
FROM Customers
GROUP BY governorate
ORDER BY customer_count DESC;

USE EgyptTelecomAnalysis;
GO

-- ============================================
-- 1. تحليل جغرافي + ديموغرافي
-- ============================================

-- توزيع العملاء Urban vs Rural مع متوسط الإيراد
SELECT 
    region,
    COUNT(*) AS total_customers,
    AVG(monthly_revenue_EGP) AS avg_revenue,
    AVG(data_used_GB) AS avg_data_usage,
    CAST(SUM(churn)*100.0/COUNT(*) AS DECIMAL(5,2)) AS churn_rate
FROM Customers
GROUP BY region
ORDER BY avg_revenue DESC;

-- أفضل 10 محافظات من حيث رضا العملاء (Satisfaction)
SELECT TOP 10
    governorate,
    COUNT(*) AS customers,
    AVG(satisfaction_score) AS avg_satisfaction,
    AVG(complaints_count) AS avg_complaints
FROM Customers
GROUP BY governorate
ORDER BY avg_satisfaction DESC;

-- ============================================
-- 2. تحليل نوع الجهاز والحزم
-- ============================================

-- أداء كل نوع جهاز (Device Tier)
SELECT 
    device_tier,
    COUNT(*) AS customer_count,
    AVG(data_used_GB) AS avg_data,
    AVG(voice_minutes) AS avg_voice,
    AVG(monthly_revenue_EGP) AS avg_revenue,
    CAST(AVG(satisfaction_score) AS DECIMAL(4,1)) AS avg_satisfaction
FROM Customers
GROUP BY device_tier
ORDER BY avg_revenue DESC;

-- كفاءة الحزم (Data Usage vs Bundle)
SELECT 
    data_bundle,
    COUNT(*) AS users,
    AVG(data_used_GB) AS avg_used,
    AVG(data_used_GB) * 100.0 / 
        (CASE 
            WHEN data_bundle LIKE '%10GB%' THEN 10
            WHEN data_bundle LIKE '%20GB%' THEN 20
            WHEN data_bundle LIKE '%5GB%' THEN 5
            WHEN data_bundle LIKE '%1GB%' THEN 1
            ELSE 10 
         END) AS usage_efficiency_percent
FROM Customers
GROUP BY data_bundle
ORDER BY usage_efficiency_percent DESC;

-- ============================================
-- 3. تحليل الوقت (Registration Date)
-- ============================================

-- عدد العملاء الجدد والـ Churn حسب الشهر
SELECT 
    FORMAT(registration_date, 'yyyy-MM') AS registration_month,
    COUNT(*) AS new_customers,
    SUM(churn) AS churned,
    CAST(SUM(churn)*100.0/COUNT(*) AS DECIMAL(5,2)) AS churn_rate
FROM Customers
GROUP BY FORMAT(registration_date, 'yyyy-MM')
ORDER BY registration_month DESC;

-- متوسط العمر الزمني للعملاء (Tenure) حسب الـ Operator
SELECT 
    operator,
    AVG(tenure_months) AS avg_tenure_months,
    MIN(tenure_months) AS min_tenure,
    MAX(tenure_months) AS max_tenure
FROM Customers
GROUP BY operator
ORDER BY avg_tenure_months DESC;

-- ============================================
-- 4. تحليل متقدم (باستخدام JOIN)
-- ============================================

-- جودة الشبكة + رضا العملاء + Churn (أقوى استعلام)
SELECT 
    g.governorate_en AS Governorate,
    g.avg_d_mbps AS Download_Mbps,
    g.avg_lat_ms AS Latency_ms,
    COUNT(c.customer_id) AS Total_Customers,
    AVG(c.satisfaction_score) AS Avg_Satisfaction,
    CAST(AVG(c.complaints_count) AS DECIMAL(4,2)) AS Avg_Complaints,
    CAST(SUM(c.churn)*100.0/COUNT(c.customer_id) AS DECIMAL(5,2)) AS Churn_Rate
FROM GovernorateSummary g
LEFT JOIN Customers c ON g.governorate_ar = c.governorate
GROUP BY g.governorate_en, g.avg_d_mbps, g.avg_lat_ms
ORDER BY Avg_Satisfaction DESC, Churn_Rate ASC;

-- ============================================
-- 5. استعلامات إضافية قوية
-- ============================================

-- العملاء High Value (إيراد عالي + داتا عالية)
SELECT 
    customer_id, operator, governorate, age_group,
    monthly_revenue_EGP, data_used_GB, satisfaction_score
FROM Customers
WHERE monthly_revenue_EGP > 150 AND data_used_GB > 15
ORDER BY monthly_revenue_EGP DESC;

-- مقارنة Prepaid vs Postpaid
SELECT 
    plan_type,
    COUNT(*) AS customers,
    AVG(monthly_revenue_EGP) AS avg_revenue,
    AVG(tenure_months) AS avg_tenure,
    CAST(SUM(churn)*100.0/COUNT(*) AS DECIMAL(5,2)) AS churn_rate
FROM Customers
GROUP BY plan_type;

-- أكثر Operator سيطرة في كل محافظة
SELECT 
    governorate,
    operator,
    COUNT(*) AS customer_count,
    RANK() OVER (PARTITION BY governorate ORDER BY COUNT(*) DESC) AS rank_in_governorate
FROM Customers
GROUP BY governorate, operator
ORDER BY governorate, rank_in_governorate;

-- العملاء الـ Risky (عالي الشكاوى + منخفض الرضا)
SELECT 
    customer_id, operator, governorate, complaints_count, satisfaction_score, churn
FROM Customers
WHERE complaints_count >= 3 AND satisfaction_score <= 2
