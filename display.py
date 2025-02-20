#!/usr/bin/env python3
"""display.py
Displays NetAtmo weather station data on a local screen
input: data.json file, result of NetAtmo getstationsdata API
screen: PaPiRus ePaper / eInk Screen HAT for Raspberry Pi - 2.7"
output: copy of the screen in file: image.bmp
"""

import json
import time
import os
import sys
import logging
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

logging.basicConfig(level=logging.WARNING)

WHITE = 1
BLACK = 0
# Font file: path below if installed with
# sudo apt install fonts-freefont-ttf
font_file = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
if not os.path.isfile(font_file):
    font_file = '../freefont/FreeSans.ttf'
    if not os.path.isfile(font_file):
        exit()
# File names
data_filename = 'data.json'
image_filename = 'image.bmp'
# Global variables
g_data = dict()
g_image = None

def datetimestr(t):
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t))

def timestr(t):
    return time.strftime('%H:%M',time.localtime(t))

def read_json(filename):
    """Read a JSON file to a dict object."""
    with open(filename, 'r') as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            data = dict()
    return data

def trend_symbol(trend):
    """Unicode symbol for temperature trend"""
    if trend == 'up':
        return '\u2197' # '↗' U+2197
    elif trend == 'down':
        return '\u2198' # '↘' U+2198
    elif trend == 'stable':
        return '\u2192' # '→' U+2192
    else:
        return ' '

def textsize(text, font):
    left, top, right, bottom = font.getbbox(text)
    width, height = int(right - left), int(bottom - top)
    return width, height

def draw_image():
    """Draws the image in memory (g_image)"""
    global g_data
    global g_image

    # prepare for drawing
    draw = ImageDraw.Draw(g_image)
    width, height = g_image.size

    # base font size on mono spaced font
    #font_size_temp = int((width - 4) / (10 * 0.65))     # room for 10 chars
    #font_size_time = int((width - 10) / (20 * 0.65))    # YYYY-MM-DD HH:MM:SS
    #font_temp = ImageFont.truetype(font_file, font_size_temp)
    #font_time = ImageFont.truetype(font_file, font_size_time)
    font_temp = ImageFont.truetype(font_file, 25)
    font_time = ImageFont.truetype(font_file, 20)

    # read data
    if os.path.isfile(data_filename):
        g_data = read_json(data_filename)
    else:
        logging.error("No data file")
        return
    if not ("body" in g_data):
        logging.error("Bad data format")
        return

    # Units
    # see https://dev.netatmo.com/en-US/resources/technical/reference/weather/getstationsdata
    # for details
    user_admin = g_data["body"]["user"]["administrative"]
    unit_temp = ['°C', '°F'][user_admin["unit"]]
    unit_rain = ['mm/h', 'in/h'][user_admin["unit"]]
    unit_wind = ['kph', 'mph', 'm/s', 'beaufort', 'knot'][user_admin["windunit"]]
    unit_pressure = ['mbar', 'inHg', 'mmHg'][user_admin["pressureunit"]]
    unit_CO2 = ['ppm', 'ppm', 'ppm'][user_admin["unit"]]
    unit_noise = ['dB', 'dB', 'dB'][user_admin["unit"]]
    unit_humidity = ['%', '%', '%'][user_admin["unit"]]

    # get and format values
    indoor_temp_str = 'N/A'
    indoor_pressure_str = 'N/A'
    indoor_co2_str = 'N/A'
    indoor_noise_str = 'N/A'
    indoor_humidity_str = 'N/A'
    outdoor_temp_str = 'N/A'
    outdoor_humidity = 'N/A'
    rain_str = 'N/A'
    wind_str = 'N/A'

    data_time_str = timestr(g_data["time_server"])

    # main module: indoor temperature (line 1) and pressure (not used)
    device = g_data["body"]["devices"][0]
    if "dashboard_data" in device:
        indoor_data = device["dashboard_data"]
        indoor_temp_str = '{0:.2f}'.format(indoor_data["Temperature"]) + " " + unit_temp
        if "temp_trend" in indoor_data:
            indoor_temp_str += trend_symbol(indoor_data["temp_trend"])
        indoor_pressure_str = '{0:.1f}'.format(indoor_data["Pressure"]) + " " + unit_pressure
        if "pressure_trend" in indoor_data:
            indoor_pressure_str += trend_symbol(indoor_data["pressure_trend"])
        indoor_co2_str = '{0:.1f}'.format(indoor_data["CO2"]) + " " + unit_CO2
        indoor_noise_str = '{0:.1f}'.format(indoor_data["Noise"]) + " " + unit_noise
        indoor_humidity_str = '{0:.1f}'.format(indoor_data["Humidity"]) + " " + unit_humidity

    # other modules: outdoor temperature, rain (lines 2 & 3), wind (unused), optional indoor (unused)
    for module in device["modules"]:
        if "dashboard_data" in module:
            module_type = module["type"]
            module_data = module["dashboard_data"]
            if module_type == "NAModule1":
                # Outdoor Module
                outdoor_temp_str = '{0:.2f}'.format(module_data["Temperature"]) + " " + unit_temp
                if "temp_trend" in module_data:
                    outdoor_temp_str += trend_symbol(module_data["temp_trend"])
                outdoor_humidity = '{0:.2f}'.format(module_data["Humidity"]) + " " + unit_humidity
            elif module_type == "NAModule2":
                # Wind Gauge
               wind_str = '{0:.1f}'.format(module_data["WindStrength"]) + " " + unit_wind
            elif module_type == "NAModule3":
                # Rain Gauge
               rain_str = '{0:.1f}'.format(module_data["Rain"]) + " " + unit_rain
            elif module_type == "NAModule4":
                # Optional indoor module
                pass

    # width and height of strings
    (width_indoor, height_indoor) = textsize(indoor_temp_str, font=font_temp)
    (width_outdoor, height_outdoor) = textsize(outdoor_temp_str, font=font_temp)
