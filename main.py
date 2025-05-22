import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv


load_dotenv()
blobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USERNAME = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

#Formulário de Cadastro de Produtos
st.title("Cadastro de Produtos")
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])

#Save image to blob storage
def upload_image_to_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    container_client = blob_service_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

def insert_product(name, product_price, description, product_image):
    try:
        image_url = upload_image_to_blob(product_image)
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USERNAME, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Produtos (nome, descricao, preco, imagem_url) " \
        "VALUES (%s, %s, %s, %s)", (name, description, product_price, image_url))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False
    
def get_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USERNAME, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Produtos")
        products = cursor.fetchall()
        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao carregar produtos: {e}")
        return []    

def display_products():
    products = get_products()
    if products:
        cards_por_linha = 3
        cols = st.columns(cards_por_linha)
        for i, product in enumerate(products):
            col = cols[i % cards_por_linha]
            with col:
                st.write(f"**Nome:** {product[1]}")
                st.write(f"**Descrição:** {product[2]}")
                st.write(f"**Preço:** R$ {product[3]:.2f}")
                if product[4]:
                    html_img = f'<img src="{product[4]}" width="200" height="200" alt="Imagem do Produto">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")
            if (i + 1) % cards_por_linha == 0 and (i + 1) < len(products):
                cols = st.columns(cards_por_linha)
    else:
        st.warning("Nenhum produto encontrado.")

if st.button("Salvar Produto"):
    if product_name and product_price and product_description and product_image:
        if insert_product(product_name, product_price, product_description, product_image):
            st.success("Produto salvo com sucesso!")
        else:
            st.error("Erro ao salvar produto.")
    else:
        st.warning("Por favor, preencha todos os campos.")
    return_message = "Produto salvo com sucesso!"

st.header("Produtos Cadastrados")


if st.button("Carregar Produtos"):
    display_products()
    st.success("Produtos carregados com sucesso!")