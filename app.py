import streamlit as st
import requests
import os
from dotenv import load_dotenv
import csv
from openai import OpenAI
import json
import PyPDF2
import textwrap

# === CONFIGURAÇÕES ===

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
ZAMMAD_API_URL = os.getenv("ZAMMAD_API_URL")
ZAMMAD_API_TOKEN = os.getenv("ZAMMAD_API_TOKEN")
CATEGORIA_TXT = "categorias.json"
OPENAI_MODEL = "gpt-4.1"

HEADERS_ZAMMAD = {
    "Authorization": f"Token token={ZAMMAD_API_TOKEN}",
    "Content-Type": "application/json"
}

# === FUNÇÕES ===

def carregar_categorias(filepath):
    with open(filepath, encoding="utf-8") as f:
        categorias = json.load(f)
    return categorias


def carregar_grupos(path_txt):
    grupos = {}
    with open(path_txt, "r", encoding="utf-8") as file:
        for linha in file:
            if linha.startswith("ID:"):
                partes = linha.strip().split(", Nome:")
                if len(partes) == 2:
                    id_str = partes[0].replace("ID:", "").strip()
                    nome = partes[1].strip()
                    grupos[nome] = int(id_str)
    return grupos


def gerar_prompt(title, note, categorias_dict):
    prompt = """Você é um assistente especializado na **categorização de chamados de Service Desk**. Sua tarefa é analisar o título e a descrição do chamado e classificá-lo corretamente com **uma categoria e subcategoria** entre as opções fornecidas.

📌 **REGRAS IMPORTANTES**:
- Use **exclusivamente** as categorias e subcategorias listadas abaixo.
- Algumas podem estar escritas de forma diferente no chamado. Use o **contexto e o significado** para encontrar a correspondência correta.
- Se houver mais de uma possibilidade, escolha a opção **mais precisa e relevante**.
- **Não invente** novas categorias ou subcategorias.
- A saída deve ser apenas no formato: `Categoria > Subcategoria`

🔽 **Categorias e Subcategorias Disponíveis**:
"""
    for categoria, subcategorias in categorias_dict.items():
        for sub in subcategorias:
            prompt += f"- {categoria} > {sub}\n"

    prompt += "\n"
    prompt += f"📝 **Título do chamado**: {title.strip()}\n"
    if note:
        prompt += f"🧾 **Descrição detalhada**: {note.strip()}\n"
    prompt += "\n✅ **Classificação final esperada**: Apenas o nome da categoria e subcategoria, no formato `Categoria > Subcategoria`"
    
    return prompt


def classificar_com_openai(prompt):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente de categorização de chamados técnicos."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        resposta = response.choices[0].message.content.strip()
        
        if ">" not in resposta or len(resposta.split(">")) != 2:
            return None, None  # retorno seguro para tratar depois

        categoria, subcategoria = [parte.strip() for parte in resposta.split(">")]

        if not categoria or not subcategoria:
            return None, None

        return categoria, subcategoria
    
    except Exception as e:
        print(f"Erro ao classificar categoria: {str(e)}")
        return None, None


def classificar_grupo_com_openai(title, note, grupos_dict):
    nomes_grupos = list(grupos_dict.keys())
    opcoes_formatadas = "\n".join([f"- {g}" for g in nomes_grupos])

    prompt = f"""
        Você é um assistente técnico responsável por classificar chamados. Com base no título e na descrição de um chamado, classifique-o de acordo com o grupo correto abaixo,selecione apenas 1 grupo:

        Grupos disponíveis:
        {opcoes_formatadas}

        Título: {title}
        Descrição: {note}

        Retorne apenas o **NOME exato** de um dos grupos listados.
        Retorne apenas 1 grupo, sem explicações adicionais.

        """.strip()

    if not title.strip() and not note.strip():
        return "Indefinido – título ou descrição ausente."

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especialista em direcionar chamados para o grupo correto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        nome_grupo = response.choices[0].message.content.strip()
        grupo_id = grupos_dict.get(nome_grupo, "Não encontrado")
        return nome_grupo, grupo_id
    except Exception as e:
        return f"Erro ao classificar grupo: {str(e)}", None

grupos_dict = carregar_grupos("Grupos.txt")


