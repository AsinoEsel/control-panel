import asyncio
from controlpanel.upy.artnet import ArtNet, OpCode
from micropython import const
from machine import Pin, SoftSPI, freq, reset

from controlpanel.upy.phys.shift_register import PisoShiftRegister
from controlpanel.upy.phys.led_strip import LEDStrip

freq(240000000)


def artnet_callback(op_code: OpCode, ip: str, port: int, reply):
    if op_code == OpCode.ArtCommand:
        command = reply.get("Command")
        if command == "RESET":
            reset()
        if command == "MATRIX-LOCALMODE":
            keyboard_led_strip.set_animation(0) # hi
        if command == "MATRIX-NETWORKMODE":
            ...
        print(command)
    elif op_code == OpCode.ArtDmx:
        print(f"Received DMX at universe {reply.get("Universe")}...")
        universe = reply.get("Universe")
        data = reply.get("Data")
        device = universe_dict.get(universe)
        if device is None:
            return
        print(f"Parsing dmx data {data} for device {device.name}")
        device.parse_dmx_data(data)


async def start_main_loop():
    await main_loop()


async def main_loop():
    ups = 30
    asyncio.create_task(keyboard_piso_module.run(updates_per_second=ups))
    asyncio.create_task(keyboard_led_strip.run(updates_per_second=ups))

    while True:
        await asyncio.sleep_ms(1000)

artnet = ArtNet()

NUM_MODULE_ROWS = const(3)
NUM_MODULE_COLS = const(5)
NUM_KEYBOARD_MODULES = NUM_MODULE_COLS * NUM_MODULE_ROWS
NUM_SHIFT_REGISTERS = const(NUM_KEYBOARD_MODULES * 2)

PISO_CLOCK_PIN = const(15)  # 33  # 18
PISO_LATCH_PIN = const(4)  # 4
PISO_SERIALIN_PIN = const(17)  # 15
KEYBOARD_LED_PIN = const(16)

keyboard_piso_module = PisoShiftRegister(artnet, "MainframeKeys", PISO_CLOCK_PIN, PISO_LATCH_PIN, PISO_SERIALIN_PIN, NUM_SHIFT_REGISTERS)
keyboard_led_strip = LEDStrip(artnet, "MainframeLEDs", KEYBOARD_LED_PIN, 16 * NUM_KEYBOARD_MODULES)

universe_dict = {
                 keyboard_led_strip.universe: keyboard_led_strip,
                 }

artnet.subscribe_all(artnet_callback)

asyncio.run(start_main_loop())


print("whoops, end of main.py")

######################## ----------------------------------------------------------------------------

# class Conway():
#
#     def __init__(self):
#         self.running = True
#
#         self.height = NUM_MODULE_ROWS * 16
#         self.width = NUM_MODULE_COLS * 16
#
#         self.states = [[False for x in range(0, self.width)] for y in range(0, self.height)]
#
#         self.WHITE = (255, 255, 255)
#         self.RED = (255, 0, 0)
#         self.GREEN = (0, 255, 0)
#         self.DARK_GREEN = (0, 100, 0)
#         self.BLUE = (0, 0, 255)
#         self.GREY = (50, 50, 50)
#
#
#     def sum_alive_neighbours(self, x, y):
#         return sum([
#             # row above
#             self.states[(x - 1) % self.width][(y - 1) % self.height],  # left
#             self.states[(  x  ) % self.width][(y - 1) % self.height],  # mid
#             self.states[(x + 1) % self.width][(y - 1) % self.height],  # right
#
#             # same row
#             self.states[(x - 1) % self.width][(  y  ) % self.height],  # left
#                                                                       # skip self
#             self.states[(x + 1) % self.width][(  y  ) % self.height],  # right
#
#             # row below
#             self.states[(x - 1) % self.width][(y + 1) % self.height],  # left
#             self.states[(  x  ) % self.width][(y + 1) % self.height],  # mid
#             self.states[(x + 1) % self.width][(y + 1) % self.height],  # right
#         ])
#
#     def step(self):
#         future_states = [[False for x in range(0, self.width)] for y in range(0, self.height)]
#         for x in range(self.width):
#             for y in range(self.height):
#                 n = self.sum_alive_neighbours(x, y)
#                 if 2 <= n < 4:
#                     future_states[x][y] = self.states[x][y]
#                 else:
#                     future_states[x][y] = False
#                 if n == 3:
#                     future_states[x][y] = True
#
#         self.states = future_states
#
#     def process_inputs(self, event: Event):
#         ...
#
#     def draw(self):
#         for x in range(self.width):
#             for y in range(self.height)
#                 ...
#         ...
#
#     def run(self):
#         self.running = True
#         while self.running:
#             self.process_inputs()
#             self.step()
#             self.draw()
#
# while running:
#
#     tick += 1
#
#     for event in pygame.event.get():
#         if event.type == pygame.MOUSEBUTTONDOWN:
#             (x, y) = pygame.mouse.get_pos()
#             x //= SCALING
#             y //= SCALING
#             # if not auto_progression:
#             buttons[x][y].toggle()
#             # else:
#             print(f"Mouse at {x}, {y}")
#
#         if event.type == pygame.KEYDOWN:
#             keys = pygame.key.get_pressed()
#             if event.key == pygame.K_SPACE:
#                 if event.mod & (pygame.KMOD_LSHIFT or pygame.KMOD_RSHIFT):
#                     auto_progression = not auto_progression
#                     print(f"Toggled auto progression, now {auto_progression}")
#                 else:
#                     auto_progression = False
#                     conway()
#             if event.key == pygame.K_RETURN:
#                 if event.mod & (pygame.KMOD_LSHIFT or pygame.KMOD_RSHIFT):
#                     buttons[random.randrange(SCREEN_WIDTH)][random.randrange(SCREEN_HEIGHT)].state = True
#                 else:
#                     for x in range(SCREEN_WIDTH):
#                         for y in range(SCREEN_HEIGHT):
#                             buttons[x][y].state = random.randrange(100) > 75
#             if event.key == pygame.K_ESCAPE:
#                 for x in range(SCREEN_WIDTH):
#                     for y in range(SCREEN_HEIGHT):
#                         buttons[x][y].state = False
#                         buttons[x][y].accumulation = 0
#
#             if event.key == pygame.K_n:
#                 distribute_nutrients = not distribute_nutrients
#
#         if event.type == pygame.QUIT:
#             running = False
#
#     if auto_progression and tick % 10 == 0:
#         conway()
#
#     nutrient_rate = .01
#
#     if distribute_nutrients and auto_progression:
#         for i in range(10):
#             buttons[random.randrange(SCREEN_WIDTH)][random.randrange(SCREEN_HEIGHT)].accumulation += nutrient_rate
#         for x in range(SCREEN_WIDTH):
#             for y in range(SCREEN_HEIGHT):
#                 if buttons[x][y].accumulation >= 1:
#                     buttons[x][y].state = True
#                     buttons[x][y].accumulation = 0
#
#     # Draw button states and
#     for x in range(SCREEN_WIDTH):
#         for y in range(SCREEN_HEIGHT):
#             pygame.draw.rect(screen, buttons[x][y].get_color(), pygame.Rect(x * SCALING, y * SCALING, SCALING, SCALING))
#             pygame.draw.rect(screen, GREY, pygame.Rect(x * SCALING, y * SCALING, SCALING, SCALING), 1)
#
#     pygame.display.flip()
#
#     clock.tick(60)
#
# pygame.quit()