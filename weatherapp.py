import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from datetime import datetime
import io
from collections import defaultdict

# ------------------------- CONFIG -------------------------
API_KEY = "70cdf4650c17be7b51f6f0c4b4577550"  # Replace with your free OpenWeatherMap API key
CURRENT_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
REFRESH_INTERVAL = 10 * 60 * 1000  # 10 minutes

# Background images for weather conditions (add these in a folder named "backgrounds")
BACKGROUND_IMAGES = {
    "clear": "backgrounds/sunny.jpg",
    "cloud": "backgrounds/cloudy.jpg",
    "rain": "backgrounds/rainy.jpg",
    "snow": "backgrounds/snow.jpg",
    "default": "backgrounds/default.jpg"
}

# ---------------------- FUNCTIONS ------------------------
def kelvin_to_celsius(k):
    return round(k - 273.15, 1)

def fetch_current(city):
    try:
        params = {"q": city, "appid": API_KEY}
        response = requests.get(CURRENT_URL, params=params, timeout=10)
        data = response.json()
        if data.get("cod") != 200:
            return None, data.get("message", "Error fetching current weather")
        return data, None
    except Exception as e:
        return None, str(e)

def fetch_forecast(city):
    try:
        params = {"q": city, "appid": API_KEY}
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        data = response.json()
        if data.get("cod") != "200":
            return None, data.get("message", "Error fetching forecast")
        return data, None
    except Exception as e:
        return None, str(e)

def get_bg_image(desc):
    desc = desc.lower()
    for key in ["clear", "cloud", "rain", "snow"]:
        if key in desc:
            try:
                return Image.open(BACKGROUND_IMAGES[key])
            except:
                continue
    try:
        return Image.open(BACKGROUND_IMAGES["default"])
    except:
        return None

def get_bg_color(desc):
    desc = desc.lower()
    if "rain" in desc:
        return "#76c7ff"
    elif "cloud" in desc:
        return "#b0c4de"
    elif "sun" in desc or "clear" in desc:
        return "#ffd27f"
    elif "snow" in desc:
        return "#e0f7fa"
    else:
        return "#d3d3d3"

def create_card(parent, text, icon_url, bg_color="#fff"):
    card = tk.Frame(parent, bg=bg_color, bd=2, relief="raised")
    try:
        icon_response = requests.get(icon_url, timeout=5)
        icon_img = Image.open(io.BytesIO(icon_response.content)).resize((50,50))
        icon_photo = ImageTk.PhotoImage(icon_img)
        icon_label = tk.Label(card, image=icon_photo, bg=bg_color)
        icon_label.image = icon_photo
        icon_label.pack(pady=5)
    except:
        tk.Label(card, text="No Icon", bg=bg_color).pack(pady=5)
    tk.Label(card, text=text, bg=bg_color, wraplength=100, justify="center").pack(pady=5)
    card.pack(side="left", padx=5, pady=5)
    return card

# ---------------------- BACKGROUND HANDLING ------------------------
current_bg_img = None  # To store PIL image
bg_photo = None        # To store Tkinter PhotoImage

def resize_bg(event=None):
    global bg_photo
    if current_bg_img:
        resized = current_bg_img.resize((event.width, event.height))
        bg_photo = ImageTk.PhotoImage(resized)
        bg_label.config(image=bg_photo)
        bg_label.image = bg_photo

def set_bg(desc):
    global current_bg_img, bg_photo
    current_bg_img = get_bg_image(desc)
    if current_bg_img:
        resized = current_bg_img.resize((root.winfo_width(), root.winfo_height()))
        bg_photo = ImageTk.PhotoImage(resized)
        bg_label.config(image=bg_photo)
        bg_label.image = bg_photo

