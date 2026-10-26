import os

import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI


def clean_data(df):
    """Create a cleaned copy and return a cleaning summary."""
    original_rows = len(df)
    original_missing = int(df.isna().sum().sum())

    cleaned_df = df.copy().drop_duplicates().copy()

    numeric_columns = cleaned_df.select_dtypes(include="number").columns
    for column in numeric_columns:
        if cleaned_df[column].isna().any():
            median_value = cleaned_df[column].median()
            cleaned_df[column] = cleaned_df[column].fillna(median_value)

    text_columns = cleaned_df.select_dtypes(
        include=["object", "string", "category"]
    ).columns
    for column in text_columns:
        cleaned_df[column] = cleaned_df[column].fillna("Unknown")

    summary = {
        "original_rows": original_rows,
        "cleaned_rows": len(cleaned_df),
        "duplicates_removed": original_rows - len(df.drop_duplicates()),
        "missing_values_before": original_missing,
        "missing_values_after": int(cleaned_df.isna().sum().sum()),
    }
    return cleaned_df, summary


def answer_question(df, question):
    """Answer common business questions using calculations from the dataset."""
    q = question.lower().strip()
    if not q:
        return "Please enter a question."

    if "missing" in q or "null" in q:
        missing = df.isna().sum()
        missing = missing[missing > 0]
        if missing.empty:
            return "There are no missing values in this dataset."
        return "Missing values by column:\n" + missing.to_string()

    if "duplicate" in q:
        return f"The dataset contains {int(df.duplicated().sum())} duplicate rows."

    if "profit" in q and "region" in q:
        if not {"Region", "Profit_GBP"}.issubset(df.columns):
            return "This dataset needs Region and Profit_GBP columns."
        result = df.groupby("Region")["Profit_GBP"].sum().sort_values(ascending=False)
        return f"Highest-profit region: {result.index[0]} (£{result.iloc[0]:,.2f}).\n\nProfit by region:\n{result.to_string()}"

    if "profit" in q and "product" in q:
        if not {"Product", "Profit_GBP"}.issubset(df.columns):
            return "This dataset needs Product and Profit_GBP columns."
        result = df.groupby("Product")["Profit_GBP"].sum().sort_values(ascending=False)
        return f"Most profitable product: {result.index[0]} (£{result.iloc[0]:,.2f}).\n\nProfit by product:\n{result.to_string()}"

    if "revenue" in q and "product" in q:
        if not {"Product", "Revenue_GBP"}.issubset(df.columns):
            return "This dataset needs Product and Revenue_GBP columns."
        result = df.groupby("Product")["Revenue_GBP"].sum().sort_values(ascending=False)
        return f"Top product by revenue: {result.index[0]} (£{result.iloc[0]:,.2f}).\n\nRevenue by product:\n{result.to_string()}"

    if "revenue" in q and "region" in q:
        if not {"Region", "Revenue_GBP"}.issubset(df.columns):
            return "This dataset needs Region and Revenue_GBP columns."
        result = df.groupby("Region")["Revenue_GBP"].sum().sort_values(ascending=False)
        return f"Top region by revenue: {result.index[0]} (£{result.iloc[0]:,.2f}).\n\nRevenue by region:\n{result.to_string()}"

    if "channel" in q:
        if not {"Sales_Channel", "Revenue_GBP"}.issubset(df.columns):
            return "This dataset needs Sales_Channel and Revenue_GBP columns."
        result = df.groupby("Sales_Channel")["Revenue_GBP"].sum().sort_values(ascending=False)
        return f"Top sales channel: {result.index[0]} (£{result.iloc[0]:,.2f} revenue).\n\nRevenue by channel:\n{result.to_string()}"

    if "average order" in q:
        if "Revenue_GBP" not in df.columns:
            return "This dataset does not contain a revenue column."
        if "Order_ID" in df.columns:
            average = df.groupby("Order_ID")["Revenue_GBP"].sum().mean()
        else:
            average = df["Revenue_GBP"].mean()
        return f"Average revenue per order: £{average:,.2f}."

    if "revenue" in q or "sales" in q:
        if "Revenue_GBP" not in df.columns:
            return "This dataset does not contain a revenue column."
        return f"Total recorded revenue is £{df['Revenue_GBP'].sum():,.2f}."

    if "profit" in q:
        if "Profit_GBP" not in df.columns:
            return "This dataset does not contain a profit column."
        return f"Total recorded profit is £{df['Profit_GBP'].sum():,.2f}."

    return ("I cannot answer that question yet. Try asking about revenue, profit by product or region, "
            "sales channels, average order value, missing values or duplicates.")


