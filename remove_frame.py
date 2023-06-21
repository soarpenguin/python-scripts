import sys
import re
from PIL import Image, ImageSequence

def parse_frame_indices(frames):
    parsed_indices = []
    for frame in frames.split(','):
        match = re.match(r'^(\d+)-(\d+)$', frame)
        if match:
            start, end = map(int, match.groups())
            parsed_indices.extend(range(start, end + 1))
        else:
            parsed_indices.append(int(frame))
    return parsed_indices

def remove_frames(input_path, output_path, frames_to_remove):
    # Open the GIF image
    with Image.open(input_path) as im:
        # Create a list to hold the modified frames
        modified_frames = []

        # Iterate over each frame in the GIF
        for index, frame in enumerate(ImageSequence.Iterator(im)):
            # Check if the current frame index is in the frames_to_remove list
            if index not in frames_to_remove:
                modified_frames.append(frame.copy())

        # Save the modified frames as a GIF
        modified_frames[0].save(output_path, save_all=True, append_images=modified_frames[1:], loop=0)

if __name__ == '__main__':
    # Check if the required command-line arguments are provided
    if len(sys.argv) != 4:
        print('Usage: python remove_frames.py <input_gif> <output_gif> <frames_to_remove>')
        sys.exit(1)

    # Extract command-line arguments
    input_gif = sys.argv[1]
    output_gif = sys.argv[2]
    frames_to_remove = parse_frame_indices(sys.argv[3])

    # Remove frames and save the modified GIF
    remove_frames(input_gif, output_gif, frames_to_remove)

