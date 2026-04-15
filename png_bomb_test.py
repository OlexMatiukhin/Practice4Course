

#Can be used as code with png
from PIL import Image
import os

def copy_and_paste_image(source_image_path, output_directory, num_copies):
    source_image = Image.open(source_image_path)
    os.makedirs(output_directory, exist_ok=True)
    for i in range(1, num_copies + 1):
        output_filename = f"copy_{i}.png"
        output_path = os.path.join(output_directory, output_filename)
        source_image.save(output_path)
        print(f"{i} files copied")

if __name__ == "__main__":
    source_image_path = input("Enter the image file path ending with .png : ")
    output_directory = input("Enter the path of the directory/folder you want to bomb this image file into : ")
    num_copies = int(input("Enter the number of copies you want to bomb : "))
    copy_and_paste_image(source_image_path, output_directory, num_copies)