def ai_answer_question(df, question):
    """Use an AI model to explain dataset summaries and answer a question."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
        except Exception:
            api_key = ""
    if not api_key:
        return (
            "OpenAI API key not found. Close this Streamlit session and launch the app "
            "from the PowerShell window where OPENAI_API_KEY is set."
        )

    try:
        client = OpenAI(api_key=api_key)
        columns = ", ".join(str(column) for column in df.columns)
        summary_parts = [f"Rows: {len(df)}", f"Columns: {columns}"]

        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            summary_parts.append("Numeric summary:\n" + numeric_df.describe().round(2).to_string())

        # Include exact group totals for common business fields when available.
        for group_column, value_column, label in [
            ("Product", "Revenue_GBP", "Revenue by product"),
            ("Region", "Revenue_GBP", "Revenue by region"),
            ("Region", "Profit_GBP", "Profit by region"),
            ("Product", "Profit_GBP", "Profit by product"),
            ("Sales_Channel", "Revenue_GBP", "Revenue by sales channel"),
        ]:
            if group_column in df.columns and value_column in df.columns:
                totals = df.groupby(group_column)[value_column].sum().sort_values(ascending=False)
                summary_parts.append(f"{label}:\n{totals.round(2).to_string()}")

        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are a careful data analyst. Answer using only the supplied dataset summaries. "
                "Do not invent figures or claim to have inspected individual records. Explain limitations. "
                "Label possible causes as hypotheses, not proven facts. Keep answers clear and practical."
            ),
            input=("Dataset information:\n\n" + "\n\n".join(summary_parts)
                   + f"\n\nUser question: {question}")
        )
        return response.output_text
    except Exception as error:
        return f"AI request failed: {error}"


st.set_page_config(page_title="AI Data Analysis Agent", page_icon="📊", layout="wide")
st.title("📊 AI Data Analysis Agent")
st.write("Upload a dataset to explore its structure, check data quality and view basic statistics.")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.success("Dataset loaded successfully!")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        col3.metric("Duplicate rows", int(df.duplicated().sum()))

        st.subheader("1. Dataset Preview")
        st.dataframe(df.head(10), use_container_width=True)

        st.subheader("Data Cleaning")
        st.write("Create a cleaned copy of the uploaded dataset. The original uploaded data remains unchanged.")
        if st.button("Clean Dataset"):
            cleaned_df, cleaning_summary = clean_data(df)
            st.session_state["cleaned_df"] = cleaned_df
            st.session_state["cleaning_summary"] = cleaning_summary

        if "cleaned_df" in st.session_state:
            cleaned_df = st.session_state["cleaned_df"]
            summary = st.session_state["cleaning_summary"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Original Rows", summary["original_rows"])
            col2.metric("Cleaned Rows", summary["cleaned_rows"])
            col3.metric("Duplicates Removed", summary["duplicates_removed"])
            st.write("Missing values before cleaning:", summary["missing_values_before"])
            st.write("Missing values after cleaning:", summary["missing_values_after"])
            st.subheader("Cleaned Dataset Preview")
            st.dataframe(cleaned_df.head(10), use_container_width=True)
            csv_data = cleaned_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Cleaned CSV", data=csv_data,
                               file_name="cleaned_dataset.csv", mime="text/csv")

        st.subheader("2. Data Quality")
        quality = pd.DataFrame({
            "Data Type": df.dtypes.astype(str),
            "Missing Values": df.isna().sum(),
            "Missing (%)": (df.isna().mean() * 100).round(2),
        })
        st.dataframe(quality, use_container_width=True)

        st.subheader("3. Statistical Summary")
        numeric_df = df.select_dtypes(include="number")
        if not numeric_df.empty:
            st.dataframe(numeric_df.describe().round(2), use_container_width=True)
        else:
            st.info("No numeric columns were found.")

        st.subheader("4. Explore a Column")
        selected_column = st.selectbox("Choose a column", df.columns.tolist())
        st.write("Value counts:")
        st.dataframe(
            df[selected_column].value_counts(dropna=False).head(20)
            .rename_axis("Value").reset_index(name="Count"),
            use_container_width=True,
        )

        st.subheader("Choose Data for Analysis")
        if "cleaned_df" in st.session_state:
            use_cleaned_data = st.checkbox("Use cleaned dataset for analysis", value=True)
            analysis_df = st.session_state["cleaned_df"] if use_cleaned_data else df
        else:
            analysis_df = df
            st.info("Click 'Clean Dataset' above to enable cleaned-data analysis.")

        st.subheader("5. Interactive Data Visualisation")
        if "Revenue_GBP" in analysis_df.columns and "Product" in analysis_df.columns:
            revenue_by_product = analysis_df.groupby("Product", as_index=False)["Revenue_GBP"].sum().sort_values("Revenue_GBP", ascending=False)
            fig = px.bar(revenue_by_product, x="Product", y="Revenue_GBP",
                         title="Total Revenue by Product",
                         labels={"Product": "Product", "Revenue_GBP": "Revenue (£)"}, text_auto=".2s")
            fig.update_yaxes(rangemode="tozero")
            st.plotly_chart(fig, use_container_width=True)

        if "Profit_GBP" in analysis_df.columns and "Region" in analysis_df.columns:
            profit_by_region = analysis_df.groupby("Region", as_index=False)["Profit_GBP"].sum().sort_values("Profit_GBP", ascending=False)
            fig = px.bar(profit_by_region, x="Region", y="Profit_GBP",
                         title="Total Profit by Region",
                         labels={"Region": "Region", "Profit_GBP": "Profit (£)"}, text_auto=".2s")
            fig.update_yaxes(rangemode="tozero")
            st.plotly_chart(fig, use_container_width=True)

        if "Order_Date" in analysis_df.columns and "Revenue_GBP" in analysis_df.columns:
            monthly = analysis_df.copy()
            monthly["Order_Date"] = pd.to_datetime(monthly["Order_Date"], errors="coerce")
            monthly = monthly.dropna(subset=["Order_Date"])
            monthly["Month"] = monthly["Order_Date"].dt.to_period("M").dt.to_timestamp()
            monthly = monthly.groupby("Month", as_index=False)["Revenue_GBP"].sum().sort_values("Month")
            fig = px.line(monthly, x="Month", y="Revenue_GBP", markers=True,
                          title="Monthly Revenue Trend",
                          labels={"Month": "Month", "Revenue_GBP": "Revenue (£)"})
            fig.update_yaxes(rangemode="tozero")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("6. Business Insights Summary")
        if "Revenue_GBP" in analysis_df.columns:
            st.metric("Total Revenue", f"£{analysis_df['Revenue_GBP'].sum():,.2f}")
        if "Profit_GBP" in analysis_df.columns:
            st.metric("Total Profit", f"£{analysis_df['Profit_GBP'].sum():,.2f}")
        if "Order_ID" in analysis_df.columns and "Revenue_GBP" in analysis_df.columns:
            average_order_value = analysis_df.groupby("Order_ID")["Revenue_GBP"].sum().mean()
            st.metric("Average Revenue per Order", f"£{average_order_value:,.2f}")
        if "Revenue_GBP" in analysis_df.columns and "Product" in analysis_df.columns:
            revenue_by_product = analysis_df.groupby("Product")["Revenue_GBP"].sum()
            top_product = revenue_by_product.idxmax()
            st.write(f"**Top product by revenue:** {top_product} (£{revenue_by_product.max():,.2f})")
        if "Profit_GBP" in analysis_df.columns and "Region" in analysis_df.columns:
            profit_by_region = analysis_df.groupby("Region")["Profit_GBP"].sum()
            top_region = profit_by_region.idxmax()
            st.write(f"**Most profitable region:** {top_region} (£{profit_by_region.max():,.2f})")

        st.subheader("7. Ask Your Data Analyst")
        st.write("Ask a question about your dataset. Choose the standard assistant or the AI-powered assistant.")
        assistant_mode = st.radio("Assistant mode", ["Standard (calculated answers)", "AI-powered answer"], horizontal=True)
        question = st.text_input("What would you like to know?", placeholder="Which product generates the most revenue?")
        if st.button("Analyse Question"):
            if assistant_mode == "AI-powered answer":
                with st.spinner("AI is analysing the dataset summary..."):
                    answer = ai_answer_question(analysis_df, question)
            else:
                answer = answer_question(analysis_df, question)
            st.markdown("### Analysis Result")
            st.write(answer)

    except Exception as error:
        st.error(f"Could not analyse this file: {error}")
else:
    st.info("Upload a CSV file to get started.")
