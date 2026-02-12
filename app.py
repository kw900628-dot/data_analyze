import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np

# 페이지 설정
st.set_page_config(page_title="데이터 만능 분석기", layout="wide")

# ---------------------------------------------------------
# [필수] 한글 폰트 설정 (GitHub에 NanumGothic.ttf 올려야 함)
# ---------------------------------------------------------
def set_korean_font():
    font_path = "NanumGothic.ttf" 
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        font_name = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_name)
        plt.rc('axes', unicode_minus=False)
    else:
        # 폰트 파일이 없을 경우를 대비한 경고 (로컬 실행 시 무시 가능)
        pass 

set_korean_font()

# ---------------------------------------------------------
# [함수] 데이터 로드 (캐싱 & 엑셀/CSV 처리)
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            return pd.read_excel(file, sheet_name=None)
        elif file.name.endswith('.csv'):
            try:
                return pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                file.seek(0)
                return pd.read_csv(file, encoding='cp949')
        else:
            return None
    except Exception as e:
        return None

# ---------------------------------------------------------
# [함수] 데이터 핵심 인사이트 생성
# ---------------------------------------------------------
def generate_insights(df):
    insights = []
    numeric_df = df.select_dtypes(include=['number'])
    
    if not numeric_df.empty:
        # (1) 강한 상관관계 찾기
        if len(numeric_df.columns) >= 2:
            corr_matrix = numeric_df.corr().abs()
            mask = np.ones(corr_matrix.shape, dtype=bool)
            np.fill_diagonal(mask, 0)
            max_corr = corr_matrix[mask].max().max()
            
            if max_corr > 0.7:
                row, col = np.where(corr_matrix == max_corr)
                # 중복 제거를 위해 첫 번째 쌍만 가져오기
                var1 = corr_matrix.columns[row[0]]
                var2 = corr_matrix.columns[col[0]]
                insights.append(f"🔗 **'{var1}'**와(과) **'{var2}'** 변수는 서로 매우 강력한 관계({max_corr:.2f})가 있습니다.")

        # (2) 변동성 분석
        try:
            std_val = numeric_df.std()
            max_std_col = std_val.idxmax()
            insights.append(f"📊 **'{max_std_col}'** 데이터가 가장 들쭉날쭉합니다 (변동성이 큼).")
        except:
            pass

        # (3) 최대/최소 요약
        try:
            first_col = numeric_df.columns[0]
            max_val = numeric_df[first_col].max()
            min_val = numeric_df[first_col].min()
            insights.append(f"📈 **'{first_col}'**의 최대값은 **{max_val}**, 최소값은 **{min_val}** 입니다.")
        except:
            pass

    return insights

# ---------------------------------------------------------
# 메인 화면 UI
# ---------------------------------------------------------
st.title("📊 누구나 쓸 수 있는 데이터 자동 분석기")
st.markdown("CSV나 Excel 파일을 업로드하면, 자동으로 컬럼을 분석하여 시각화합니다.")

uploaded_file = st.file_uploader("데이터 파일을 업로드해주세요 (csv, xlsx)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    loaded_data = load_data(uploaded_file)

    if loaded_data is not None:
        df = None
        
        # 1. 엑셀 처리
        if isinstance(loaded_data, dict):
            sheet_names = list(loaded_data.keys())
            if len(sheet_names) > 1:
                st.info(f"💡 이 파일에는 {len(sheet_names)}개의 시트가 있습니다.")
                selected_sheet = st.selectbox("분석할 시트를 선택하세요:", sheet_names)
                df = loaded_data[selected_sheet]
            else:
                df = list(loaded_data.values())[0]
        # 2. CSV 처리
        else:
            df = loaded_data

        # ---------------------------------------------------------
        # 분석 탭 시작
        # ---------------------------------------------------------
        if df is not None:
            st.success("✅ 파일 업로드 성공!")
            
            tab1, tab2, tab3 = st.tabs(["📄 데이터 미리보기", "🎨 시각화 & 인사이트", "🤖 AI 종합 리포트"])

            # [Tab 1] 미리보기
            with tab1:
                st.write(f"총 {df.shape[0]}행, {df.shape[1]}열의 데이터입니다.")
                st.dataframe(df.head())

            # [Tab 2] 시각화 및 인사이트
            with tab2:
                st.subheader("💡 AI 스마트 인사이트")
                insight_list = generate_insights(df)
                if insight_list:
                    for msg in insight_list:
                        st.info(msg)
                else:
                    st.write("수치형 데이터가 부족하여 인사이트를 도출할 수 없습니다.")

                st.divider()

                st.subheader("📊 데이터 시각화")
                all_cols = df.columns.tolist()
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    chart_type = st.radio(
                        "그래프 유형 선택:",
                        ["산점도 (Scatter Plot)", "선 그래프 (Line Chart)", "막대 그래프 (Bar Chart)"],
                        horizontal=True
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X축 선택 (모든 데이터)", all_cols)
                    with col2:
                        y_col = st.selectbox("Y축 선택 (숫자 데이터)", numeric_cols)
                    
                    if chart_type == "산점도 (Scatter Plot)":
                        fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                    elif chart_type == "선 그래프 (Line Chart)":
                        sort_opt = st.checkbox("X축 기준 정렬하기", value=True)
                        plot_df = df.sort_values(by=x_col) if sort_opt else df
                        fig = px.line(plot_df, x=x_col, y=y_col, title=f"{x_col}에 따른 {y_col} 변화")
                    elif chart_type == "막대 그래프 (Bar Chart)":
                        fig = px.bar(df, x=x_col, y=y_col, title=f"{x_col}별 {y_col}")

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("수치형 데이터가 없어 그래프를 그릴 수 없습니다.")

            # [Tab 3] AI 리포트
            with tab3:
                st.write("### 🤖 AI 종합 분석 리포트")
                st.info("데이터의 모든 통계적 특성을 분석합니다.")
                
                with st.expander("💡 리포트 보는 법"):
                    st.markdown("""
                    * **Overview:** 데이터의 전체 크기와 결측치 현황
                    * **Variables:** 각 항목별 상세 통계
                    * **Correlations:** 항목 간의 상관관계 히트맵
                    """)

                if st.button("종합 분석 리포트 생성하기"):
                    with st.spinner("리포트를 생성 중입니다..."):
                        # 한글 폰트 적용을 위해 설정 확인
                        try:
                            # 리포트 생성
                            pr = ProfileReport(df, minimal=True, title="데이터 분석 보고서")
                            report_html = pr.to_html()
                            components.html(report_html, height=800, scrolling=True)
                        except Exception as e:
                            st.error(f"리포트 생성 중 오류 발생: {e}")

    else:
        st.error("파일 형식을 확인해주세요.")