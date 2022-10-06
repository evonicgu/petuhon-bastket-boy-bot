import math
import time

from PIL import Image, ImageDraw
import pyautogui
import pyscreeze

pyautogui.hotkey("alt", "tab")

crop = (536, 174, 1418, 1056)
ball_center = (127, 655)
ball_half_height = 23

g = 10
K = 90
ring_from_center = 30

bgcords, ltcords, leftcords, middlecords, rightcords = (55, 195), (65, 188), (70, 195), (92, 195), (115, 195)

ring = Image.open("detector.png")

ring_width, ring_height = ring.size

def color_diff(first, second):
    return abs(color_rel_diff(first, second))

def color_rel_diff(first, second):
    return first[0] * 256 + first[1] * 16 + first[2] - second[0] * 256 - second[1] * 16 - second[2]


def save_screenshot(screen, angle, velocity, V):
    draw = ImageDraw.Draw(screen)

    draw.line((ball_center[0], 0, ball_center[0], ball_center[1]), fill="#ffffff")
    draw.line((ball_center[0], ball_center[1], crop[2] - crop[0], ball_center[1]), fill="#ffffff")

    sin, cos = math.sin(math.radians(angle)), math.cos(math.radians(angle))

    for i in range(0, crop[2] - crop[0] - ball_center[0]):
        height = (sin * i) / cos - (g * (i ** 2)) / (2 * (velocity ** 2) * (cos ** 2))

        draw.point((ball_center[0] + i, ball_center[1] - height), fill="#00ff00")

        pass

    for i in range(0, crop[2] - crop[0] - ball_center[0]):
        height = (velocity * sin * i) / (velocity * cos + V) - (g * (i ** 2)) / (2 * ((velocity * cos + V) ** 2))

        draw.point((ball_center[0] + i, ball_center[1] - height), fill="#ffffff")

        pass

    screen.save("screenshot.png")


while True:
    start = time.time_ns()

    V = 0

    while time.time_ns() - start < 500000000:
        mscreen = pyautogui.screenshot().crop(crop)
        bg = mscreen.getpixel(bgcords)

        lt = mscreen.getpixel(ltcords)

        left = mscreen.getpixel(leftcords)
        middle = mscreen.getpixel(middlecords)
        right = mscreen.getpixel(rightcords)

        if color_diff(left, bg) < 1000:
            continue

        if color_diff(lt, bg) < 1000:
            V = -3.5

            if color_diff(right, middle) < 1000:
                V -= 1.4

            if color_diff(middle, left) < 1000 and color_diff(right, middle) < 1000:
                V -= 4

            pass
        else:
            V = 4.5

            if color_diff(left, middle) < 1000:
                V += 2.9

            if color_diff(middle, right) < 1000 and color_diff(left, middle) < 1000:
                V += 4.3

            pass

    time.sleep(1 - (time.time_ns() - start) / 1000000000)

    screen = pyautogui.screenshot()

    screen = screen.crop(crop)

    result = pyscreeze.locate(ring, screen)

    if result is None:
        continue

    left, top  = result[0], result[1]

    detector = top + ring_height // 2

    color = screen.getpixel((left + ring_width, detector))

    left_bound, right_bound = left + ring_width, left + ring_width
    top_bound, bottom_bound = top + ring_height, top + ring_height

    while color_diff(color, screen.getpixel((left_bound, detector))) <= 10000:
        left_bound -= 1

    while color_diff(color, screen.getpixel((right_bound, detector))) <= 10000:
        right_bound += 1

    detector_xmax = left + ring_width

    while color_diff(color, screen.getpixel((detector_xmax, top_bound))) <= 10000:
        top_bound -= 1

    while color_diff(color, screen.getpixel((detector_xmax, bottom_bound))) <= 10000:
        bottom_bound += 1

    shield_bounds = (top_bound, right_bound, bottom_bound, left_bound)

    ring_cords = ((right_bound + left_bound) // 2, int(bottom_bound * 0.787 + top_bound * 0.213))

    angle = 9
    best = None

    H = ball_center[1] - ring_cords[1]
    S = ring_cords[0] - ball_center[0]

    while angle < 90:
        angle += 1
        sin, cos = math.sin(math.radians(angle)), math.cos(math.radians(angle))
        sin2 = math.sin(math.radians(angle * 2))

        rhs = (sin ** 2) * (V ** 2) + sin2 * S * g - 2 * H * (cos ** 2) * g

        if rhs < 0:
            continue

        velocity = (-sin * S * V + 2 * H * cos * V + S * math.sqrt(rhs)) / (sin2 * S - 2 * H * (cos ** 2))

        if velocity <= 0:
            continue

        flight_time = S / (velocity * cos + V)

        time_up = velocity * sin / g
        hmax = (velocity ** 2) * (sin ** 2) / (2 * g)

        s_ring_enter = S - ring_from_center
        h_ring_enter = (velocity * sin * s_ring_enter) / (velocity * cos + V) - (g * (s_ring_enter ** 2)) / (2 * ((velocity * cos + V) ** 2))

        if h_ring_enter - H <= ball_half_height:
            continue

        if flight_time < time_up:
            continue

        if hmax - H <= ball_half_height * 2:
            continue

        if best is None or best[2] > flight_time:
            best = (angle, velocity, flight_time, time_up)

    if best is None:
        exit(1)

    print(best, V)

    width, height = screen.size

    high_y = height - (best[1] ** 2) * (math.sin(math.radians(best[0])) ** 2) / (2 * g) + crop[1]
    high_x = best[3] * best[1] * math.cos(math.radians(best[0])) + ball_center[0] + crop[0]

    save_screenshot(screen, best[0], best[1], V)

    pyautogui.click((high_x, high_y - K))
