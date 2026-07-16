import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------
# Page config
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Egypt Telecom Analytics",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = "data.xlsx"

# ---------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------
@st.cache_data
def load_customers():
    df = pd.read_excel(DATA_PATH, sheet_name="egypt_telecom_dataset-1")
    return df

@st.cache_data
def load_calibrated():
    df = pd.read_excel(DATA_PATH, sheet_name="egypt_telecom_calibrated_5000")
    return df

@st.cache_data
def load_tiles():
    return pd.read_excel(DATA_PATH, sheet_name="tiles_raw")

@st.cache_data
def load_gov_summary():
    return pd.read_excel(DATA_PATH, sheet_name="gov_summary")


# ---------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------
def kpi_card(label, value, delta=None, help_text=None):
    st.metric(label, value, delta=delta, help=help_text)


PLOTLY_TEMPLATE = "plotly_white"


# =================================================================
# DASHBOARD 1 — Customer & Revenue Overview
# =================================================================
def dashboard_customers():
    df = load_customers().copy()

    st.title("📊 نظرة عامة على العملاء والإيرادات")
    st.caption("مصدر البيانات: egypt_telecom_dataset-1 · 5,500 عميل")

    # ---- Filters ----
    with st.sidebar:
        st.header("🔍 الفلاتر")
        operators = st.multiselect("المشغل", sorted(df["operator"].unique()), default=list(df["operator"].unique()))
        governorates = st.multiselect("المحافظة", sorted(df["governorate"].unique()))
        plan_types = st.multiselect("نوع الخط", sorted(df["plan_type"].unique()), default=list(df["plan_type"].unique()))
        segments = st.multiselect("شريحة العميل", sorted(df["customer_segment"].unique()), default=list(df["customer_segment"].unique()))

    fdf = df[df["operator"].isin(operators) & df["plan_type"].isin(plan_types) & df["customer_segment"].isin(segments)]
    if governorates:
        fdf = fdf[fdf["governorate"].isin(governorates)]

    if fdf.empty:
        st.warning("لا توجد بيانات مطابقة للفلاتر المختارة.")
        return

    # ---- KPIs ----
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("عدد العملاء", f"{len(fdf):,}")
    with c2:
        kpi_card("متوسط الإيراد الشهري", f"{fdf['monthly_revenue_EGP'].mean():,.0f} ج.م")
    with c3:
        churn_rate = fdf["churn"].mean() * 100
        kpi_card("معدل التسرب (Churn)", f"{churn_rate:.1f}%")
    with c4:
        kpi_card("متوسط الرضا", f"{fdf['satisfaction_score'].mean():.1f} / 5")
    with c5:
        kpi_card("متوسط مدة الاشتراك", f"{fdf['tenure_months'].mean():.0f} شهر")

    st.divider()

    # ---- Row 1: Revenue by operator, customers by governorate ----
    col1, col2 = st.columns(2)
    with col1:
        rev_by_op = fdf.groupby("operator", as_index=False)["monthly_revenue_EGP"].mean().sort_values("monthly_revenue_EGP", ascending=False)
        fig = px.bar(rev_by_op, x="operator", y="monthly_revenue_EGP", color="operator",
                     title="متوسط الإيراد الشهري حسب المشغل", template=PLOTLY_TEMPLATE,
                     labels={"monthly_revenue_EGP": "الإيراد (ج.م)", "operator": "المشغل"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        cust_by_gov = fdf["governorate"].value_counts().reset_index()
        cust_by_gov.columns = ["governorate", "count"]
        cust_by_gov = cust_by_gov.sort_values("count", ascending=False).head(10)
        fig = px.bar(cust_by_gov, x="count", y="governorate", orientation="h",
                     title="أعلى 10 محافظات بعدد العملاء", template=PLOTLY_TEMPLATE,
                     labels={"count": "عدد العملاء", "governorate": "المحافظة"})
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # ---- Row 2: Age distribution, churn by segment ----
    col3, col4 = st.columns(2)
    with col3:
        fig = px.histogram(fdf, x="age", nbins=20, color="gender", barmode="overlay",
                            title="توزيع الأعمار حسب النوع", template=PLOTLY_TEMPLATE,
                            labels={"age": "العمر", "count": "العدد"})
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        churn_by_seg = fdf.groupby("customer_segment", as_index=False)["churn"].mean()
        churn_by_seg["churn"] *= 100
        fig = px.bar(churn_by_seg.sort_values("churn", ascending=False), x="customer_segment", y="churn",
                     title="معدل التسرب حسب شريحة العميل (%)", template=PLOTLY_TEMPLATE,
                     labels={"customer_segment": "الشريحة", "churn": "نسبة التسرب %"},
                     color="churn", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

    # ---- Row 3: Data usage trend & plan type split ----
    col5, col6 = st.columns(2)
    with col5:
        usage_by_bundle = fdf.groupby("data_bundle", as_index=False)["data_used_GB"].mean().sort_values("data_used_GB", ascending=False)
        fig = px.bar(usage_by_bundle, x="data_bundle", y="data_used_GB",
                     title="متوسط استهلاك البيانات حسب الباقة", template=PLOTLY_TEMPLATE,
                     labels={"data_bundle": "الباقة", "data_used_GB": "الاستهلاك (GB)"})
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        plan_split = fdf["plan_type"].value_counts().reset_index()
        plan_split.columns = ["plan_type", "count"]
        fig = px.pie(plan_split, names="plan_type", values="count", hole=0.45,
                     title="توزيع نوع الخط (مسبق/فوترة)", template=PLOTLY_TEMPLATE)
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔎 عرض البيانات الخام"):
        st.dataframe(fdf, use_container_width=True)


# =================================================================
# DASHBOARD 2 — Network Performance by Governorate
# =================================================================
def dashboard_network():
    tiles = load_tiles().copy()
    gov = load_gov_summary().copy()

    st.title("📶 أداء الشبكة حسب المحافظة")
    st.caption("مصدر البيانات: tiles_raw (965 نقطة قياس) · gov_summary (27 محافظة)")

    with st.sidebar:
        st.header("🔍 الفلاتر")
        selected_govs = st.multiselect("اختر محافظات للمقارنة", sorted(gov["governorate_en"].unique()))

    gdf = gov[gov["governorate_en"].isin(selected_govs)] if selected_govs else gov

    # ---- KPIs ----
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("متوسط سرعة التنزيل", f"{gdf['avg_d_mbps'].mean():.1f} Mbps")
    with c2:
        kpi_card("متوسط سرعة الرفع", f"{gdf['avg_u_mbps'].mean():.1f} Mbps")
    with c3:
        kpi_card("متوسط زمن الاستجابة", f"{gdf['avg_lat_ms'].mean():.0f} ms")
    with c4:
        kpi_card("إجمالي الاختبارات", f"{int(gdf['total_tests'].sum()):,}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        top = gov.sort_values("avg_d_mbps", ascending=False)
        fig = px.bar(top, x="avg_d_mbps", y="governorate_en", orientation="h",
                     title="متوسط سرعة التنزيل حسب المحافظة (Mbps)", template=PLOTLY_TEMPLATE,
                     labels={"avg_d_mbps": "سرعة التنزيل (Mbps)", "governorate_en": "المحافظة"},
                     color="avg_d_mbps", color_continuous_scale="Blues")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=650)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(gov, x="avg_d_mbps", y="avg_lat_ms", size="total_tests", color="avg_u_mbps",
                          hover_name="governorate_en", title="سرعة التنزيل مقابل زمن الاستجابة",
                          labels={"avg_d_mbps": "سرعة التنزيل (Mbps)", "avg_lat_ms": "زمن الاستجابة (ms)", "avg_u_mbps": "سرعة الرفع (Mbps)"},
                          template=PLOTLY_TEMPLATE, color_continuous_scale="Teal")
        st.plotly_chart(fig, use_container_width=True)

        best = gov.loc[gov["avg_d_mbps"].idxmax(), "governorate_en"]
        worst = gov.loc[gov["avg_d_mbps"].idxmin(), "governorate_en"]
        st.info(f"🏆 أفضل أداء تنزيل: **{best}** · 🐌 أقل أداء تنزيل: **{worst}**")

    st.subheader("🗺️ خريطة نقاط القياس")
    fig = px.scatter_mapbox(
        tiles, lat="tile_lat", lon="tile_lon", color="avg_d_kbps", size="tests",
        hover_name="governorate_en", zoom=4.6, height=550,
        color_continuous_scale="Turbo", mapbox_style="open-street-map",
        labels={"avg_d_kbps": "سرعة التنزيل (Kbps)"},
        title="توزيع نقاط قياس الشبكة في مصر"
    )
    fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔎 عرض ملخص المحافظات (gov_summary)"):
        st.dataframe(gov.sort_values("avg_d_mbps", ascending=False), use_container_width=True)


# =================================================================
# DASHBOARD 3 — Churn Analysis
# =================================================================
def dashboard_churn():
    df = load_calibrated().copy()

    st.title("⚠️ تحليل التسرب (Churn Analysis)")
    st.caption("مصدر البيانات: egypt_telecom_calibrated_5000 · 5,000 عميل")

    with st.sidebar:
        st.header("🔍 الفلاتر")
        operators = st.multiselect("المشغل", sorted(df["operator"].unique()), default=list(df["operator"].unique()), key="churn_op")
        segments = st.multiselect("شريحة العميل", sorted(df["customer_segment"].unique()), default=list(df["customer_segment"].unique()), key="churn_seg")

    fdf = df[df["operator"].isin(operators) & df["customer_segment"].isin(segments)]
    if fdf.empty:
        st.warning("لا توجد بيانات مطابقة للفلاتر المختارة.")
        return

    churned = fdf[fdf["churn"] == 1]
    retained = fdf[fdf["churn"] == 0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("معدل التسرب الإجمالي", f"{fdf['churn'].mean()*100:.1f}%")
    with c2:
        kpi_card("عدد العملاء المتسربين", f"{len(churned):,}")
    with c3:
        kpi_card("متوسط الشكاوى (متسرب)", f"{churned['complaints_count'].mean():.1f}", help_text=f"مقابل {retained['complaints_count'].mean():.1f} للعملاء الباقين")
    with c4:
        kpi_card("متوسط الرضا (متسرب)", f"{churned['satisfaction_score'].mean():.1f} / 5", help_text=f"مقابل {retained['satisfaction_score'].mean():.1f} للعملاء الباقين")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        churn_by_seg = fdf.groupby("customer_segment", as_index=False)["churn"].mean()
        churn_by_seg["churn"] *= 100
        fig = px.bar(churn_by_seg.sort_values("churn", ascending=False), x="customer_segment", y="churn",
                     title="معدل التسرب حسب الشريحة (%)", template=PLOTLY_TEMPLATE,
                     labels={"customer_segment": "الشريحة", "churn": "نسبة التسرب %"},
                     color="churn", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        churn_by_complaints = fdf.groupby("complaints_count", as_index=False)["churn"].mean()
        churn_by_complaints["churn"] *= 100
        fig = px.line(churn_by_complaints, x="complaints_count", y="churn", markers=True,
                      title="علاقة عدد الشكاوى بمعدل التسرب", template=PLOTLY_TEMPLATE,
                      labels={"complaints_count": "عدد الشكاوى", "churn": "نسبة التسرب %"})
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig = px.box(fdf, x="churn", y="satisfaction_score", color="churn",
                     title="توزيع درجة الرضا حسب حالة التسرب", template=PLOTLY_TEMPLATE,
                     labels={"churn": "تسرب (0=لا, 1=نعم)", "satisfaction_score": "درجة الرضا"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        churn_by_device = fdf.groupby("device_tier", as_index=False)["churn"].mean()
        churn_by_device["churn"] *= 100
        fig = px.bar(churn_by_device.sort_values("churn", ascending=False), x="device_tier", y="churn",
                     title="معدل التسرب حسب فئة الجهاز (%)", template=PLOTLY_TEMPLATE,
                     labels={"device_tier": "فئة الجهاز", "churn": "نسبة التسرب %"},
                     color="churn", color_continuous_scale="Oranges")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📌 التسرب مقابل مدة الاشتراك ومحفظة الدفع الإلكتروني")
    col5, col6 = st.columns(2)
    with col5:
        fig = px.histogram(fdf, x="tenure_months", color="churn", barmode="overlay", nbins=20,
                            title="مدة الاشتراك حسب حالة التسرب", template=PLOTLY_TEMPLATE,
                            labels={"tenure_months": "مدة الاشتراك (شهر)", "churn": "تسرب"})
        st.plotly_chart(fig, use_container_width=True)
    with col6:
        ewallet_churn = fdf.groupby("has_ewallet", as_index=False)["churn"].mean()
        ewallet_churn["churn"] *= 100
        ewallet_churn["has_ewallet"] = ewallet_churn["has_ewallet"].map({0: "بدون محفظة إلكترونية", 1: "لديه محفظة إلكترونية"})
        fig = px.bar(ewallet_churn, x="has_ewallet", y="churn",
                     title="معدل التسرب حسب استخدام المحفظة الإلكترونية (%)", template=PLOTLY_TEMPLATE,
                     labels={"has_ewallet": "", "churn": "نسبة التسرب %"})
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔎 عرض البيانات الخام"):
        st.dataframe(fdf, use_container_width=True)


# =================================================================
# NAVIGATION
# =================================================================
PAGES = {
    "📊 العملاء والإيرادات": dashboard_customers,
    "📶 أداء الشبكة": dashboard_network,
    "⚠️ تحليل التسرب": dashboard_churn,
}

st.sidebar.title("📡 Egypt Telecom Analytics")
choice = st.sidebar.radio("اختر الداشبورد", list(PAGES.keys()))
st.sidebar.divider()

PAGES[choice]()
