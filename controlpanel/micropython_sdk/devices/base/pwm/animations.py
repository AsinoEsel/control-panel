from math import sin, pi

try:
    from micropython import const
except ImportError:
    def const(x): return x

MAX_DUTY = const(1023)
MS_IN_S = const(1000)


def sine(frequency: float, min_brightess: float = 0, max_brightness: float = 1):
    min_duty = int(min_brightess * MAX_DUTY)
    max_duty = int(max_brightness * MAX_DUTY)
    amplitude = (max_duty - min_duty) // 2
    mid_point = (max_duty + min_duty) // 2
    circle_frequency = frequency * 2 * pi

    def corrected_sine(t: int):
        val = int(mid_point + amplitude * sin(circle_frequency * t / MS_IN_S))
        return val

    return corrected_sine


def strobe(frequency: float, min_brightess: float = 0.0, max_brightess: float = 1.0):
    min_duty = int(min_brightess * MAX_DUTY)
    max_duty = int(max_brightess * MAX_DUTY)
    period_ms = 1000 / frequency

    def corrected_strobe(t: int):
        phase = t % period_ms
        val = max_duty if phase < period_ms / 2 else min_duty
        return val

    return corrected_strobe
