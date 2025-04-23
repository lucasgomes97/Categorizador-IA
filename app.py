# import streamlit as st
# import requests
# import os
# import openai
# from dotenv import load_dotenv
# import csv

# # === CONFIGURAÇÕES ===

# load_dotenv()

# openai.api_key = os.getenv("OPENAI_API_KEY")
# ZAMMAD_API_URL = os.getenv("ZAMMAD_API_URL")
# ZAMMAD_API_TOKEN = os.getenv("ZAMMAD_API_TOKEN")
# CATEGORIA_TXT = "categoria.txt"
# OPENAI_MODEL = "gpt-4"

# HEADERS_ZAMMAD = {
#     "Authorization": f"Token token={ZAMMAD_API_TOKEN}",
#     "Content-Type": "application/json"
# }

# # === FUNÇÕES ===

# def carregar_categorias(filepath):
#     categorias = {}
#     categoria_pai = None
#     with open(filepath, encoding="utf-8") as f:
#         for linha in f:
#             linha = linha.rstrip()
#             if not linha:
#                 continue
#             if not linha.startswith(" "):
#                 categoria_pai = linha.strip()
#                 categorias[categoria_pai] = []
#             else:
#                 categorias[categoria_pai].append(linha.strip())
#     return categorias

# def carregar_grupos(path_txt):
#     grupos = {}
#     with open(path_txt, "r", encoding="utf-8") as file:
#         for linha in file:
#             if linha.startswith("ID:"):
#                 partes = linha.strip().split(", Nome:")
#                 if len(partes) == 2:
#                     id_str = partes[0].replace("ID:", "").strip()
#                     nome = partes[1].strip()
#                     grupos[nome] = int(id_str)
#     return grupos


# def gerar_prompt(title, note, categorias_dict):
#     prompt = '''Você é um assistente de categorização de chamados de service desk. Classifique corretamente chamados conforme categorias/subcategorias fornecidas.
# 🔹 REGRAS IMPORTANTES:
# - Use apenas as categorias/subcategorias da lista abaixo.
# - Analise o contexto da descrição do chamado.
# - Se tiver dúvida entre opções semelhantes, escolha a mais específica possível.
# .\n\n'''
#     for pai, filhos in categorias_dict.items():
#         for filho in filhos:
#             prompt += f"- {pai} > {filho}\n"
#     prompt += f"\nTítulo: {title.strip()}\n"
#     if note:
#         prompt += f"Descrição: {note.strip()}\n"
#     prompt += "\nResponda apenas com o nome da subcategoria mais adequada (não inclua o nome da categoria pai)."
#     return prompt

# def classificar_com_openai(prompt):
#     response = openai.ChatCompletion.create(
#         model=OPENAI_MODEL,
#         messages=[
#             {"role": "system", "content": "Você é um assistente de categorização de chamados técnicos."},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0.2
#     )
#     return response['choices'][0]['message']['content'].strip()

# def classificar_grupo_com_openai(title, note, grupos_dict):
#     nomes_grupos = list(grupos_dict.keys())
#     opcoes_formatadas = "\n".join([f"- {g}" for g in nomes_grupos])

#     prompt = f"""
# Você é um assistente técnico responsável por classificar chamados. Com base no título e na descrição de um chamado, classifique-o de acordo com o grupo correto abaixo:

# Grupos disponíveis:
# {opcoes_formatadas}

# Título: {title}
# Descrição: {note}

# Retorne apenas o **NOME exato** de um dos grupos listados.
# Retorne apenas o nome do grupo, sem explicações adicionais.

# """.strip()

#     if not title.strip() and not note.strip():
#         return "Indefinido – título ou descrição ausente."

#     try:
#         response = openai.ChatCompletion.create(
#             model=OPENAI_MODEL,
#             messages=[
#                 {"role": "system", "content": "Você é um assistente técnico especialista em direcionar chamados para o grupo correto."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )
#         nome_grupo = response['choices'][0]['message']['content'].strip()
#         grupo_id = grupos_dict.get(nome_grupo, "Não encontrado")
#         return nome_grupo, grupo_id
#     except Exception as e:
#         return f"Erro ao classificar grupo: {str(e)}", None

