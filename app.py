import os
import io
import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from PyPDF2 import PdfReader
import fitz  # this is pymupdf

st.set_page_config(
    page_title="Mühendisler İçin ATS",
    page_icon=":dog:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


@st.cache_resource
def gemini_get_response(prompt):

    #Modelin Ayarları
    model_1_ayarları = {
        "temperature": 0.5,
        "top_p": 0.9,
        "top_k": 40,
    }

    güvenlik_ayarları = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE",
        },
    ]


    model = genai.GenerativeModel(
        model_name = "gemini-1.5-flash-latest",
        safety_settings = güvenlik_ayarları,
        generation_config = model_1_ayarları,
    )


    response = model.generate_content(prompt).text

    return response




@st.cache_resource
def read_pdf_as_text(file):
    all_page_text = ""

    pdfReader = PdfReader(file)
    count = len(pdfReader.pages)

    for i in range(count):
        page = pdfReader.pages[i]
        all_page_text += page.extract_text()

    return all_page_text



@st.cache_resource
def read_pdf_as_images(file):
    images = []

    doc = fitz.open(file)

    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images


st.sidebar.title("Mühendisler İçin ATS Sistemine Hoşgeldiniz")

dosya_türü = st.sidebar.radio("Döküman Uzantınızı Seçin!", ["PDF Dosyası", "PDF Olmayan Dosya"])

st.subheader("Lütfen Alınacak Eleman İçin Aranan Koşulları Aşağıda Doldurunuz!")

col1, col2, col3 = st.columns(3)

with col1:
    departman = st.selectbox("Departman Seçiniz", ["Yazılım",
                                                   "Elektrik",
                                                   "Endüstri",
                                                   "Makine",
                                                   "Muhasebe",
                                                   "Reklamcılık",
                                                   "Kimya"])


with col2:
    deneyim_süresi = st.slider("Adayın Toplam Deneyim Süresi", 0, 20, 0, 1)


with col3:
    cinsiyet = st.selectbox("Cinsiyet Seçiniz", ["Erkek", "Kadın"])



if dosya_türü == "PDF Dosyası":
    yüklenen_dosya = st.sidebar.file_uploader("Lütfen PDF Dosyanızı Yükleyin!", type=["pdf"])

    if yüklenen_dosya:

        st.toast("PDF Dosyanız Yüklendi!", icon="🔥")

        on = st.sidebar.toggle("PDF'in Text Hali")

        if on:
            pdf_text = read_pdf_as_text(yüklenen_dosya)
            st.sidebar.write(pdf_text)

            prompt = pdf_text + f"""You are an experienced Human Resources Specialist. Staff will be recruited for {departman}. 
                    I want you to review the resume sample in the image and comment

                    You should pay attention to some points when commenting:
                        - Check whether the uploaded text is a resume, if the uploaded text is not a resume, give a warning message saying "Please upload a resume sample".
                        - Since the needs of each department are different, evaluate the compatibility between the specified department and the uploaded resume.
                        - Minimum required experince is must be 5 years. The users'experince time is {deneyim_süresi} year. If it is less then {deneyim_süresi} years, give info about it.
                        - Give me the percentage of  match if the resume matches the job description.
                        - After percentage, highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
                        - Final response should be in Markdown format, style is up to you, i count on you.
                        - Output must be in Turkish, other languages are not acceptable.
                        """

            if st.button("Yapay Zekaya Sor"):
                response = gemini_get_response(prompt)
                st.markdown(response)

        else:

            with open("temp.pdf", "wb") as file:
                file.write(yüklenen_dosya.getbuffer())

            images = read_pdf_as_images("temp.pdf")
            st.sidebar.image(images[0], caption="PDF'in İlk Sayfası")

            prompt = images[0], f"""You are an experienced Human Resources Specialist. Staff will be recruited for {departman}. 
                                I want you to review the resume sample in the image and comment

                                You should pay attention to some points when commenting:
                                    - Check whether the uploaded text is a resume, if the image is not a resume, give a warning message saying "Please upload a resume sample".
                                    - Since the needs of each department are different, evaluate the compatibility between the specified department and the uploaded resume.
                                    - Minimum required experince is must be 5 years. The users'experince time is {deneyim_süresi} year. If it is less then {deneyim_süresi} years, give info about it.
                                    - Give me the percentage of  match if the resume matches the {departman}. While doing that, you should use these parameters:
                                        > 
                                        >
                                        >
                                    - After percentage, highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
                                    - Final response should be in Markdown format, style is up to you, i count on you.
                                    - Output must be in Turkish, other languages are not acceptable.
                                    """

            if st.button("Yapay Zekaya Sor"):

                status_placeholder = st.empty()
                status_placeholder.info("Yapay Zeka Modeli Çalışıyor...")


                response = gemini_get_response(prompt)
                st.markdown(response)

                status_placeholder.success("Yapay Zeka Modeli Çalışması Tamamlandı!")
                st.download_button("Sonuçları İndir", response, "sonuçlar.txt", "txt")



else:
    yüklenen_dosya_2 = st.sidebar.file_uploader("Lütfen Görüntü Dosyanızı Yükleyin!", type=["jpg", "jpeg", "png"])

    if yüklenen_dosya_2:
        st.sidebar.image(yüklenen_dosya_2, caption="Yüklenen Görüntü")

        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": yüklenen_dosya_2.getvalue(),
            },
        ]

        prompt = image_parts[0], f"""You are an experienced Human Resources Specialist. Staff will be recruited for {departman}. 
                                        I want you to review the resume sample in the image and comment

                                        You should pay attention to some points when commenting:
                                            - Check whether the uploaded text is a resume, if the image is not a resume, give a warning message saying "Please upload a resume sample".
                                            - Since the needs of each department are different, evaluate the compatibility between the specified department and the uploaded resume.
                                            - Minimum required experince is must be 5 years. The users'experince time is {deneyim_süresi} year. If it is less then {deneyim_süresi} years, give info about it.
                                            - Give me the percentage of  match if the resume matches the {departman}. While doing that, you should use these parameters:
                                                > 
                                                >
                                                >
                                            - After percentage, highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
                                            - Final response should be in Markdown format, style is up to you, i count on you.
                                            - Output must be in Turkish, other languages are not acceptable.
                                            """

        if st.button("Yapay Zekaya Sor"):
            status_placeholder = st.empty()
            status_placeholder.info("Yapay Zeka Modeli Çalışıyor...")

            response = gemini_get_response(prompt)
            st.markdown(response)

            status_placeholder.success("Yapay Zeka Modeli Çalışması Tamamlandı!")
            st.download_button("Sonuçları İndir", response, "sonuçlar.txt", "txt")































