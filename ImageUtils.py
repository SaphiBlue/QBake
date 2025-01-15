import bpy
import numpy

#https://blender.stackexchange.com/questions/274712/how-to-channel-pack-texture-in-python

def pack_image_channels(pack_order):
    dst_array = None
    has_alpha = False
    colorspace = 'Non-Color'
    alphamode = 'STRAIGHT'
    # Build the packed pixel array
    for pack_item in pack_order:
        image = pack_item[0]
        alphamode = image.alpha_mode
        colorspace = image.colorspace_settings.name
        
        # Initialize arrays on the first iteration
        if dst_array is None:
            w, h = image.size
            src_array = numpy.empty(w * h * 4, dtype=numpy.float32)
            dst_array = numpy.ones(w * h * 4, dtype=numpy.float32)

        assert image.size[:] == (w, h), "Images must be same size"

        # Fetch pixels from the source image and copy channels
        image.pixels.foreach_get(src_array)
        for src_chan, dst_chan in pack_item[1:]:
            if dst_chan == 3:
                has_alpha = True
            dst_array[dst_chan::4] = src_array[src_chan::4]

    # Create image from the packed pixels
    dst_image = bpy.data.images.new("Packed Image", w, h, alpha=has_alpha)
    
    dst_image.colorspace_settings.name = colorspace;
    dst_image.alpha_mode = alphamode;
    dst_image.pixels.foreach_set(dst_array)

    # Since the image doesn't exist on disk, we need to pack it into the .blend
    # or it won't exist after the .blend is closed
    dst_image.pack()

    return dst_image


# Pack four monochrome images into RGBA
def channel_pack(r: bpy.types.Image, g: bpy.types.Image, b: bpy.types.Image, a: bpy.types.Image):
    pack_order = [
        (r, (0, 0)),
        (g, (0, 1)),
        (b, (0, 2)),
        (a, (0, 3)),
    ]
    return pack_image_channels(pack_order)

# Pack the RGB of one an image into the RGB of the output, with a
# monochrome image packed into the alpha.
def alpha_pack(rgb: bpy.types.Image, a: bpy.types.Image):
    pack_order = [
        (rgb, (0, 0), (1, 1), (2, 2)),
        (a, (0, 3)),
    ]
    return pack_image_channels(pack_order)