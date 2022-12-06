import math
import os
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

def create_screenshot(screen, angle, velocity, V):
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

    return screen

def setup_screenshots_dir():
    if not os.path.exists("screenshots"):
        os.mkdir("screenshots")

counter = 0

while True:
    setup_screenshots_dir()

    start = time.time_ns()

    V = 0.1

    # compute additional speed for no more than 250ms
    while time.time_ns() - start < 250000000:
        mscreen = pyautogui.screenshot().crop(crop)
        bg = mscreen.getpixel(bgcords)

        lt = mscreen.getpixel(ltcords)

        left = mscreen.getpixel(leftcords)
        middle = mscreen.getpixel(middlecords)
        right = mscreen.getpixel(rightcords)

        # color of the indicator pixel is same as background
        if color_diff(left, bg) < 1000:
            continue

        # arrow points at the left
        if color_diff(lt, bg) < 1000:
            V = -3.3

            # if middle and right are the same color . < <
            if color_diff(right, middle) < 1000:
                V -= 1.6

            # if left, middle and right are the same color < < <
            if color_diff(middle, left) < 1000 and color_diff(right, middle) < 1000:
                V -= 4

        # arrow points at the right
        else:
            V = 4.5

            # if middle and left are the same color > > .
            if color_diff(left, middle) < 1000:
                V += 2.9

            # if left, middle and right are the same color > > >
            if color_diff(middle, right) < 1000 and color_diff(left, middle) < 1000:
                V += 4.3

    # sleep for 0.5 - time spent
    time.sleep(0.5 - (time.time_ns() - start) / 1000000000)

    screen = pyautogui.screenshot()

    screen = screen.crop(crop)

    # locate the marker on the screen
    result = pyscreeze.locate(ring, screen)

    if result is None:
        continue

    # found marker cords
    left, top  = result[0], result[1]

    detector_center_y = top + ring_height // 2

    color = screen.getpixel((left + ring_width, detector_center_y))

    left_bound, right_bound = left + ring_width, left + ring_width
    top_bound, bottom_bound = top + ring_height, top + ring_height

    # move by one pixel at a time to find the first pixel to differ
    # repeat for all 4 directions to find shield bounds

    while color_diff(color, screen.getpixel((left_bound, detector_center_y))) <= 10000:
        left_bound -= 1

    while color_diff(color, screen.getpixel((right_bound, detector_center_y))) <= 10000:
        right_bound += 1

    detector_right_x = left + ring_width

    while color_diff(color, screen.getpixel((detector_right_x, top_bound))) <= 10000:
        top_bound -= 1

    while color_diff(color, screen.getpixel((detector_right_x, bottom_bound))) <= 10000:
        bottom_bound += 1

    shield_bounds = (top_bound, right_bound, bottom_bound, left_bound)

    # find ring cords as middle on x-axis i.e. (right_bound + left_bound) // 2
    # y cord is located at 0.787 of the distance between bottom_bound and top_bound + bottom_bound i.e.
    # bottom_bound + (top_bound - bottom_bound) * 0.787
    ring_cords = ((right_bound + left_bound) // 2, int(bottom_bound * 0.787 + top_bound * 0.213))

    angle = 9
    best = None

    # vertical distance between the center of the ball and the ring
    H = ball_center[1] - ring_cords[1]

    # horizontal distance between the center of the ball and the ring
    S = ring_cords[0] - ball_center[0]

    # iterate over angles from 10 to 90
    while angle < 90:
        angle += 1

        # compute cos, sin and sin2 functions results needed later
        sin, cos = math.sin(math.radians(angle)), math.cos(math.radians(angle))
        sin2 = math.sin(math.radians(angle * 2))

        rhs = (sin ** 2) * (V ** 2) + sin2 * S * g - 2 * H * (cos ** 2) * g

        if rhs < 0:
            continue

        velocity = (-sin * S * V + 2 * H * cos * V + S * math.sqrt(rhs)) / (sin2 * S - 2 * H * (cos ** 2))

        if velocity <= 0:
            continue

        # total flight time
        flight_time = S / (velocity * cos + V)

        # flight time until peak height
        time_up = velocity * sin / g

        #peak height
        hmax = (velocity ** 2) * (sin ** 2) / (2 * g)

        # horizontal distance to ring_enter
        s_ring_enter = S - ring_from_center

        # vertical distance to ring_enter
        h_ring_enter = (velocity * sin * s_ring_enter) / (velocity * cos + V) - (g * (s_ring_enter ** 2)) / (2 * ((velocity * cos + V) ** 2))

        # vertical distance must be greater than half ball height
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

    # y cord at the peak
    high_y = height - (best[1] ** 2) * (math.sin(math.radians(best[0])) ** 2) / (2 * g) + crop[1]

    # x cord at the peak
    high_x = best[3] * best[1] * math.cos(math.radians(best[0])) + ball_center[0] + crop[0]

    create_screenshot(screen, best[0], best[1], V).save(f"screenshots/screenshot_{counter}.png")

    counter += 1

    pyautogui.click((high_x, high_y - K))
