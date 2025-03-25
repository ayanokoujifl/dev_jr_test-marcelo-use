from fastapi import FastAPI, HTTPException
import requests
import sqlite3

app = FastAPI()




def get_db_connection():
  db = sqlite3.connect("weather.db")
  cursor = db.cursor()
  cursor.execute("""CREATE TABLE IF NOT EXISTS weather (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  city VARCHAR(255) NOT NULL UNIQUE,
  temperature VARCHAR(5) NOT NULL,
  humidity FLOAT NOT NULL,
  pressure FLOAT NOT NULL,
  feels_like FLOAT NOT NULL,
  description VARCHAR(255) NOT NULL,
  main VARCHAR(255) NOT NULL)
  """)

  db.commit()
  return db

#Para capturar a latitude e longitude de uma cidade, o endpoint retorna os valores das coordenadas
#http://api.openweathermap.org/geo/1.0/direct?q=London&limit=5&appid=34b2f341f158272c886ddec9c464958a

#Para capturar o histórico de uma cidade por data
#https://history.openweathermap.org/data/2.5/history/city?lat={lat}&lon={lon}&type=hour&start={start}&cnt={cnt}&appid={API key}

API_KEY = "34b2f341f158272c886ddec9c464958a"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}"

def fetch_weather_data(city : str):
  try:
    response = requests.get(WEATHER_URL.format(city, API_KEY))
    response.raise_for_status()  # Levanta erro caso a requisição falhe
    data = response.json()
    if "main" not in data:
        raise ValueError("Resposta inválida da API")
    return data
  except requests.RequestException as e:
    raise HTTPException(status_code=500, detail=f"Erro ao fazer a requisição a API: {str(e)}")
  except (ValueError, KeyError) as e:
    raise HTTPException(status_code=400, detail=f"Erro ao processar a resposta da API: {str(e)}")

@app.get("/")
def index():
  return {"message":"Bem-vindo ao teste para Desenvolvedor Jr. na USE",
        "autor":"Luís Gustavo Ferreira Leite",
        "Rota de busca por cidade":"/weather/{city}",
        "version":"1.0.0"}

@app.get("/weather/{city}")
async def get_weather(city: str):
  data = fetch_weather_data(city)
  weather_data = {
      "city": data["name"],
      "temperature": str(data["main"]["temp"])+"°C",
      "humidity": data["main"]["humidity"],
      "pressure": data["main"]["pressure"],
      "feels_like": data["main"]["feels_like"],
      "description": data["weather"][0]["description"],
      "main": data["weather"][0]["main"]
  }

  try:
      db = get_db_connection()
      cursor = db.cursor()
      cursor.execute(
          """
          INSERT INTO weather (city, temperature, humidity, pressure, feels_like, description, main)
          VALUES (:city, :temperature, :humidity, :pressure, :feels_like, :description, :main)
          ON CONFLICT(city) 
          DO UPDATE SET 
              temperature = excluded.temperature,
              humidity = excluded.humidity,
              pressure = excluded.pressure,
              feels_like = excluded.feels_like,
              description = excluded.description,
              main = excluded.main
          """, weather_data
      )
      db.commit()
      return weather_data
  except Exception as e:
      raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco de dados: {str(e)}")


