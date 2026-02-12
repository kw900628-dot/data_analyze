import streamlit as st
import pandas as pd
import plotly.express as px
from ydata_profiling import ProfileReport
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="데이터 만능 분석기", layout="wide")

# ---------------------------------------------------------
# [수정된 함수] ExcelFile 객체 대신 '데이터(Dict)'를 반환하도록 변경
# ---------------------------------------------------------
@st.cache_data
def load_data(file):
    try:
        # [CASE A] 엑셀 파일일 경우
        if file.name.endswith('.xlsx') or file.name.endswith('.xls'):
            # sheet_name=None 옵션은 모든 시트를 {'시트명': DF} 형태의 딕셔너리로 읽어옵니다.
            # 이 딕셔너리는 Streamlit 캐시에 저장 가능합니다!
            return pd.read_excel(file, sheet_name=None)
        
        # [CASE B] CSV 파일일 경우
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
    # 데이터 로드 (이제 캐시 에러가 나지 않습니다)
    loaded_data = load_data(uploaded_file)

    if loaded_data is not None:
        df = None
        
        # [로직 변경] 로드된 데이터가 '딕셔너리(엑셀)'인지 '데이터프레임(CSV)'인지 확인
        
        # 1. 엑셀 (딕셔너리 형태)인 경우
        if isinstance(loaded_data, dict):
            sheet_names = list(loaded_data.keys())
            
            if len(sheet_names) > 1:
                st.info(f"💡 이 파일에는 {len(sheet_names)}개의 시트가 있습니다.")
                selected_sheet = st.selectbox("분석할 시트를 선택하세요:", sheet_names)
                df = loaded_data[selected_sheet] # 선택한 시트의 데이터프레임 꺼내기
            else:
                # 시트가 1개면 바로 첫 번째 시트 사용
                df = list(loaded_data.values())[0]
        
        # 2. CSV (데이터프레임 형태)인 경우
        else:
            df = loaded_data

        # ---------------------------------------------------------
        # 여기서부터는 기존 분석 코드와 동일
        # ---------------------------------------------------------
        if df is not None:
            st.success("파일 업로드 성공!")
            
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