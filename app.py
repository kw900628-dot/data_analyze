import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="데이터 만능 분석기", layout="wide")

# ---------------------------------------------------------
# [데이터 로드 함수] 캐싱 적용 & 엑셀/CSV 완벽 지원
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        # [CASE A] 엑셀 파일일 경우: 모든 시트를 딕셔너리로 읽기
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            return pd.read_excel(file, sheet_name=None)
        
        # [CASE B] CSV 파일일 경우: 인코딩 자동 처리
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
# 메인 화면 구성
# ---------------------------------------------------------
st.title("📊 누구나 쓸 수 있는 데이터 자동 분석기")
st.markdown("CSV나 Excel 파일을 업로드하면, 자동으로 컬럼을 분석하여 시각화합니다.")

uploaded_file = st.file_uploader("데이터 파일을 업로드해주세요 (csv, xlsx)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 데이터 로드
    loaded_data = load_data(uploaded_file)

    if loaded_data is not None:
        df = None
        
        # 1. 엑셀 (딕셔너리 형태) 처리
        if isinstance(loaded_data, dict):
            sheet_names = list(loaded_data.keys())
            if len(sheet_names) > 1:
                st.info(f"💡 이 파일에는 {len(sheet_names)}개의 시트가 있습니다.")
                selected_sheet = st.selectbox("분석할 시트를 선택하세요:", sheet_names)
                df = loaded_data[selected_sheet]
            else:
                df = list(loaded_data.values())[0]
        
        # 2. CSV (데이터프레임 형태) 처리
        else:
            df = loaded_data

        # ---------------------------------------------------------
        # 데이터 분석 탭 구성 (여기서부터 들여쓰기 주의!)
        # ---------------------------------------------------------
        if df is not None:
            st.success("✅ 파일 업로드 및 데이터 로드 성공!")
            
            # 탭 3개 생성
            tab1, tab2, tab3 = st.tabs(["📄 데이터 미리보기", "🎨 내 마음대로 시각화", "🤖 AI 종합 리포트"])

            # [Tab 1] 데이터 미리보기
            with tab1:
                st.write(f"총 {df.shape[0]}행, {df.shape[1]}열의 데이터입니다.")
                st.dataframe(df.head())

            # [Tab 2] 시각화 (X축 문자열 허용, 다양한 차트)
            with tab2:
                st.subheader("📊 데이터 시각화")
                
                all_cols = df.columns.tolist()  # 전체 컬럼 (X축용)
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist() # 숫자 컬럼 (Y축용)
                
                if numeric_cols:
                    # 1. 그래프 유형 선택
                    chart_type = st.radio(
                        "그래프 유형을 선택하세요:",
                        ["산점도 (Scatter Plot)", "선 그래프 (Line Chart)", "막대 그래프 (Bar Chart)"],
                        horizontal=True
                    )

                    # 2. X, Y축 선택
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X축 선택 (모든 데이터 가능)", all_cols)
                    with col2:
                        y_col = st.selectbox("Y축 선택 (숫자 데이터만)", numeric_cols)
                    
                    # 3. 그래프 그리기
                    if chart_type == "산점도 (Scatter Plot)":
                        fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                    
                    elif chart_type == "선 그래프 (Line Chart)":
                        sort_opt = st.checkbox("X축 기준 정렬하기 (시간순/순서대로 볼 때 추천)", value=True)
                        plot_df = df.sort_values(by=x_col) if sort_opt else df
                        fig = px.line(plot_df, x=x_col, y=y_col, title=f"{x_col}에 따른 {y_col} 변화")

                    elif chart_type == "막대 그래프 (Bar Chart)":
                        fig = px.bar(df, x=x_col, y=y_col, title=f"{x_col}별 {y_col}")

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("데이터에 수치형 컬럼이 없어서 그래프를 그릴 수 없습니다.")

            # [Tab 3] AI 리포트 (이제 Tab 2 밖으로 나왔습니다!)
            with tab3:
                st.write("### 🤖 AI 종합 분석 리포트")
                st.info("데이터의 통계적 특성, 결측치, 상관관계 등을 한 번에 분석합니다.")
                
                # 리포트 보는 법 가이드 (한국어 설명 추가)
                with st.expander("💡 리포트 보는 법 (용어 설명)"):
                    st.markdown("""
                    * **Overview (개요):** 데이터의 전체적인 크기, 변수 유형, 결측치 비율 등을 보여줍니다.
                    * **Variables (변수):** 각 컬럼별 상세 통계(평균, 최대/최소, 분포)를 보여줍니다.
                    * **Distinct (고유값):** 서로 다른 값이 몇 개나 있는지 보여줍니다.
                    * **Missing (결측치):** 데이터가 비어있는 부분이 어디인지 시각화합니다.
                    * **Correlations (상관관계):** 변수들끼리 얼마나 밀접한 관계가 있는지 보여줍니다.
                    """)
                    
                if st.button("종합 분석 리포트 생성하기"):
                    with st.spinner("리포트를 생성 중입니다... 잠시만 기다려주세요."):
                        pr = ProfileReport(df, minimal=True, title="데이터 분석 보고서")
                        report_html = pr.to_html()
                        components.html(report_html, height=800, scrolling=True)

    else:
        st.error("파일 형식을 확인해주세요.")