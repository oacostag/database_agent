from google.adk.agents.llm_agent import Agent
import sqlite3

DB_NAME = "./agente_basedatos/sakila.db"


def execute_sql(query: str) -> dict:
    try:
        cursor = sqlite3.connect(DB_NAME).cursor()
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return {"result": str(results), "status": "success", "query": query}
    except Exception as e:
        return {"error": str(e), "status": "error", "query": query}

def get_schema_info() -> str:
    """Helper para inyectar el esquema en el prompt del agente."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schema = "\n".join([t[0] for t in cursor.fetchall()])
    conn.close()
    return schema

sql_worker = Agent(
    name="SQL_Specialist",
    model='gemini-2.5-flash,
    description="Agente experto en SQL para SQLite. Traduce lenguaje natural a SQL y ejecuta consultas.",
    instruction=f"""
    Eres un experto en SQL. Tu objetivo es obtener datos de la base de datos para responder a la solicitud.
    
    ESQUEMA DE LA BASE DE DATOS:
    {get_schema_info()}
    
    PASOS A SEGUIR:
    1. Analiza la solicitud y genera la consulta SQL adecuada (usa LIMIT si esperas muchos datos).
    2. Ejecuta la consulta con 'execute_sql'.
    3. Si obtienes resultados exitosos, TERMINA y devuelve los datos como respuesta final.
    4. NO ejecutes la misma consulta múltiples veces si ya obtuviste resultados.
    """,
    tools=[execute_sql]
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Consulta información de una base de datos y responde preguntas al usuario.",
    instruction="""Eres el asistente principal de una empresa.
    
    TU FLUJO DE TRABAJO:
    1. Si el usuario te saluda o hace preguntas generales (clima, chistes), responde tú mismo.
    2. Si el usuario pregunta por DATOS de la empresa (ventas, precios, stock), DEBES delegar la tarea al agente 'SQL_Specialist'.
    3. Una vez que el especialista te regrese los datos, formaliza la respuesta para el usuario final.""",
    sub_agents=[sql_worker],
)