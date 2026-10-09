import time
import json
import urllib.request
import urllib.parse
from datetime import datetime

class WeatherService:
    """
    Servicio de Clima Exterior Local para la ubicación geográfica de la torre hidropónica SIFMA.
    Utiliza la API abierta y gratuita Open-Meteo (sin necesidad de API keys).
    Soporta persistencia de coordenadas personalizadas (por defecto: Santa Marta, Colombia).
    Incluye caché en memoria (10 min) y fallback offline elegante si la torre no tiene internet.
    """
    _instance = None
    _cached_data = None
    _last_fetch_time = 0
    _CACHE_TTL = 600  # 10 minutos de caché

    # Coordenadas Oficiales SIFMA - Santa Marta, Magdalena, Colombia
    DEFAULT_LAT = 11.2408
    DEFAULT_LON = -74.1990
    DEFAULT_CITY = "Santa Marta, Magdalena"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WeatherService()
        return cls._instance

    @staticmethod
    def _interpret_wmo_code(code: int) -> dict:
        """Traduce códigos meteorológicos estándar WMO a descripción en español e icono."""
        mapping = {
            0: ("Cielo Despejado", "wb_sunny", "sunny"),
            1: ("Mayormente Despejado", "wb_sunny", "mostly_sunny"),
            2: ("Parcialmente Nublado", "partly_cloudy_day", "partly_cloudy"),
            3: ("Nublado", "cloud", "cloudy"),
            45: ("Neblina", "foggy", "fog"),
            48: ("Niebla con Escarcha", "foggy", "fog"),
            51: ("Llovizna Ligera", "grain", "drizzle"),
            53: ("Llovizna Moderada", "grain", "drizzle"),
            55: ("Llovizna Intensa", "grain", "drizzle"),
            61: ("Lluvia Ligera", "water_drop", "rain"),
            63: ("Lluvia Moderada", "water_drop", "rain"),
            65: ("Lluvia Fuerte", "rainy", "rain"),
            80: ("Chubascos Aislados", "shower", "rain"),
            81: ("Chubascos Moderados", "shower", "rain"),
            82: ("Chubascos Violentos", "thunderstorm", "rain"),
            95: ("Tormenta Eléctrica", "thunderstorm", "storm"),
            96: ("Tormenta con Granizo Ligero", "thunderstorm", "storm"),
            99: ("Tormenta con Granizo Fuerte", "thunderstorm", "storm")
        }
        desc, icon, badge_class = mapping.get(code, ("Clima Estable", "cloud_queue", "cloudy"))
        return {
            "description": desc,
            "icon": icon,
            "badge_class": badge_class
        }

    def get_current_weather(self, lat: float = None, lon: float = None, city_name: str = None) -> dict:
        """
        Obtiene el clima actual para las coordenadas configuradas.
        Si falla la conexión a internet, retorna el último valor en caché o un estado offline seguro.
        """
        now = time.time()
        lat = lat if lat is not None else self.DEFAULT_LAT
        lon = lon if lon is not None else self.DEFAULT_LON
        city = city_name or self.DEFAULT_CITY

        if self._cached_data and (now - self._last_fetch_time < self._CACHE_TTL):
            return self._cached_data

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,surface_pressure&"
            f"timezone=auto"
        )

        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'SIFMA-Hydroponics-Monitor/1.0'}
            )
            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    raw = json.loads(response.read().decode('utf-8'))
                    current = raw.get('current', {})
                    wmo_info = self._interpret_wmo_code(current.get('weather_code', 0))

                    data = {
                        "online": True,
                        "temperature_c": round(current.get('temperature_2m', 30.0), 1),
                        "apparent_temperature_c": round(current.get('apparent_temperature', 32.0), 1),
                        "humidity_rh": int(current.get('relative_humidity_2m', 70)),
                        "wind_speed_kmh": round(current.get('wind_speed_10m', 10.0), 1),
                        "weather_code": current.get('weather_code', 0),
                        "weather_description": wmo_info["description"],
                        "icon": wmo_info["icon"],
                        "badge_class": wmo_info["badge_class"],
                        "location_name": city,
                        "latitude": lat,
                        "longitude": lon,
                        "updated_at": datetime.now().strftime("%H:%M"),
                        "status_text": "En Línea (Open-Meteo)"
                    }
                    self._cached_data = data
                    self._last_fetch_time = now
                    return data
        except Exception:
            pass

        # Fallback offline si no hay conexión o expira el timeout
        if self._cached_data:
            cached_copy = dict(self._cached_data)
            cached_copy["status_text"] = "Caché Local (Sin conexión)"
            cached_copy["online"] = False
            return cached_copy

        return {
            "online": False,
            "temperature_c": 30.0,
            "apparent_temperature_c": 32.0,
            "humidity_rh": 72,
            "wind_speed_kmh": 8.0,
            "weather_code": 0,
            "weather_description": "Modo Local Autónomo",
            "icon": "cloud_off",
            "badge_class": "offline",
            "location_name": city,
            "latitude": lat,
            "longitude": lon,
            "updated_at": datetime.now().strftime("%H:%M"),
            "status_text": "Nodo Autónomo (Sin Internet)"
        }

    def clear_cache(self):
        """Invalida la caché para forzar una consulta inmediata ante cambio de coordenadas."""
        self._cached_data = None
        self._last_fetch_time = 0
