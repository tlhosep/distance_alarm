"""
PiPico Distance measuring with alarm and display
------------------------------------------------

This app uses

* Raspberry Pi Pico
* HC-SR04-P to measure the distance
* 1602 HD44780 2 line LCD display with I2C Bus
* 12V LED to show an alarm
* step down converter to 5.0 V
* 12 V Battery
* 10kOhm potentiometer
* 1Resistor 2k2
* 1Transistor NPN
* 2Resistors 10k

Info::

    Author.: (c) Thomas Lüth 2025
    Email..: info@tlc-it-consulting.com
    Created: 2025-04-23

Code
^^^^
"""
from time import sleep_ms
import utime
from machine import Pin, I2C, PWM, ADC
from machine_i2c_lcd import I2cLcd

VERSION = "1.2"
alarm_led = PWM(Pin(0))
alarm_led.freq(10000) #1000hz
alarm_led.duty_u16(32767>>6) #dark
trig = Pin(16, Pin.OUT)
echo = Pin(17, Pin.IN)
poti = ADC(0)
temp = ADC(4)
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
#start with version info
lcd.backlight_on()
trig.value(1)
lcd.putstr("Distance-alarm"+"\n"+"Version: "+VERSION)
sleep_ms(1000)
show_temp=0
TEMP_CONV = 3.3 / 65535
ALARM_CONV= 330 / 65535
no_measure=False

def calc_bar(alarm_dif:float, interval:float)->str:
    """Create the bar to show the distance left

    Args:
        alarm_dif (float): cm left until alarm level has been reached
        interval (float): increments for one char at the bar

    Returns:
        str: created bar-str up to 16char
    """
    steps=16-int(alarm_dif/interval)
#    print(f"steps:{steps:d} dif={alarm_dif:3.0f}")
    steps=min(16,steps)
    steps=max(1,steps)
    bar=""
    for _i in range(0,steps):
        bar += "\xff"
    return bar

while True:
    alarm_distance_raw=poti.read_u16()
    alarm_distance_cm=10.0+(alarm_distance_raw*ALARM_CONV)
    trig.value(0)
    utime.sleep_us(10)
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)
    fault_detection=1000
    while echo.value()==0 and fault_detection > 0:
        fault_detection-=1
    no_measure=fault_detection<1
    dist_diff_cm=200.0
    if not no_measure:
        tmr_start=utime.ticks_us()
        while echo.value()==1:
            pass
        tmr_end=utime.ticks_us()
        duration=utime.ticks_diff(tmr_end,tmr_start)
        distance_cm=duration*0.0171
        dist_diff_cm = distance_cm - alarm_distance_cm

    if dist_diff_cm < 5.0:
        alarm_led.freq(1000) #full on
        alarm_led.duty_u16(65535)
    elif dist_diff_cm < 15.0:
        alarm_led.freq(1000)
        alarm_led.duty_u16(32767)
    elif dist_diff_cm < 20.0:
        alarm_led.freq(1000)
        alarm_led.duty_u16(32767>>2)
    elif dist_diff_cm < 50.0:
        alarm_led.freq(1000)
        alarm_led.duty_u16(32767>>4)
    elif dist_diff_cm < 100.0:
        alarm_led.freq(1000)
        alarm_led.duty_u16(32767>>5)
    else:
        alarm_led.freq(1000)
        alarm_led.duty_u16(32767>>6)

    lcd.clear()
    if no_measure:
        msg1="Error:No measure"
    else:
        msg1=f"Distance: {distance_cm:3.0f} cm"
    if show_temp >3:
        volt = temp.read_u16() * TEMP_CONV
        room_temp=27-(volt-0.706)/0.001721
        msg2=f"Roomtemp = {room_temp:2.0f} C"
        show_temp=0
    elif show_temp == 2:
        msg2=f"Alarm = {alarm_distance_cm:3.0f} cm"
    else:
        msg2=calc_bar(dist_diff_cm,5.0)
    lcd.putstr(msg1+ "\n" +msg2)
    sleep_ms(1000)
    show_temp += 1