#    (width_rain, height_rain) = textsize(rain_str, font=font_temp)
    (width_time, height_time) = textsize(data_time_str, font=font_time)

    # which is bigger?
    txtwidth, txtheight = width_indoor, height_indoor
    if width_outdoor > txtwidth:
        txtwidth = width_outdoor
#    if width_rain > txtwidth:
#        txtwidth = width_rain

    x = int((width - txtwidth) / 2) -40  # Move text 40 pixels to the left
    y = int((height - 5*txtheight - 10) / 2.5)

    draw.rectangle((2, 2, width - 4, height - 4), fill=WHITE, outline=BLACK)
    # temperatures and rain
    draw.text((x, y),f"Vonku: { outdoor_temp_str}", fill=BLACK, font = font_temp)
    draw.text((x, y + txtheight + 0),f"Dnu: {indoor_temp_str}", fill=BLACK, font=font_temp)
    draw.text((x, y + 2*txtheight + 4),f"Tlak: {indoor_pressure_str}", fill=BLACK, font = font_temp)
    draw.text((x, y + 3*txtheight + 8),f"CO2: {indoor_co2_str}", fill=BLACK, font = font_temp)
    draw.text((x, y + 4*txtheight + 12),f"Hluk: { indoor_noise_str}", fill=BLACK, font = font_temp)
    draw.text((x, y + 5*txtheight + 16),f"Vlhkost: { indoor_humidity_str}", fill=BLACK, font = font_temp)
    # draw.text((x, y + 2*txtheight + 10), rain_str, fill=BLACK, font = font_temp)
    # time
    draw.text((width - 255, 5), data_time_str, fill = BLACK, font = font_time)

def main():
    """Main function"""
    global g_image

    try:
        # *** PaPiRus ePaper / eInk Screen HAT for Raspberry Pi - 2.7" ***
        from papirus import Papirus
        papirus = Papirus(rotation = 0)
        g_image = Image.new('1', papirus.size, WHITE)
        draw_image()
        g_image.save(image_filename)
        papirus.display(g_image)
        papirus.update()
        return
    except:
        logging.debug("Papirus failed.", exc_info=1)

    try:
        # *** Waveshare 2.7inch e-Paper HAT ***
        libdir = os.path.realpath(os.getenv('HOME') + '/e-Paper/RaspberryPi_JetsonNano/python/lib')
        if os.path.exists(libdir):
            sys.path.append(libdir)
        else:
            libdir = os.path.realpath(os.getenv('HOME') + '/e-Paper/RaspberryPi&JetsonNano/python/lib')
            if os.path.exists(libdir):
                sys.path.append(libdir)
        from waveshare_epd import epd2in7
        epd = epd2in7.EPD()
        epd.init()
        g_image = Image.new('1', (epd.height, epd.width), 255)
        draw_image()
        g_image.save(image_filename)
        epd.display(epd.getbuffer(g_image))
        epd.sleep()
        return
    except:
        logging.debug("Waveshare failed.", exc_info=1)

    # *** no known screen: just save the bmp
    logging.debug("No known screen.")
    g_image = Image.new('1', (264, 176), WHITE)
    draw_image()
    g_image.save(image_filename)

# main
if __name__ == '__main__':
    main()
