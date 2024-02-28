import os
from RPi import GPIO
 
step = 1
toggle = False
 
GPIO.setmode(GPIO.BCM) 
 
CLK_PIN = 17
DT_PIN = 18
SW_PIN = 27
 
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
 
counter = 0
 
# Events
def clkClicked(channel):
        global counter
        global step
 
        clkState = GPIO.input(CLK_PIN)
        dtState = GPIO.input(DT_PIN)
 
        if clkState == 0 and dtState == 1:
                counter = counter + step
                print ("Counter ", counter)
 
def dtClicked(channel):
        global counter
        global step
 
        clkState = GPIO.input(CLK_PIN)
        dtState = GPIO.input(DT_PIN)
         
        if clkState == 1 and dtState == 0:
                counter = counter - step
                print ("Counter ", counter)
 
def swToggle(channel):
        global toggle
        toggle = not paused
        print ("Paused ", toggle)             
                 
GPIO.add_event_detect(CLK_PIN, GPIO.FALLING, callback=clkClicked, bouncetime=1)
GPIO.add_event_detect(DT_PIN, GPIO.FALLING, callback=dtClicked, bouncetime=1)
GPIO.add_event_detect(SW_PIN, GPIO.FALLING, callback=swToggle, bouncetime=1)

if __name__ == "__main__":
    print("turn the wheel")
    while (True):
        pass

GPIO.cleanup()
