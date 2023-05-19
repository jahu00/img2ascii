from math import floor
from PIL import Image
import numpy
from settings import *

src_file_name = get_str_setting("src")
dst_file_name = get_str_setting("dst")

src_data = numpy.fromfile(src_file_name, dtype = "uint8")
src_bits = numpy.unpackbits(src_data)
bit_count = src_bits.shape[0]

character_width = 8
character_height = 8
character_pixel_count = character_width * character_height
characters_per_row = 16
pixels_per_row = character_pixel_count * characters_per_row

width = characters_per_row * character_width
height = floor(bit_count / width)

pixel_count = width * height

dst_image = Image.new("L", (width, height))

pixels = [0 if bit == 0 else 255 for bit in src_bits]
pixels = pixels[bit_count - pixel_count:]

ordered_pixels = []

for i in range(len(pixels)):
    y = floor(i / width) % character_height
    col = floor(i / character_width) % characters_per_row
    row = floor(i / pixels_per_row)
    #y = floor(i / character_width) % character_height
    #x = i 
    offset = col * character_pixel_count + y * character_height + row * pixels_per_row
    ordered_pixels.append(pixels[offset + i % character_width])

dst_image.putdata(ordered_pixels)
dst_image.save(dst_file_name)
