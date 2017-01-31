# aeon_labs_led_bulb
Adaptor for Aeon Labs LED Bulb

This adaptor works with the Light Controller bridge app. It expects data in the form:

{'soft_white': '0', 'blue': '0', 'cold_white': '205', 'green': '0', 'red': '0'}

The values are between 0 (off) and 255 (fully on) and are strings (not int).
