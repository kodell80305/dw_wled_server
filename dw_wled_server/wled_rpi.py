#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
import argparse
import math
from queue import Queue
from rpi_ws281x import *
import config


# LED strip configuration:
#LED_COUNT = 16 #LED_COUNT = 16 in config.py
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


strip = 0
current_effect = -1   # -1 = no effect
current_playist = -1

# empty variable declarations, to stop Python from complaining

theaterChase = lambda x: x
rainbow = lambda x: x
rainbowCycle = lambda x: x
theaterChaseRainbow = lambda x: x
strip = None

effects_list = [
    {
        # Static color effect - should always be first - defines the default
        # state of the LEDs
        "name": "Static",
        "description": "Solid color lighting effect",
        "parameters": {
            "color": "#0000FF",
            "brightness": 128
      }
    },
    {
        "func": theaterChase,
        "name": "theaterChase",
        "description": "Movie theater light style chaser animation.",
        "parameters": {
            "wait_ms": 20,
        }
    },
    {
        "func": rainbow,
        "name": "rainbow",
        "description": "A smooth rainbow effect that cycles through colors",
        "parameters": {
            "wait_ms": 20,
        }
    },
    {
        "func": rainbowCycle,
        "name": "rainbowCycle",
        "description": "Draw rainbow that uniformly distributes itself across all pixels.",
        "parameters": {
            "speed": 50,
            "intensity": 128
        }
    },
    {
        "func": theaterChaseRainbow,
        "name": "theaterChaseRainbow",
        "description": "Rainbow movie theater light style chaser animation",
        "parameters": {
            "speed": 50,
            "intensity": 128
        }
    }
]

#For now I'm just using the fact that a message is waiting to interrupt the effect ... if it's
#a command like setting the led brightness, then we'll restart the pattern.   Any other command
#will set a different effect to run.  
def checkCancel(wait_ms=100):
    time.sleep(wait_ms/1000.0)
    if not config.myQueue.empty():
        return True
    return False    

def get_effects():
    json_effects = []

    for i, effect in enumerate(effects_list):
        # Make copy of effect before modifying it
        effect = dict(effect)
        # Add id to function
        effect['id'] = i
        del effect['func']  # Can't put functions into a JSON, so remove it
        json_effects.append(effect)

    return json_effects

def run_effects(effect_id): 
    effect = effects_list[effect_id] 
    function = effect['func']
    print("Running effect", effect['name'])    

    function(strip)

def update_effect(effect_id):
    global current_effect, current_pl
    print("in update_effect()", effect_id)
    current_pl  =  -1
    current_effect = effect_id

def update_playlist(playlist_id):
    global current_effect, current_pl   
    print("in update_playlist()", playlist_id)
    current_pl = playlist_id
    current_effect = -1


def init_rpi():
    global strip

    print("Initializing", config.LED_COUNT)
    strip = PixelStrip(config.LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, 128, LED_CHANNEL, config.LED_COLOR )
  
    strip.begin()



def run_rpi_app():
    global current_effect

    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    
    for i in range(0, config.SEGMENT_0_START):
        strip.setPixelColor(i, Color(128,128,128))
    
    try:
        print('Waiting for cmd')      
        while True:
            time.sleep(100/1000.0)
            
            if not config.myQueue.empty():
                func, args = config.myQueue.get()
                func(*args)

            if(current_effect > 0):
                run_effects(current_effect)


    except Exception as e: # KeyboardInterrupt:
        breakpoint()
        if args.clear:
            all_off()

    
def update_bri(bri_arg):
    strip.setBrightness(bri_arg)
    strip.show()
 
        
def all_off():
    global current_effect, current_pl
    current_effect = -1
    current_pl = -1
    for i in range(config.SEGMENT_0_START, strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    
    strip.show()

def set_led(led_colors):
    global current_effect, current_pl
    current_effect = -1
    current_pl = -1
    #set leds to the values in the list led_colors
    #breakpoint()
    print("led_color", led_colors)
    for i in range(config.SEGMENT_0_START, strip.numPixels()):
        strip.setPixelColor(i, Color(*led_colors[i]))
    strip.show()
    

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(config.SEGMENT_0_START, strip.numPixels()):
 
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)
        #every effect should return if anything is in the queue
        if not config.myQueue.empty():
            return


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(config.SEGMENT_0_START, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            #every effect should return if anything is in the queue
            if not config.myQueue.empty():
                return
            for i in range(config.SEGMENT_0_START, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
                #every effect should return if anything is in the queue
        if not config.myQueue.empty():
            return
        for i in range(config.SEGMENT_0_START, strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)
        #every effect should return if anything is in the queue
        if not config.myQueue.empty():
            return


def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(config.SEGMENT_0_START, strip.numPixels()):
            strip.setPixelColor(i, wheel(
                (int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)
        #every effect should return if anything is in the queue
        if not config.myQueue.empty():
            return

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(config.SEGMENT_0_START, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            #every effect should return if anything is in the queue
            if not config.myQueue.empty():
                return
            for i in range(config.SEGMENT_0_START, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)







 