def classificar_nivel_com_openai(title, note):
    definicoes_nivel = """
Você é um assistente técnico treinado para classificar chamados com base em níveis de suporte técnico,Sua tarefa é classificar chamados técnicos em um dos três níveis de complexidade, conforme as definições abaixo::

- Nível 1 (N1): Chamados básicos, como reiniciar serviços, monitoramento simples, problemas simples de login, coleta de logs, uso básico de comandos Docker.
- Nível 2 (N2): Chamados intermediários com análise de performance detalhada, ajustes de configuração, problemas de rede avançados, gerenciamento de certificados e logs.
- Nível 3 (N3): Chamados críticos e complexos, como containers que não iniciam, falhas graves no Docker Daemon, perda de dados, desempenho gravemente degradado, falhas de volume e problemas em clusters Docker Swarm.

Classifique o chamado abaixo como N1, N2 ou N3 apenas com base nas definições acima.

Título: {title}
Descrição: {note}

Responda apenas com: N1, N2 ou N3.
""".strip()

    if not title.strip() and not note.strip():
        return "Indefinido – título ou descrição ausente."

    if not title.strip():
        title = "Título ausente"

    if not note.strip():
        note = "Descrição ausente"

    prompt = definicoes_nivel.format(title=title, note=note)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em suporte a Docker."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao classificar nível: {str(e)}"


def classificar_criticidade_com_openai(title, note):
    definicoes_criticidade = """
Você é um assistente técnico treinado para classificar chamados com base na criticidade do problema onde analisa o titulo do chamado e descrição e avalia o chamado apartir da definições abaixo:

- Crítico (1): Problemas graves que afetam diretamente o funcionamento do serviço, como falhas críticas, perda de dados, ou falha no serviço principal.
- Alto (2): Problemas significativos que afetam o desempenho, mas não paralisam completamente o serviço.
- Normal (3): Problemas de médio impacto, como ajustes ou melhorias que não afetam diretamente o serviço.
- Baixo (4): Problemas menores ou questões de manutenção, como ajustes de configuração, problemas não urgentes ou simples dúvidas.

Classifique o chamado abaixo como Crítico (1), Alto (2), Normal (3) ou Baixo (4) apenas com base nas definições acima.

Título: {title}
Descrição: {note}

Responda apenas com: 1 Crítico, 2 Alto, 3 Normal ou 4 Baixo.
""".strip()

    if not title.strip() and not note.strip():
        return "Indefinido – título ou descrição ausente."

    prompt = definicoes_criticidade.format(title=title, note=note)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em suporte a chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao classificar criticidade: {str(e)}"
    

def classificar_prioridade_com_openai(title, note):
    definicoes_prioridade = """
Você é um assistente técnico treinado para classificar chamados com base na prioridade, onde analisa o titulo do chamado e descrição e avalia o chamado apartir da definições abaixo:

- 1 (Baixo): Solicitações não urgentes, sem impacto imediato ou relacionadas a dúvidas e melhorias menores.
- 2 (Normal): Chamados que requerem atenção no fluxo padrão, mas sem urgência.
- 3 (Alto): Chamados que devem ser tratados o quanto antes, com impacto considerável, mas que não são críticos.

Classifique o chamado abaixo como 1, 2 ou 3, de acordo com essas definições.

Título: {title}
Descrição: {note}

Responda apenas com: 1 baixo, 2 normal ou 3 alto.
""".strip()

    if not title.strip() and not note.strip():
        return "Indefinido – título ou descrição ausente."

    prompt = definicoes_prioridade.format(title=title, note=note)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em triagem de chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erro ao classificar prioridade: {str(e)}"


def extrair_atividades_csv(caminho_csv):
    atividades = []
    nome_catalogo = None
    with open(caminho_csv, encoding='cp1252') as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=';')
        for linha in leitor:
            descricao = linha.get("descricao") or linha.get("Descrição") or linha.get("descrição") or linha.get("atividade")
            ust = linha.get("ust") or linha.get("UST")
            fonte = linha.get("fonte") or linha.get("Fonte") or "Fonte não especificada"

            if descricao and ust:
                try:
                    atividades.append((descricao.strip(), float(ust.strip()), fonte.strip()))
                except ValueError:
                    continue
            if not nome_catalogo and fonte:
                nome_catalogo = fonte.strip()
    return nome_catalogo, atividades


def extrair_nome_catalogo_pdf(caminho_pdf):
    try:
        with open(caminho_pdf, "rb") as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            primeira_pagina = leitor.pages[0]
            texto = primeira_pagina.extract_text()
            for linha in texto.split("\n"):
                if "Catálogo" in linha:
                    return linha.strip()
        return "Catálogo Desconhecido"
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return "Catálogo Desconhecido"


