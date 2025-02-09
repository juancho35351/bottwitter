import tweepy
import time
import random
import json
import threading
import openai
import logging
import requests
import discord
from discord.ext import commands
from datetime import datetime
import re

# Configuración de credenciales (sustituir con tus claves API)
API_KEY = "TU_API_KEY"
API_SECRET = "TU_API_SECRET"
ACCESS_TOKEN = "TU_ACCESS_TOKEN"
ACCESS_TOKEN_SECRET = "TU_ACCESS_TOKEN_SECRET"
OPENAI_API_KEY = "TU_OPENAI_API_KEY"

# Configuración de notificaciones por Discord
DISCORD_BOT_TOKEN = "TU_DISCORD_BOT_TOKEN"
DISCORD_USER_ID = TU_DISCORD_USER_ID  # Reemplazar con tu ID de usuario en Discord (sin comillas)

# Configurar OpenAI
openai.api_key = OPENAI_API_KEY

# Autenticación con Twitter
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# Palabras clave para detectar sorteos
PALABRAS_CLAVE = ["sorteo", "giveaway", "ganar", "participa", "concurso"]

# Archivos de datos
LISTA_NEGRA_FILE = "lista_negra.json"
ESTADISTICAS_FILE = "estadisticas.json"
COMENTARIOS_FILE = "comentarios.json"

# Cargar datos
try:
    with open(LISTA_NEGRA_FILE, "r") as file:
        lista_negra = set(json.load(file))
except (FileNotFoundError, json.JSONDecodeError):
    lista_negra = set()

try:
    with open(ESTADISTICAS_FILE, "r") as file:
        estadisticas = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    estadisticas = {"sorteos_participados": 0, "ganados": 0}

try:
    with open(COMENTARIOS_FILE, "r") as file:
        comentarios_previos = json.load(file)
except (FileNotFoundError, json.JSONDecodeError):
    comentarios_previos = {}

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def guardar_datos():
    with open(LISTA_NEGRA_FILE, "w") as file:
        json.dump(list(lista_negra), file)
    with open(ESTADISTICAS_FILE, "w") as file:
        json.dump(estadisticas, file)
    with open(COMENTARIOS_FILE, "w") as file:
        json.dump(comentarios_previos, file)

# Enviar mensaje privado por Discord
def notificar_discord_dm(mensaje):
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        user = await bot.fetch_user(DISCORD_USER_ID)
        if user:
            await user.send(mensaje)
            logging.info("📢 Notificación enviada por DM en Discord")
        await bot.close()
    
    bot.run(DISCORD_BOT_TOKEN)

# Verificar si se ha ganado un sorteo
def verificar_ganador():
    if estadisticas["ganados"] > 0:
        mensaje = f"🎉 ¡Has ganado un sorteo! 🏆 Total ganados: {estadisticas['ganados']}"
        notificar_discord_dm(mensaje)

# Buscar y participar en sorteos
def buscar_sorteos():
    logging.info("Buscando sorteos...")
    for palabra in PALABRAS_CLAVE:
        for tweet in tweepy.Cursor(api.search_tweets, q=palabra, lang="es").items(5):
            try:
                if tweet.id in lista_negra or "RT @" in tweet.text:
                    continue
                
                tweet_id = tweet.id
                usuario = tweet.user.screen_name
                lista_negra.add(tweet_id)
                estadisticas["sorteos_participados"] += 1
                guardar_datos()
                
                api.create_favorite(tweet_id)
                api.retweet(tweet_id)
                logging.info("✔ Like y retweet realizado.")
                
                time.sleep(random.randint(30, 60))  # Evitar bloqueos
            except tweepy.TweepError as e:
                logging.error(f"Error: {e}")
            except StopIteration:
                break
    verificar_ganador()

# Iniciar bot en un hilo
def ejecutar_bot():
    while True:
        buscar_sorteos()
        logging.info("🔄 Esperando 45 minutos para la siguiente búsqueda...")
        time.sleep(2700)

bot_thread = threading.Thread(target=ejecutar_bot)
bot_thread.start()
