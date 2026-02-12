import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components
import openpyxl

# 페이지 설정
st.set_page_config(page_title="데이터 만능 분석기", layout="wide")

# ---------------------------------------------------------
# [중요] 함수 정의는 무조건 실행 코드보다 위에 있어야 합니다!
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        # [CASE A] 엑셀 파일일 경우: 시트 선택 기능 추가를 위해 객체 반환
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            return pd.ExcelFile(file)
        
        # [CASE B] CSV 파일일 경우: 인코딩 자동 처리 후 데이터프레임 반환
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
# 메인 화면 구성 (UI)
# ---------------------------------------------------------
st.title("📊 누구나 쓸 수 있는 데이터 자동 분석기")
st.markdown("CSV나 Excel 파일을 업로드하면, 자동으로 컬럼을 분석하여 시각화합니다.")

uploaded_file = st.file_uploader("데이터 파일을 업로드해주세요 (csv, xlsx)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 함수 호출 (이제 위에서 정의했으므로 에러 안 남)
    loaded_object = load_data(uploaded_file)

    if loaded_object is not None:
        df = None
        
        # 엑셀 파일인 경우 시트 선택 로직
        if isinstance(loaded_object, pd.ExcelFile):
            sheet_names = loaded_object.sheet_names
            if len(sheet_names) > 1:
                st.info(f"💡 이 파일에는 {len(sheet_names)}개의 시트가 있습니다.")
                selected_sheet = st.selectbox("분석할 시트를 선택하세요:", sheet_names)
                df = loaded_object.parse(selected_sheet)
            else:
                df = loaded_object.parse(sheet_names[0])
        
        # CSV 파일인 경우 (이미 데이터프레임임)
        else:
            df = loaded_object

        # 데이터가 준비되었으면 분석 시작
        if df is not None:
            st.success("파일 업로드 성공!")
            
            # 탭 구성
            tab1, tab2, tab3 = st.tabs(["📄 데이터 미리보기", "🎨 내 마음대로 시각화", "🤖 AI 종합 리포트"])

            with tab1:
                st.write(f"총 {df.shape[0]}행, {df.shape[1]}열의 데이터입니다.")
                st.dataframe(df.head())

            with tab2:
                st.subheader("원하는 컬럼을 선택해 그래프 그리기")
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                
                if numeric_cols:
                    col1, col2 = st.columns(2)
                    with col1:
                        x_col = st.selectbox("X축 선택", numeric_cols)
                    with col2:
                        y_col = st.selectbox("Y축 선택", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                    
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"{x_col} vs {y_col}")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("수치형 데이터가 없어 산점도를 그릴 수 없습니다.")

            with tab3:
                st.write("데이터의 기초 통계, 결측치, 상관관계 등을 한 번에 분석합니다.")
                if st.button("종합 분석 리포트 생성하기"):
                    with st.spinner("리포트를 생성 중입니다..."):
                        pr = ProfileReport(df, minimal=True)
                        report_html = pr.to_html()
                        components.html(report_html, height=800, scrolling=True)
    else:
        st.error("파일을 읽을 수 없습니다. 형식을 확인해주세요.")