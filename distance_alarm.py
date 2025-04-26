"""
PiPico Distance measuring with alarm and display
------------------------------------------------

This app uses

* Raspberry Pi Pico
* HC-SR04-P to measure the distance
* 1602 HD44780 2 line LCD display with I2C Bus
* 12V LED to set an alarm
* step down to 3.3 V
* step down to 5.0 V
* 12 V Battery
* 10kOhm potentiometer

Info::

    Author.: (c) Thomas Lüth 2025
    Email..: info@tlc-it-consulting.com
    Created: 2025-04-23

Code
^^^^
"""
from time import sleep_ms
from machine import Pin, I2C, PWM, ADC
from machine_i2c_lcd import I2cLcd
import utime
version = "0.1"
alarm_led = PWM(Pin(0))
alarm_led.freq(8) #8hz (min) at the beginning
alarm_led.duty_u16(int(32767/4)) #12,5 % duty cycle
trig = Pin(16, Pin.OUT)
echo = Pin(17, Pin.IN)
poti = ADC(0)
i2c = I2C(0, sda=Pin(20), scl=Pin(21), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
#start with version info
lcd.backlight_on()
trig.value(1)
lcd.putstr("Distance-alarm"+"\n"+"Version: "+version)
sleep_ms(1000)

while True:
    alarm_distance_raw=poti.read_u16()
    alarm_distance_cm=10.0+(alarm_distance_raw/65535)*300
    trig.value(0)
    utime.sleep_us(10)
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)
    while echo.value()==0:
        pass
    tmr_start=utime.ticks_us()
    while echo.value()==1:
        pass
    tmr_end=utime.ticks_us()
    duration=utime.ticks_diff(tmr_end,tmr_start)
    distance_cm=duration*0.0171
    distance_diff_cm = distance_cm - alarm_distance_cm
    if distance_diff_cm < 5.0:
        alarm_led.freq(1000) #full on
        alarm_led.duty_u16(65535)
    elif distance_diff_cm < 15.0:
        alarm_led.freq(30)
        alarm_led.duty_u16(32767)
    elif distance_diff_cm < 20.0:
        alarm_led.freq(22)
        alarm_led.duty_u16(32767)
    elif distance_diff_cm < 50.0:
        alarm_led.freq(18)
        alarm_led.duty_u16(32767)
    elif distance_diff_cm < 100.0:
        alarm_led.freq(12)
        alarm_led.duty_u16(32767)
    else:
        alarm_led.freq(8)
        alarm_led.duty_u16(32767)
        
    lcd.clear()
    msg1="Dist.: "+ str(distance_cm)[:6]+"cm"
    msg2="Alarm: "+ str(alarm_distance_cm)[:6]+"cm"
    lcd.putstr(msg1+"\n"+msg2)
    sleep_ms(1000)
    