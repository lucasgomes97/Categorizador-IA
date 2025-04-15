import streamlit as st
import requests
import os
import openai
import time
from dotenv import load_dotenv

# === CONFIGURAÇÕES ===

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
ZAMMAD_API_URL = os.getenv("ZAMMAD_API_URL")
ZAMMAD_API_TOKEN = os.getenv("ZAMMAD_API_TOKEN")
CATEGORIA_TXT = "categoria.txt"
OPENAI_MODEL = "gpt-4"

HEADERS_ZAMMAD = {
    "Authorization": f"Token token={ZAMMAD_API_TOKEN}",
    "Content-Type": "application/json"
}

# === FUNÇÕES ===

def carregar_categorias(filepath):
    categorias = {}
    categoria_pai = None
    with open(filepath, encoding="utf-8") as f:
        for linha in f:
            linha = linha.rstrip()
            if not linha:
                continue
            if not linha.startswith(" "):
                categoria_pai = linha.strip()
                categorias[categoria_pai] = []
            else:
                categorias[categoria_pai].append(linha.strip())
    return categorias

def gerar_prompt(title, note, categorias_dict):
    prompt = '''Você é um assistente de categorização de chamados de service desk. Classifique corretamente chamados conforme categorias/subcategorias fornecidas.
🔹 REGRAS IMPORTANTES:
- Use apenas as categorias/subcategorias da lista abaixo.
- Analise o contexto da descrição do chamado.
.\n\n'''
    for pai, filhos in categorias_dict.items():
        for filho in filhos:
            prompt += f"- {pai} > {filho}\n"
    prompt += f"\nTítulo: {title.strip()}\n"
    if note:
        prompt += f"Descrição: {note.strip()}\n"
    prompt += "\nResponda apenas com o nome da subcategoria mais adequada (não inclua o nome da categoria pai)."
    return prompt

def classificar_com_openai(prompt):
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Você é um assistente de categorização de chamados técnicos."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response['choices'][0]['message']['content'].strip()

def atualizar_categoria_chamado(ticket_id, categoria_pai, subcategoria):
    payload = {
        "categoria": [categoria_pai, subcategoria]
    }
    url = f"{ZAMMAD_API_URL}/api/v1/tickets/{ticket_id}"
    resposta = requests.put(url, headers=HEADERS_ZAMMAD, json=payload)
    return resposta.status_code == 200, resposta.text

def encontrar_categoria_pai(categorias_dict, subcategoria):
    for pai, filhos in categorias_dict.items():
        if subcategoria.lower() in [f.lower() for f in filhos]:
            return pai
    return None

def buscar_chamado_por_numero(numero):
    url = f"{ZAMMAD_API_URL}/api/v1/tickets/search?query=number:{numero}"
    resposta = requests.get(url, headers=HEADERS_ZAMMAD)
    if resposta.status_code == 200:
        resultados = resposta.json()
        if 'tickets' in resultados and resultados['tickets']:
            ticket_id = resultados['tickets'][0]
            if 'assets' in resultados and str(ticket_id) in resultados['assets']['Ticket']:
                return resultados['assets']['Ticket'][str(ticket_id)]
    return None

def obter_primeira_descricao(ticket_id):
    url = f"{ZAMMAD_API_URL}/api/v1/ticket_articles/by_ticket/{ticket_id}"
    resposta = requests.get(url, headers=HEADERS_ZAMMAD)
    if resposta.status_code == 200:
        artigos = resposta.json()
        if artigos:
            return artigos[0].get("body", "")
    return ""

# === INTERFACE STREAMLIT ===

st.set_page_config(page_title="Categorizador de Chamados", page_icon="🧠")
st.title("🧠 Categorizador de Chamados I.A")

categorias = carregar_categorias(CATEGORIA_TXT)

with st.form("formulario_chamado"):
    numero_chamado = st.text_input("Número do chamado:")
    submitted = st.form_submit_button("Classificar Chamado")

    if submitted:
        if not numero_chamado.strip():
            st.warning("Por favor, informe um número de chamado.")
            st.stop()

        chamado = buscar_chamado_por_numero(numero_chamado.strip())
        if not chamado:
            st.error(f"❌ Chamado {numero_chamado} não encontrado.")
            st.stop()

        ticket_id = chamado["id"]
        title = chamado.get("title", "")
        note = obter_primeira_descricao(ticket_id)

        prompt = gerar_prompt(title, note, categorias)
        try:
            subcategoria = classificar_com_openai(prompt)
        except Exception as e:
            st.error(f"❌ Erro ao classificar o chamado: {e}")
            st.stop()

        categoria_pai = encontrar_categoria_pai(categorias, subcategoria)
        if categoria_pai:
            sucesso, resposta = atualizar_categoria_chamado(ticket_id, categoria_pai, subcategoria)
            if sucesso:
                st.success(f"✅ Chamado {numero_chamado} categorizado como: {categoria_pai} > {subcategoria}")
            else:
                st.error(f"❌ Erro ao atualizar o chamado: {resposta}")
        else:
            st.error(f"❌ Subcategoria '{subcategoria}' não encontrada nas categorias definidas.")

        # Aguarda e limpa toda a interface
        time.sleep(1.5)
        st.rerun()