# grupos_dict = carregar_grupos("Grupos.txt")


# def classificar_nivel_com_openai(title, note):
#     definicoes_nivel = """
# Você é um assistente técnico treinado para classificar chamados com base em níveis de suporte técnico,Sua tarefa é classificar chamados técnicos em um dos três níveis de complexidade, conforme as definições abaixo::

# - Nível 1 (N1): Chamados básicos, como reiniciar serviços, monitoramento simples, problemas simples de login, coleta de logs, uso básico de comandos Docker.
# - Nível 2 (N2): Chamados intermediários com análise de performance detalhada, ajustes de configuração, problemas de rede avançados, gerenciamento de certificados e logs.
# - Nível 3 (N3): Chamados críticos e complexos, como containers que não iniciam, falhas graves no Docker Daemon, perda de dados, desempenho gravemente degradado, falhas de volume e problemas em clusters Docker Swarm.

# Classifique o chamado abaixo como N1, N2 ou N3 apenas com base nas definições acima.

# Título: {title}
# Descrição: {note}

# Responda apenas com: N1, N2 ou N3.
# """.strip()

#     if not title.strip() and not note.strip():
#         return "Indefinido – título ou descrição ausente."

#     if not title.strip():
#         title = "Título ausente"

#     if not note.strip():
#         note = "Descrição ausente"

#     prompt = definicoes_nivel.format(title=title, note=note)

#     try:
#         response = openai.ChatCompletion.create(
#             model=OPENAI_MODEL,
#             messages=[
#                 {"role": "system", "content": "Você é um assistente técnico especializado em suporte a Docker."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )
#         return response['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         return f"Erro ao classificar nível: {str(e)}"


# def classificar_criticidade_com_openai(title, note):
#     definicoes_criticidade = """
# Você é um assistente técnico treinado para classificar chamados com base na criticidade do problema onde analisa o titulo do chamado e descrição e avalia o chamado apartir da definições abaixo:

# - Crítico (1): Problemas graves que afetam diretamente o funcionamento do serviço, como falhas críticas, perda de dados, ou falha no serviço principal.
# - Alto (2): Problemas significativos que afetam o desempenho, mas não paralisam completamente o serviço.
# - Normal (3): Problemas de médio impacto, como ajustes ou melhorias que não afetam diretamente o serviço.
# - Baixo (4): Problemas menores ou questões de manutenção, como ajustes de configuração, problemas não urgentes ou simples dúvidas.

# Classifique o chamado abaixo como Crítico (1), Alto (2), Normal (3) ou Baixo (4) apenas com base nas definições acima.

# Título: {title}
# Descrição: {note}

# Responda apenas com: 1 Crítico, 2 Alto, 3 Normal ou 4 Baixo.
# """.strip()

#     if not title.strip() and not note.strip():
#         return "Indefinido – título ou descrição ausente."

#     prompt = definicoes_criticidade.format(title=title, note=note)

#     try:
#         response = openai.ChatCompletion.create(
#             model=OPENAI_MODEL,
#             messages=[
#                 {"role": "system", "content": "Você é um assistente técnico especializado em suporte a chamados."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )
#         return response['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         return f"Erro ao classificar criticidade: {str(e)}"
    

# def classificar_prioridade_com_openai(title, note):
#     definicoes_prioridade = """
# Você é um assistente técnico treinado para classificar chamados com base na prioridade, onde analisa o titulo do chamado e descrição e avalia o chamado apartir da definições abaixo:

# - 1 (Baixo): Solicitações não urgentes, sem impacto imediato ou relacionadas a dúvidas e melhorias menores.
# - 2 (Normal): Chamados que requerem atenção no fluxo padrão, mas sem urgência.
# - 3 (Alto): Chamados que devem ser tratados o quanto antes, com impacto considerável, mas que não são críticos.