def encontrar_melhor_atividade(titulo_chamado, descricao_chamado, atividades):
    if not descricao_chamado:
        return None, None, None

    prompt = f"""
        Você é um assistente técnico treinado para identificar tarefas específicas em um catálogo fechado. O catálogo de fontes, tarefas e UST está listado logo abaixo e é a **única fonte confiável**.
        ---
        📌 **REGRAS OBRIGATÓRIAS**:
        - Você **NÃO PODE inventar, adaptar ou sugerir tarefas ou fontes** fora da lista abaixo.
        - A tarefa, UST e fonte devem vir **exatamente do catálogo listado**.
        - Se encontrar uma correspondência perfeita, retorne neste formato:

        Tarefa: [descrição exata da tarefa]
        UST: [valor]
        Fonte: [fonte exata]

        - Se **não encontrar nenhuma correspondente**, procure a **mais parecida** e retorne assim:

        ❌ Nenhuma tarefa referente encontrada nos catálogos. A mais próxima e recomendada é:
        Tarefa: [descrição mais semelhante da lista]
        UST: [valor]
        Fonte: [fonte da linha correspondente com o assunto do chamado]

        ⚠️ Caso invente qualquer texto fora da lista final, será considerado erro crítico inadimicivel.

        ---

        📦 Catálogo fechado de tarefas disponíveis:
        """ + "\n".join([f"- {desc} (UST: {ust}, Fonte: {fonte})" for desc, ust, fonte in atividades]) + f"""

        ---
        📝 Chamado a ser analisado:
        Título: {titulo_chamado}
        Descrição: {descricao_chamado}

        🔚 Agora retorne apenas conforme os formatos exigidos acima, sem explicações extras.
        """

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você seleciona e analisa tarefas, fontes e UST do catálogo sem inventar."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )

        resposta = response.choices[0].message.content.strip()

        # Processa a resposta
        if resposta.startswith('Tarefa:'):
            # Resposta de correspondência perfeita
            linhas = resposta.split('\n')
            tarefa = linhas[0].replace('Tarefa:', '').strip()
            ust = linhas[1].replace('UST:', '').strip()
            fonte = linhas[2].replace('Fonte:', '').strip()
            return tarefa, ust, fonte

        elif resposta.startswith('❌'):
            # Resposta de sugestão (não encontrou perfeita)
            linhas = resposta.split('\n')
            tarefa = linhas[1].replace('Tarefa:', '').strip()
            ust = linhas[2].replace('UST:', '').strip()
            fonte = linhas[3].replace('Fonte:', '').strip()
            return tarefa, ust, fonte

        else:
            return "Resposta fora do formato esperado.", None, None

    except Exception as e:
        return f"Erro ao encontrar atividade: {str(e)}", None, None

csv_atividades = 'consultoria_docker.csv'
atividades_ust = extrair_atividades_csv(csv_atividades)


def classificar_tipo_chamado(title, note, atividades_ust):
    melhor_atividade, ust_valor, fonte_catalogo = encontrar_melhor_atividade(title, note, atividades_ust)

    prompt = f"""
        Você é um assistente técnico de Service Desk onde analisa chamados técnicos.

        Com base no título e na descrição do chamado, classifique somente como requisição ou incidente, use a definição abaixo:

        - **Requisição**: quando se trata de solicitações que exigem execução/desenvolvimento de tarefas, mudanças ou serviços.
        - **Incidente**: quando se trata de erros, falhas ou interrupções.

        Título: {title}
        Descrição: {note}

        Retorne neste formato:
        Tipo: Requisição ou Incidente
    """.strip()

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em classificação de chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return response.choices[0].message.content.strip(), melhor_atividade, ust_valor, fonte_catalogo
    except Exception as e:
        return f"Erro ao classificar tipo: {str(e)}", melhor_atividade, ust_valor, fonte_catalogo



def atualizar_categoria_chamado(ticket_id, categoria_pai, subcategoria):
    payload = {
        "categoria": [categoria_pai, subcategoria]
    }
    url = f"{ZAMMAD_API_URL}/api/v1/tickets/{ticket_id}"
    resposta = requests.put(url, headers=HEADERS_ZAMMAD, json=payload)
    return resposta.status_code == 200, resposta.text


def encontrar_categoria_pai(categorias, subcategoria_alvo):
    subcategoria_alvo = subcategoria_alvo.strip().lower()
    for categoria_pai, subcategorias in categorias.items():
        for sub in subcategorias:
            if sub.strip().lower() == subcategoria_alvo:
                return categoria_pai
    return None
    
  
def buscar_chamado_por_numero(numero):
    url = f"{ZAMMAD_API_URL}/api/v1/tickets/search?query=number:{numero}"
    resposta = requests.get(url, headers=HEADERS_ZAMMAD)

    if resposta.status_code == 200:
        resultados = resposta.json()

        if isinstance(resultados, list) and len(resultados) > 0:
            return resultados[0]  # Retorna diretamente o primeiro ticket encontrado

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

if "classificacao_realizada" not in st.session_state:
    st.session_state.classificacao_realizada = False

