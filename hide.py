from PIL import Image
import sys
from steganopy.api import create_stegano_image, extract_data_from_stegano_image

def main():
	
	process = sys.argv[1]

	if process == 'hide':

		image = sys.argv[2]
		data = sys.argv[3]

		if '.png' not in image:
			image = Image.open(image)
			image.save('input.png')
			image = 'input.png'

		stegano_image = create_stegano_image(
		    original_image=image,
		    data_to_hide=data,
		    cipher_key="JarrodCTaylor"
		)

		stegano_image.save("stegano_image.png")
	else:
		extracted_data = extract_data_from_stegano_image(
		    image="stegano_image.png",
		    cipher_key="JarrodCTaylor"
		)

		with open("decoded.txt", "w") as f:
		    f.write(extracted_data)


if __name__ == '__main__':
	main()