# Classifique o chamado abaixo como 1, 2 ou 3, de acordo com essas definições.

# Título: {title}
# Descrição: {note}

# Responda apenas com: 1 baixo, 2 normal ou 3 alto.
# """.strip()

#     if not title.strip() and not note.strip():
#         return "Indefinido – título ou descrição ausente."

#     prompt = definicoes_prioridade.format(title=title, note=note)

#     try:
#         response = openai.ChatCompletion.create(
#             model=OPENAI_MODEL,
#             messages=[
#                 {"role": "system", "content": "Você é um assistente técnico especializado em triagem de chamados."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )
#         return response['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         return f"Erro ao classificar prioridade: {str(e)}"


# # Função para extrair as tarefas do CSV
# def extrair_atividades_csv(caminho_csv):
#     atividades = []
#     with open(caminho_csv, encoding='cp1252') as arquivo:
#         leitor = csv.reader(arquivo, delimiter=';')
#         next(leitor)  # pula o cabeçalho
#         for linha in leitor:
#             if len(linha) >= 2:
#                 descricao = linha[0].strip()
#                 try:
#                     ust = float(linha[1].strip())
#                     atividades.append((descricao, ust))
#                 except ValueError:
#                     continue
#     return atividades


# # Função para encontrar atividades relacionadas com base na descrição
# def encontrar_atividades_relacionadas(descricao_chamado, atividades):
#     descricao_chamado = descricao_chamado.lower()
#     relacionadas = []
#     for desc, ust in atividades:
#         if any(palavra in desc.lower() for palavra in descricao_chamado.split()):
#             relacionadas.append((desc, ust))
#     return relacionadas

# csv_atividades = 'consultoria_docker.csv'
# atividades_ust = extrair_atividades_csv(csv_atividades)



# def classificar_tipo_chamado(title, note, atividades_ust):
#     prompt = f"""
# Você é um assistente técnico de Service Desk onde analisa chamados técnicos.

# Com base no título e na descrição do chamado, classifique somente como requisição ou incidente, use a definição abaixo para verificar qual melhor se adequa:

# - **Requisição**: quando se trata de solicitações que exigem execução/desemvolvimento de tarefas, mudanças ou serviços.
# - **Incidente**: quando se trata de erros, falhas ou interrupções.

# Se for classificado como Requisição, analise a descrição do chamado e com base nas atividades abaixo, estime a quantidade de UST (Unidades de Serviço Técnico) envolvidas.

# **Atividades e UST disponíveis:**
# {atividades_ust}


# Título: {title}
# Descrição: {note}

# Retorne neste formato:
# Tipo: Requisição ou Incidente
# UST estimado: número (se aplicável) ou "Não se aplica"
# """.strip()

#     try:
#         response = openai.ChatCompletion.create(
#             model=OPENAI_MODEL,
#             messages=[
#                 {"role": "system", "content": "Você é um assistente técnico especializado em classificação de chamados."},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )
#         return response['choices'][0]['message']['content'].strip()
#     except Exception as e:
#         return f"Erro ao classificar tipo: {str(e)}"


# def atualizar_categoria_chamado(ticket_id, categoria_pai, subcategoria):
#     payload = {
#         "categoria": [categoria_pai, subcategoria]
#     }
#     url = f"{ZAMMAD_API_URL}/api/v1/tickets/{ticket_id}"
#     resposta = requests.put(url, headers=HEADERS_ZAMMAD, json=payload)
#     return resposta.status_code == 200, resposta.text

# def encontrar_categoria_pai(categorias_dict, subcategoria):
#     for pai, filhos in categorias_dict.items():
#         if subcategoria.lower() in [f.lower() for f in filhos]:
#             return pai
#     return None

