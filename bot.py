import os
import re
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8620726561:AAEFBg0eTduLwxIpRr3Ab40k-5rE8dS9OGk"
NOTION_TOKEN = "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"
NOTION_DATABASE_ID = "335d0da7c01680a39a38cabd5848e4cc"

DIAS = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
}

def texto_a_numero(texto):
    numeros = {
        "cero": 0, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4,
        "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciseis": 16, "diecisiete": 17, "dieciocho": 18,
        "diecinueve": 19, "veinte": 20
    }
    texto = texto.lower().strip()
    if texto in numeros:
        return numeros[texto]
    try:
        return int(texto)
    except:
        return None

def parsear_mensaje(texto):
    texto_lower = texto.lower()
    hora = None
    match_hora_palabra = re.search(
        r'(cero|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|trece|catorce|quince|dieciseis|diecisiete|dieciocho|diecinueve|veinte)\s*(horas?|hs)',
        texto_lower
    )
    match_hora_numero = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(horas?|hs)', texto_lower)
    if match_hora_palabra:
        hora_num = texto_a_numero(match_hora_palabra.group(1))
        if hora_num is not None:
            hora = f"{hora_num:02d}:00"
    elif match_hora_numero:
        h = int(match_hora_numero.group(1))
        m = match_hora_numero.group(2) or "00"
        hora = f"{h:02d}:{m}"
    fecha = None
    hoy = datetime.now()
    for dia_nombre, dia_num in DIAS.items():
        if dia_nombre in texto_lower:
            dias_hasta = (dia_num - hoy.weekday()) % 7
            if dias_hasta == 0:
                dias_hasta = 7
            fecha_obj = hoy + timedelta(days=dias_hasta)
            fecha = fecha_obj.strftime("%Y-%m-%d")
            break
    fecha_completa = None
    if fecha and hora:
        fecha_completa = f"{fecha}T{hora}:00"
    elif fecha:
        fecha_completa = fecha
    materia = ""
    match_materia = re.search(r'tarea\s+(.+?)(?:\s+(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|\d))', texto_lower)
    if match_materia:
        materia = match_materia.group(1).strip().title()
    return {"nombre": texto.strip(), "materia": materia, "fecha": fecha_completa}

def crear_en_notion(nombre, materia, fecha):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    properties = {
        "Name": {"title": [{"text": {"content": nombre}}]}
    }
    if materia:
        properties["Materia"] = {"rich_text": [{"text": {"content": materia}}]}
    if fecha:
        properties["Fecha"] = {"date": {"start": fecha}}
    data = {"parent": {"database_id": NOTION_DATABASE_ID}, "properties": properties}
    response = requests.post(url, headers=headers, json=data)
    return response.status_code == 200

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    resultado = parsear_mensaje(texto)
    exito = crear_en_notion(resultado["nombre"], resultado["materia"], resultado["fecha"])
    if exito:
        respuesta = "✅ Agregado a Notion!\n\n"
        respuesta += f"Tarea: {resultado['nombre']}\n"
        if resultado["materia"]:
            respuesta += f"Materia: {resultado['materia']}\n"
        if resultado["fecha"]:
            respuesta += f"Fecha: {resultado['fecha']}\n"
    else:
        respuesta = "❌ Error al guardar en Notion. Intenta de nuevo."
    await update.message.reply_text(respuesta)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    print("Bot iniciado...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
