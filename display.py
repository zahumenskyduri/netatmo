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
try:
    from papirus import Papirus
    from PIL import Image
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except ImportError as e:
    print(e)
    sys.exit(1)

WHITE = 1
BLACK = 0

#FONT_FILE = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
FONT_FILE = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
#FONT_FILE = '/usr/share/fonts/truetype/freefont/FreeSerif.ttf'

data_filename = "data.json"
image_filename = "image.bmp"

g_data = dict()

def datetimestr(t):
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(t))

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

def main():
    """Main function"""
    global g_data
    papirus = Papirus(rotation = 0)
    #papirus.clear()

    # initially set all white background
    image = Image.new('1', papirus.size, WHITE)

    # prepare for drawing
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # base font size on mono spaced font
    font_size_temp = int((width - 4) / (10 * 0.65))     # room for 10 chars
    font_temp = ImageFont.truetype(FONT_FILE, font_size_temp)
    font_size_time = int((width - 10) / (20 * 0.65))    # YYYY-MM-DD HH:MM:SS
    font_time = ImageFont.truetype(FONT_FILE, font_size_time)

    # read data
    if os.path.isfile(data_filename):
        g_data = read_json(data_filename)
    else:
        sys.exit(1)
    if not ("body" in g_data):
        sys.exit(1)

    # extract data
    device = g_data["body"]["devices"][0]
    #place = device["place"]
    indoor = device["dashboard_data"]
    outdoor = device["modules"][0]["dashboard_data"]
    rain = device["modules"][1]["dashboard_data"]

    # get values
    data_time_str = datetimestr(g_data["time_server"])
    indoor_temp_str = '{0:.2f}'.format(indoor["Temperature"]) + '°C' + trend_symbol(indoor["temp_trend"])
    outdoor_temp_str = '{0:.2f}'.format(outdoor["Temperature"]) + '°C' + trend_symbol(outdoor["temp_trend"])
    rain_str = '{0:.2f}'.format(rain["Rain"]) + 'mm/h'

    # center the temperatures
    #(txtwidth, txtheight) = draw.textsize(indoor_temp_str, font=font_temp)
    (width_indoor, height_indoor) = draw.textsize(indoor_temp_str, font=font_temp)
    (width_outdoor, height_outdoor) = draw.textsize(outdoor_temp_str, font=font_temp)
    (width_rain, height_rain) = draw.textsize(rain_str, font=font_temp)

    txtwidth, txtheight = width_indoor, height_indoor
    if width_outdoor > txtwidth:
        txtwidth = width_outdoor
    if width_rain > txtwidth:
        txtwidth = width_rain

    #print("txtwidth:", txtwidth)
    #print("width_indoor:", width_indoor)
    #print("width_outdoor:", width_outdoor)

    x = int((width - txtwidth) / 2)
    y = int((height - 3*txtheight - 10) / 2)

    draw.rectangle((2, 2, width - 2, height - 2), fill=WHITE, outline=BLACK)

    #draw.text((x + txtwidth - width_indoor, y), indoor_temp_str, fill=BLACK, font=font_temp)
    #draw.text((x + txtwidth - width_outdoor, y + txtheight + 5), outdoor_temp_str, fill=BLACK, font = font_temp)
    #draw.text((x + txtwidth - width_rain, y + 2*txtheight + 10), rain_str, fill=BLACK, font = font_temp)
    draw.text((x, y), indoor_temp_str, fill=BLACK, font=font_temp)
    draw.text((x, y + txtheight + 5), outdoor_temp_str, fill=BLACK, font = font_temp)
    draw.text((x, y + 2*txtheight + 10), rain_str, fill=BLACK, font = font_temp)

    draw.text((5, 5), data_time_str, fill = BLACK, font = font_time)

    papirus.display(image)
    papirus.update()
    image.save(image_filename)

# main
if "__main__" == __name__:
        main()