# def buscar_chamado_por_numero(numero):
#     url = f"{ZAMMAD_API_URL}/api/v1/tickets/search?query=number:{numero}"
#     resposta = requests.get(url, headers=HEADERS_ZAMMAD)
#     if resposta.status_code == 200:
#         resultados = resposta.json()
#         if 'tickets' in resultados and resultados['tickets']:
#             ticket_id = resultados['tickets'][0]
#             if 'assets' in resultados and str(ticket_id) in resultados['assets']['Ticket']:
#                 return resultados['assets']['Ticket'][str(ticket_id)]
#     return None

# def obter_primeira_descricao(ticket_id):
#     url = f"{ZAMMAD_API_URL}/api/v1/ticket_articles/by_ticket/{ticket_id}"
#     resposta = requests.get(url, headers=HEADERS_ZAMMAD)
#     if resposta.status_code == 200:
#         artigos = resposta.json()
#         if artigos:
#             return artigos[0].get("body", "")
#     return ""

# # === INTERFACE STREAMLIT ===

# st.set_page_config(page_title="Categorizador de Chamados", page_icon="🧠")
# st.title("🧠 Categorizador de Chamados I.A")

# categorias = carregar_categorias(CATEGORIA_TXT)

# if "classificacao_realizada" not in st.session_state:
#     st.session_state.classificacao_realizada = False

# with st.form("formulario_chamado"):
#     numero_chamado = st.text_input("Número do chamado:")
#     submitted = st.form_submit_button("Classificar Chamado")

#     if submitted:
#         if not numero_chamado.strip():
#             st.warning("Por favor, informe um número de chamado.")
#             st.stop()

#         chamado = buscar_chamado_por_numero(numero_chamado.strip())
#         if not chamado:
#             st.error(f"❌ Chamado {numero_chamado} não encontrado.")
#             st.stop()
            

#         ticket_id = chamado["id"]
#         title = chamado.get("title", "Sem título")
#         note = obter_primeira_descricao(ticket_id)

#         criticidade = chamado.get("criticidade", "Não definida")
#         tipo_chamado = chamado.get("tipo", "Não definido")
#         grupo = chamado.get("group_id", "Não definido")
#         prioridade = chamado.get("priority_id", "Não definida")

#         st.subheader("📄 Detalhes do Chamado:")
#         st.markdown(f"**Título:** {title}")
#         st.markdown(f"**Descrição:** {note or 'Sem descrição'}")
#         st.markdown(f"**Criticidade:** {criticidade}")
#         st.markdown(f"**Tipo:** {tipo_chamado}")
#         st.markdown(f"**Grupo (ID):** {grupo}")
#         st.markdown(f"**Prioridade (ID):** {prioridade}")
#         prioridade_sugerida = classificar_prioridade_com_openai(title, note)
        

#         prompt = gerar_prompt(title, note, categorias)

#         try:
#             subcategoria = classificar_com_openai(prompt)
#             categoria_pai = encontrar_categoria_pai(categorias, subcategoria)

#             if not categoria_pai:
#                 st.error(f"❌ Subcategoria '{subcategoria}' não encontrada.")
#                 st.stop()

#             nivel_sugerido = classificar_nivel_com_openai(title, note)
#             criticidade_sugerida = classificar_criticidade_com_openai(title, note)

#             st.subheader("📊 Classificações Sugeridas:")
#             st.markdown(f"**Categoria Pai:** {categoria_pai}")
#             st.markdown(f"**Subcategoria:** {subcategoria}")
#             st.markdown(f"**Nível de Suporte:** {nivel_sugerido}")
#             st.markdown(f"**Criticidade:** {criticidade_sugerida}")
#             st.markdown(f"**Prioridade Sugerida:** {prioridade_sugerida}")
#             nome_grupo, grupo_id = classificar_grupo_com_openai(title, note, grupos_dict)
#             st.markdown(f"**Grupo Sugerido:** {nome_grupo} (ID: {grupo_id})")
#             atividades_ust = extrair_atividades_csv(csv_atividades)
#             resultado = classificar_tipo_chamado(title, note, atividades_ust)
#             st.markdown("**Resultado da Classificação de Tipo:**")
#             st.text(resultado)
#             csv_atividades = 'consultoria_docker.csv'
#             atividades_ust = extrair_atividades_csv(csv_atividades)
#             st.text_area("Detalhes das tarefas desenvolvidas e valores UST", value=atividades_ust or "⚠️ Nenhum dado extraído", height=300)
#             if tipo_chamado == "Requisição":
#                 # Verificar custos da requisição
#                 custos = extrair_atividades_csv("consultoria_docker.csv")
#                 st.markdown("**Custos para a Requisição**:")
#                 for tarefa, custo in custos:
#                     st.write(f"Tarefa: {tarefa} | Custo: {custo}")