# ---------------------- UPDATE WEATHER ------------------------
def update_weather():
    city = city_entry.get().strip()
    if not city:
        messagebox.showerror("Error", "Please enter a city name")
        return

    # --- Current weather ---
    current_data, error = fetch_current(city)
    if error:
        messagebox.showerror("Error", error)
        return

    try:
        weather_desc = current_data['weather'][0]['description'].capitalize()
        temp = kelvin_to_celsius(current_data['main']['temp'])
        wind_speed = current_data['wind']['speed']

        current_label.config(text=f"{city}\n{weather_desc}\nTemp: {temp}°C\nWind: {wind_speed} m/s")

        # --- Dynamic Background ---
        set_bg(weather_desc)

        # Weather icon
        icon_code = current_data['weather'][0]['icon']
        icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
        icon_response = requests.get(icon_url)
        icon_img = Image.open(io.BytesIO(icon_response.content))
        icon_photo = ImageTk.PhotoImage(icon_img)
        icon_label.config(image=icon_photo)
        icon_label.image = icon_photo
    except Exception as e:
        messagebox.showerror("Error", f"Current weather error: {e}")
        return

    # --- Forecast ---
    forecast_data, error = fetch_forecast(city)
    if error:
        messagebox.showerror("Error", error)
        return

    # --- Hourly forecast ---
    for widget in hourly_inner.winfo_children():
        widget.destroy()
    try:
        for forecast in forecast_data['list'][:8]:
            time = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
            temp_f = kelvin_to_celsius(forecast['main']['temp'])
            desc = forecast['weather'][0]['description'].capitalize()
            icon = f"http://openweathermap.org/img/wn/{forecast['weather'][0]['icon']}@2x.png"
            bg = get_bg_color(desc)
            create_card(hourly_inner, f"{time}\n{temp_f}°C\n{desc}", icon, bg)
    except Exception as e:
        messagebox.showerror("Error", f"Hourly forecast error: {e}")
        return

    # --- Daily forecast ---
    for widget in daily_inner.winfo_children():
        widget.destroy()
    try:
        daily_data = defaultdict(list)
        for forecast in forecast_data['list']:
            date_str = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
            daily_data[date_str].append(forecast)

        count = 0
        for date_str, forecasts in daily_data.items():
            if count >= 7:
                break
            temps = [kelvin_to_celsius(f['main']['temp']) for f in forecasts]
            descs = [f['weather'][0]['description'] for f in forecasts]
            icons = [f['weather'][0]['icon'] for f in forecasts]

            avg_temp = round(sum(temps)/len(temps),1)
            main_desc = max(set(descs), key=descs.count)
            icon_code = icons[0]
            icon_url = f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
            bg = get_bg_color(main_desc)
            date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%a %d')
            create_card(daily_inner, f"{date_display}\n{avg_temp}°C\n{main_desc.capitalize()}", icon_url, bg)
            count += 1
    except Exception as e:
        messagebox.showerror("Error", f"Daily forecast error: {e}")
        return

    root.after(REFRESH_INTERVAL, update_weather)

# ------------------------ GUI ----------------------------
root = tk.Tk()
root.title("Professional Weather Dashboard")
root.geometry("1000x750")

# Dynamic Background Label
bg_label = tk.Label(root)
bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
root.bind("<Configure>", resize_bg)  # Resize background on window resize

# Input frame
input_frame = tk.Frame(root, bg="#f0f4f7")
input_frame.pack(pady=10)
tk.Label(input_frame, text="Enter City:", bg="#f0f4f7").pack(side="left", padx=5)
city_entry = tk.Entry(input_frame, width=30)
city_entry.pack(side="left", padx=5)
tk.Button(input_frame, text="Get Weather", command=update_weather).pack(side="left", padx=5)

# Current weather
current_label = tk.Label(root, text="", font=("Helvetica", 16), bg="#f0f4f7")
current_label.pack(pady=10)
icon_label = tk.Label(root, bg="#f0f4f7")
icon_label.pack()

# Hourly forecast scroll
tk.Label(root, text="Next 24h Forecast (3-hour intervals)", font=("Helvetica",14), bg="#f0f4f7").pack(pady=5)
hourly_container = tk.Frame(root, bg="#f0f4f7")
hourly_container.pack(fill="x")
hourly_canvas = tk.Canvas(hourly_container, height=180, bg="#f0f4f7")
hourly_scrollbar = ttk.Scrollbar(hourly_container, orient="horizontal", command=hourly_canvas.xview)
hourly_inner = tk.Frame(hourly_canvas, bg="#f0f4f7")
hourly_inner.bind("<Configure>", lambda e: hourly_canvas.configure(scrollregion=hourly_canvas.bbox("all")))
hourly_canvas.create_window((0,0), window=hourly_inner, anchor="nw")
hourly_canvas.configure(xscrollcommand=hourly_scrollbar.set)
hourly_canvas.pack(side="top", fill="x", expand=True)
hourly_scrollbar.pack(side="bottom", fill="x")

# Daily forecast scroll
tk.Label(root, text="7-Day Daily Forecast", font=("Helvetica",14), bg="#f0f4f7").pack(pady=5)
daily_container = tk.Frame(root, bg="#f0f4f7")
daily_container.pack(fill="x")
daily_canvas = tk.Canvas(daily_container, height=180, bg="#f0f4f7")
daily_scrollbar = ttk.Scrollbar(daily_container, orient="horizontal", command=daily_canvas.xview)
daily_inner = tk.Frame(daily_canvas, bg="#f0f4f7")
daily_inner.bind("<Configure>", lambda e: daily_canvas.configure(scrollregion=daily_canvas.bbox("all")))
daily_canvas.create_window((0,0), window=daily_inner, anchor="nw")
daily_canvas.configure(xscrollcommand=daily_scrollbar.set)
daily_canvas.pack(side="top", fill="x", expand=True)
daily_scrollbar.pack(side="bottom", fill="x")

root.mainloop()