with st.form("formulario_chamado"):
    numero_chamado = st.text_input("Número do chamado:")
    submitted = st.form_submit_button("Classificar Chamado")

    if submitted:
        if not numero_chamado.strip():
            st.warning("Por favor, informe um número de chamado.")
            st.stop()

        chamado = buscar_chamado_por_numero(numero_chamado.strip())
        # st.write("🔍 Chamado encontrado:", chamado)
        if chamado is None:
            st.error(f"❌ Chamado {numero_chamado} não encontrado.")
            st.stop()
            

        ticket_id = chamado["id"]
        title = chamado.get("title", "Sem título")
        note = obter_primeira_descricao(ticket_id)

        criticidade = chamado.get("criticidade", "Não definida")
        tipo_chamado = chamado.get("tipo", "Não definido")
        grupo = chamado.get("group_id", "Não definido")
        prioridade = chamado.get("priority_id", "Não definida")

        st.subheader("📄 Detalhes do Chamado:")
        st.markdown(f"**Título:** {title}")
        st.markdown(f"**Descrição:** {note or 'Sem descrição'}")
        st.markdown(f"**Criticidade:** {criticidade}")
        st.markdown(f"**Tipo:** {tipo_chamado}")
        st.markdown(f"**Grupo (ID):** {grupo}")
        st.markdown(f"**Prioridade (ID):** {prioridade}")
        prioridade_sugerida = classificar_prioridade_com_openai(title, note)
        

        prompt = gerar_prompt(title, note, categorias)

        try:
            categoria, subcategoria = classificar_com_openai(prompt)

            if not categoria or not subcategoria:
                st.error("❌ Resposta inválida da OpenAI.")
                st.stop()

            categoria_pai = encontrar_categoria_pai(categorias, subcategoria)

            if not categoria_pai:
                st.error(f"❌ Subcategoria '{subcategoria}' não encontrada nas categorias fornecidas.")
                st.stop()

            # Exibir sucesso (opcional)
            st.success(f"✅ Classificado como: {categoria} > {subcategoria}")

            nivel_sugerido = classificar_nivel_com_openai(title, note)
            criticidade_sugerida = classificar_criticidade_com_openai(title, note)

            st.subheader("📊 Classificação Sugerida:")
            st.markdown(f"**Categoria Pai:** {categoria_pai}")
            st.markdown(f"**Subcategoria:** {subcategoria}")
            st.markdown(f"**Nível de Suporte:** {nivel_sugerido}")
            st.markdown(f"**Criticidade:** {criticidade_sugerida}")
            st.markdown(f"**Prioridade Sugerida:** {prioridade_sugerida}")
            nome_grupo, grupo_id = classificar_grupo_com_openai(title, note, grupos_dict)
            st.markdown(f"**Grupo Sugerido** {nome_grupo} (ID: {grupo_id})")
            nome_catalogo, atividades_ust = extrair_atividades_csv(csv_atividades)
            resultado, melhor_atividade, ust_valor, fonte_catalogo = classificar_tipo_chamado(title, note, atividades_ust)
            st.markdown("**Resultado da Classificação de Tipo:**")
            st.text(resultado)

            # Determina o tipo
            tipo_classificado = "Incidente" if "Tipo: Incidente" in resultado else "Requisição"

            # Prepara o texto de exibição da melhor atividade com UST
            if tipo_classificado == "Incidente":
                texto_exibicao = "Este chamado é um Incidente e, portanto, não possui UST estimado."
                ust_extraida = None
            else:
                if melhor_atividade:
                    if melhor_atividade.lower().startswith("atividade não encontrada"):
                        # Mensagem retornada pela IA quando não encontra exatamente
                        texto_exibicao = melhor_atividade
                        ust_extraida = None
                    else:
                        texto_exibicao = melhor_atividade
                        ust_extraida = ust_valor
                else:
                    texto_exibicao = "Nenhuma atividade correspondente encontrada."
                    ust_extraida = None

            # Mostra a estimativa real da UST, se for requisição
            if tipo_classificado == "Requisição":
                st.subheader("💰 Análise da Tarefa do Catálogo:")
                st.markdown(f"- **Fonte:** {nome_catalogo}")  

                st.markdown(f"- **Resultado da busca no catálogo:**\n{textwrap.fill(texto_exibicao, width=80)}")
                if ust_extraida:
                    st.markdown(f"- **UST estimado:** {ust_extraida}")
                
            else:
                st.info("ℹ️ Este chamado é um **Incidente** e, portanto, não possui UST estimado.")

            if tipo_classificado == "Requisição" and ust_extraida:
                st.success(f"✅ Classificação concluída!\nTipo: {tipo_classificado}\nUST estimado: {ust_extraida}")
            elif tipo_classificado == "Requisição":
                st.success(f"✅ Classificação concluída!\nTipo: {tipo_classificado}\nUST estimado: Não encontrada")
            else:
                st.success(f"✅ Classificação concluída!\nTipo: {tipo_classificado}")

        except Exception as e:
            st.error(f"❌ Erro durante classificação: {e}")