#             st.success("✅ Classificação concluída!")

#         except Exception as e:
#             st.error(f"❌ Erro durante classificação: {e}")


import streamlit as st
import requests
import os
import openai
from dotenv import load_dotenv
import csv

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
    prompt = '''Você é um assistente de categorização de chamados de service desk. Classifique corretamente chamados conforme categorias/subcategorias fornecidas.
🔹 REGRAS IMPORTANTES:
- Use apenas as categorias/subcategorias da lista abaixo.
- Analise o contexto da descrição do chamado.
- Se tiver dúvida entre opções semelhantes, escolha a mais específica possível.
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

def classificar_grupo_com_openai(title, note, grupos_dict):
    nomes_grupos = list(grupos_dict.keys())
    opcoes_formatadas = "\n".join([f"- {g}" for g in nomes_grupos])

    prompt = f"""
Você é um assistente técnico responsável por classificar chamados. Com base no título e na descrição de um chamado, classifique-o de acordo com o grupo correto abaixo:

Grupos disponíveis:
{opcoes_formatadas}

Título: {title}
Descrição: {note}

Retorne apenas o **NOME exato** de um dos grupos listados.
Retorne apenas o nome do grupo, sem explicações adicionais.

""".strip()

    if not title.strip() and not note.strip():
        return "Indefinido – título ou descrição ausente."

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especialista em direcionar chamados para o grupo correto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        nome_grupo = response['choices'][0]['message']['content'].strip()
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
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em suporte a Docker."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
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
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em suporte a chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
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
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em triagem de chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Erro ao classificar prioridade: {str(e)}"


# Função para extrair as tarefas do CSV
def extrair_atividades_csv(caminho_csv):
    atividades = []
    with open(caminho_csv, encoding='cp1252') as arquivo:
        leitor = csv.reader(arquivo, delimiter=';')
        next(leitor)  # pula o cabeçalho
        for linha in leitor:
            if len(linha) >= 2:
                descricao = linha[0].strip()
                try:
                    ust = float(linha[1].strip())
                    atividades.append((descricao, ust))
                except ValueError:
                    continue
    return atividades


def encontrar_melhor_atividade(descricao_chamado, atividades):
    if not descricao_chamado:
        return None

    prompt = f"""
Você é um assistente técnico. A seguir estão descrições de tarefas com suas respectivas estimativas de esforço (UST). Com base no chamado descrito abaixo, escolha a tarefa que mais se adequa. Retorne exatamente o texto da tarefa conforme aparece na lista e o valor UST desta tarefa.

Chamado:
{descricao_chamado}

Tarefas disponíveis:
""" + "\n".join([f"- {desc} (UST: {ust})" for desc, ust in atividades]) + """

Retorne exatamente a descrição da tarefa mais adequada e seu valor em UST, sem alterar o texto.
"""

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente que escolhe tarefas com base em descrições de chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        descricao_escolhida = response['choices'][0]['message']['content'].strip()

        # Localiza a UST original correspondente à descrição retornada
        for desc, ust in atividades:
            if desc.strip().lower() == descricao_escolhida.strip().lower():
                return desc, ust

        return descricao_escolhida, None  # UST não encontrada

    except Exception as e:
        return f"Erro ao encontrar atividade: {str(e)}", None


csv_atividades = 'consultoria_docker.csv'
atividades_ust = extrair_atividades_csv(csv_atividades)


def classificar_tipo_chamado(title, note, atividades_ust):
    # Encontra a melhor atividade e o valor de UST correspondente
    melhor_atividade, ust_valor = encontrar_melhor_atividade(f"{title} {note}", atividades_ust)
    
    # Se o valor de UST estiver presente, extraímos o valor numérico de UST do texto
    if ust_valor:
        # Extraímos o valor numérico de UST diretamente da string de "melhor_atividade"
        ust_estimado = ust_valor.split("UST:")[1].strip().split()[0] if "UST:" in ust_valor else "Não se aplica"
    else:
        ust_estimado = "Não se aplica"

    # Monta o prompt com o UST estimado
    prompt = f"""
Você é um assistente técnico de Service Desk onde analisa chamados técnicos.

Com base no título e na descrição do chamado, classifique somente como requisição ou incidente, use a definição abaixo para verificar qual melhor se adequa:

- **Requisição**: quando se trata de solicitações que exigem execução/desemvolvimento de tarefas, mudanças ou serviços.
- **Incidente**: quando se trata de erros, falhas ou interrupções.

Se for classificado como Requisição, analise a descrição do chamado e com base nas atividades abaixo, estime a quantidade de UST (Unidades de Serviço Técnico) envolvidas.

**Atividades e UST disponíveis:**
{atividades_ust}


Título: {title}
Descrição: {note}

Retorne neste formato:
Tipo: Requisição ou Incidente
UST estimado: {ust_estimado} Atenção o ust deve ser o mesmo do que está no arquivo, não mude.
""".strip()

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Você é um assistente técnico especializado em classificação de chamados."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Erro ao classificar tipo: {str(e)}"


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
        if not chamado:
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
            subcategoria = classificar_com_openai(prompt)
            categoria_pai = encontrar_categoria_pai(categorias, subcategoria)

            if not categoria_pai:
                st.error(f"❌ Subcategoria '{subcategoria}' não encontrada.")
                st.stop()

            nivel_sugerido = classificar_nivel_com_openai(title, note)
            criticidade_sugerida = classificar_criticidade_com_openai(title, note)

            st.subheader("📊 Classificações Sugeridas:")
            st.markdown(f"**Categoria Pai:** {categoria_pai}")
            st.markdown(f"**Subcategoria:** {subcategoria}")
            st.markdown(f"**Nível de Suporte:** {nivel_sugerido}")
            st.markdown(f"**Criticidade:** {criticidade_sugerida}")
            st.markdown(f"**Prioridade Sugerida:** {prioridade_sugerida}")
            nome_grupo, grupo_id = classificar_grupo_com_openai(title, note, grupos_dict)
            st.markdown(f"**Grupo Sugerido:** {nome_grupo} (ID: {grupo_id})")
            atividades_ust = extrair_atividades_csv(csv_atividades)
            resultado = classificar_tipo_chamado(title, note, atividades_ust)
            st.markdown("**Resultado da Classificação de Tipo:**")
            st.text(resultado)
            csv_atividades = 'consultoria_docker.csv'
            atividades_ust = extrair_atividades_csv(csv_atividades)
            melhor_atividade = encontrar_melhor_atividade(f"{title} {note}", atividades_ust)
            st.text_area("Detalhes das tarefas desenvolvidas e valores UST:", melhor_atividade, height=150)
            if tipo_chamado == "Requisição":
                # Verificar custos da requisição
                custos = extrair_atividades_csv("consultoria_docker.csv")
                st.markdown("**Custos para a Requisição**:")
                for tarefa, custo in custos:
                    st.write(f"Tarefa: {tarefa} | Custo: {custo}")
                    

            st.success("✅ Classificação concluída!")

        except Exception as e:
            st.error(f"❌ Erro durante classificação: {e}")
