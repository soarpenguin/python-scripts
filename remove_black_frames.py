import sys
from PIL import Image, ImageSequence

def is_black_frame(frame):
    # Convert the frame to grayscale
    grayscale_frame = frame.convert('L')

    # Check if all pixels in the grayscale frame are black (0)
    return all(pixel == 0 for pixel in grayscale_frame.getdata())

def remove_black_frames(input_path, output_path):
    # Open the GIF image
    with Image.open(input_path) as im:
        # Create a list to hold the modified frames
        modified_frames = []

        # Iterate over each frame in the GIF
        for frame in ImageSequence.Iterator(im):
            if not is_black_frame(frame):
                modified_frames.append(frame.copy())

        # Save the modified frames as a GIF
        modified_frames[0].save(output_path, save_all=True, append_images=modified_frames[1:], loop=0)

if __name__ == '__main__':
    # Check if the required command-line arguments are provided
    if len(sys.argv) != 3:
        print('Usage: python remove_black_frames.py <input_gif> <output_gif>')
        sys.exit(1)

    # Extract command-line arguments
    input_gif = sys.argv[1]
    output_gif = sys.argv[2]

    # Remove black frames and save the modified GIF
    remove_black_frames(input_gif, output_gif)

