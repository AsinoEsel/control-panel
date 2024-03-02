from pyky040 import pyky040

# Define your callback
def callback(scale_position):
    print(scale_position)

# Init the encoder pins
my_encoder = pyky040.Encoder(CLK=17, DT=18, SW=27)

# Or the encoder as a device (must be installed on the system beforehand!)
# my_encoder = pyky040.Encoder(device='/dev/input/event0')

# Setup the options and callbacks (see documentation)
my_encoder.setup(scale_min=-100, scale_max=100, step=1, chg_callback=callback)

# Launch the listener
my_encoder.watch()
