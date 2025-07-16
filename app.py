import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="벤포드의 법칙 분석기", layout="centered")
st.title("🔢 벤포드의 법칙 검증기 (Benford's Law)")

# 벤포드 분포
benford_dist = np.log10(1 + 1 / np.arange(1, 10))

def extract_leading_digits(series):
    digits = series.astype(str).str.replace("-", "").str.replace(".", "").str.lstrip("0").str.extract(r'(\d)').dropna()
    return digits.astype(int)

def check_benford(series):
    digits = extract_leading_digits(series)
    counts = digits[0].value_counts(normalize=True).sort_index()
    return counts

def plot_distribution(observed, title=""):
    fig, ax = plt.subplots()
    ax.bar(range(1, 10), benford_dist, alpha=0.5, label="Benford")
    ax.bar(observed.index, observed.values, alpha=0.7, label="Observed")
    ax.set_xticks(range(1, 10))
    ax.set_xlabel("Leading Digit")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend()
    st.pyplot(fig)

def adjust_to_benford(data):
    data = np.array(data)
    original_mean = np.mean(data)
    benford_counts = (benford_dist * len(data)).astype(int)

    new_data = []
    for digit, count in zip(range(1, 10), benford_counts):
        while count > 0:
            number = digit * 10 ** np.random.uniform(0, 3)
            new_data.append(number)
            count -= 1

    while len(new_data) < len(data):
        digit = np.random.choice(range(1, 10), p=benford_dist)
        number = digit * 10 ** np.random.uniform(0, 3)
        new_data.append(number)

    new_data = np.array(new_data[:len(data)])
    adjusted_data = new_data * (original_mean / new_data.mean())
    return adjusted_data

# 📂 파일 업로드 (.csv, .xlsx, .xls)
uploaded = st.file_uploader("📂 CSV 또는 엑셀 파일 업로드", type=["csv", "xlsx", "xls"])
if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
        st.stop()

    st.write("데이터 미리보기:")
    st.dataframe(df.head())

    numeric_columns = df.select_dtypes(include='number').columns
    if len(numeric_columns) == 0:
        st.warning("분석할 수 있는 숫자 열이 없습니다.")
        st.stop()

    column = st.selectbox("분석할 숫자 열 선택", numeric_columns)
    values = df[column].dropna()
    obs_dist = check_benford(values)

    st.subheader("📊 분포 비교")
    plot_distribution(obs_dist, f"'{column}' 열의 분포")

    difference = np.abs(obs_dist.reindex(range(1, 10), fill_value=0) - benford_dist)
    if (difference > 0.05).any():
        st.error("❌ 벤포드의 법칙을 따르지 않습니다.")
        if st.button("벤포드 분포에 맞춰 데이터 조정"):
            adjusted = adjust_to_benford(values)
            df.loc[values.index, f"{column}_benford"] = adjusted
            st.success("✅ 조정 완료. 평균은 동일하고 벤포드 분포에 맞게 조정됨.")
            st.dataframe(df[[column, f"{column}_benford"]].head())

            # 저장 & 다운로드 버튼
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 수정된 CSV 다운로드", data=csv, file_name="benford_adjusted.csv", mime="text/csv")
    else:
        st.success("✅ 벤포드의 법칙을 잘 따르고 있습니다.")
