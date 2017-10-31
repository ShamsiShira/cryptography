from PIL import Image
import random
from operator import xor
import numpy
import sys
import filesUtil
import glob
import os
import binascii
import optparse
import base64

QUADRANTS_FOLDER = 'quadrants'
SHARES_DIR = 'shares'
OUT_DIR = 'combined'

quad_im1 = ['quad1', 'quad5', 'quad6', 'quad7']
quad_images = ['quad1', 'quad2', 'quad3', 'quad4']

def generate_share(image, text):

	try:
		prep = image.split('/')[1].split('.')[0]
	except Exception, e:
		prep = ''
	

	# open the image in gray scale mode
	image = Image.open(image).convert('L')
	# get its width and height
	width, height = image.size
	
	# get the pixal array of input image
	pix = image.load()

	# convert it to binary image with pixal value = 255 if value > 120 else 0
	for i in range(width):
		for j in range(height):
			if pix[i, j] < 120:
				pix[i, j] = 0
			else:
				pix[i, j] = 255


	# create new plain white image for share 1
	share1 = Image.new("1", (width, height), "white")
	share1pix = share1.load()

	# randomly allocate black pixals in share 1 image
	for i in range(width):
		for j in range(height):
			x = random.randint(0,1)
			if x == 0:
				share1pix[i, j] = 0

	# create new plain image for share 2
	share2 = Image.new("1", (width, height))
	share2pix = share2.load()

	# xor share 1 image with original to produce share 2
	for i in range(width):
		for j in range(height):	
			share2pix[i, j] = xor(share1pix[i, j], pix[i, j])

	share1 = hide(share1, text)
	share2 = hide(share2, text)

	# save both shares in shares directory
	filesUtil.save_final_image(share1, prep + 'share1.jpg')
	filesUtil.save_final_image(share2, prep + 'share2.jpg')


def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b'='* (4 - missing_padding)
    return base64.decodestring(data)


def combine_shares(share1, share2, file_name, dec_file='dec.jpg'):

	content = retr(share1)
	fh = open(dec_file, "wb")
	# content = decode_base64(content)
	fh.write(content.decode('base64'))
	fh.close()
	# open both shares directory
	share1 = Image.open(share1).convert('L')
	share2 = Image.open(share2).convert('L')

	# get its corresponding pixel array
	share1pix = share1.load()
	share2pix = share2.load()

	width, height = share1.size

	# create new plain image for shares combined image
	out = Image.new("1", (width, height))
	outPix = out.load()

	# xor both shares to produce original image
	for i in range(width):
		for j in range(height):
			outPix[i, j] = xor(share1pix[i, j], share2pix[i, j])

	# save the image to combined directory
	# filesUtil.save_image(out, OUT_DIR, file_name)
	filesUtil.save_final_image(out, file_name)


def divide_vertical(image):
	width, height = image.size
	
	# crop it into 2 halfs horizontally
	top = image.crop((0, 0, width, height / 2))
	bottom = image.crop((0, height / 2, width, height))
	return top, bottom


def divide_horizontal(image):
	width, height = image.size

	left = image.crop((0, 0, width / 2, height))
	right = image.crop((width / 2, 0, width, height))

	return left, right 

def quadralize_image(image, quad_ims):
	
	top, bottom = divide_vertical(image)

	# crop the top piece into 2 halfs
	quad1, quad2 = divide_horizontal(top)

	# crop the bottom piece into 2 halfs
	quad3, quad4 = divide_horizontal(bottom)

	quad_files = [quad1, quad2, quad3, quad4]

	# save all pieces to quadrants directory
	for f, im in zip(quad_files, quad_ims):
		filesUtil.save_image(f, QUADRANTS_FOLDER, im + '.jpg')
	return quad1
	

def decode_shares(quad_ims, out_file, is_final):
	# combine each 2 share to generate decoded image
	for quad in quad_ims[1:] if is_final else quad_ims:
		files = glob.glob(SHARES_DIR + '/' + quad + '*')
		combine_shares(files[0], files[1], quad + '.jpg')
	if files:
		share = Image.open(files[0])
		width, height = share.size

		# create new image with twice share image size
		out = Image.new("1", (width * 2, height * 2))

		# create a list of quadrants images path
		quads = map(lambda x: os.path.join(OUT_DIR, x + '.jpg'), quad_ims)

		# combine each slice to generate final image
		for i in range(2):
			for j in range(2):
				image = quads[(i * 2) + j]
				image = Image.open(image)
				out.paste(image, ((j * width), (i * height)))

		# save the final image
		out.save(out_file)


def divide_final_image(image):
	image = Image.open(image)

	# divide the final quadrant into two halfs
	top, bottom = divide_vertical(image)

	filesUtil.save_final_image(top, 'top.jpg')
	filesUtil.save_final_image(bottom, 'bottom.jpg')





# --------------   HIDE   -------------------



def rgb2hex(r, g, b):
	return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex2rgb(hexcode):
	return tuple(map(ord, hexcode[1:].decode('hex')))

def str2bin(message):
	binary = bin(int(binascii.hexlify(message), 16))
	return binary[2:]

def bin2str(binary):
	message = binascii.unhexlify('%x' % (int('0b'+binary,2)))
	return message

def encode(hexcode, digit):
	if hexcode[-1] in ('0','1', '2', '3', '4', '5'):
		hexcode = hexcode[:-1] + digit
		return hexcode
	else:
		return None

def decode(hexcode):
	if hexcode[-1] in ('0', '1'):
		return hexcode[-1]
	else:
		return None

def hide(img, message):
	binary = str2bin(message) + '1111111111111110'

	if img.mode not in ('RGBA'):
		rgbimg = Image.new("RGBA", img.size)
		rgbimg.paste(img)
		img = rgbimg

	if img.mode in ('RGBA'):
		img = img.convert('RGBA')
		datas = img.getdata()
		
		newData = []
		digit = 0
		temp = ''
		for item in datas:
			if (digit < len(binary)):
				newpix = encode(rgb2hex(item[0],item[1],item[2]),binary[digit])
				if newpix == None:
					newData.append(item)
				else:
					r, g, b = hex2rgb(newpix)
					newData.append((r,g,b,255))
					digit += 1
			else:
				newData.append(item)	
		img.putdata(newData)
		
		return img
			
	return "Incorrect Image Mode, Couldn't Hide"

						
				

def retr(filename):
	img = Image.open(filename)
	binary = ''
	
	if img.mode in ('RGBA'): 
		img = img.convert('RGBA')
		datas = img.getdata()
		
		for item in datas:
			digit = decode(rgb2hex(item[0],item[1],item[2]))
			if digit == None:
				pass
			else:
				binary = binary + digit
				if (binary[-16:] == '1111111111111110'):
					print "Success"
					return bin2str(binary[:-16])

		return bin2str(binary)
	return "Incorrect Image Mode, Couldn't Retrieve"



	


# ------------- MAIN -------------


def main():
	# run only if we provided arguments
	if len(sys.argv) > 2:
		operation = sys.argv[1]
		
		# encode operation
		if operation == 'encode':
			# get image attribute
			image = sys.argv[2]
			text_image = sys.argv[3]
			
			# clear quadrants folder
			filesUtil.delete_dir(QUADRANTS_FOLDER)

			# open the image to slice into 4 quadrants
			image = Image.open(image)
			
			# divide the image into 4 quadrants
			quad1 = quadralize_image(image, quad_im1)
			# get the first quadrant image
			# quad1_image = os.path.join(QUADRANTS_FOLDER, quad_im1[0] + '.jpg')
			
			# divide the first quadrant image into 4 quadrant again
			quad1 = quadralize_image(quad1, quad_images)

			# divide the first quadrant image into 4 quadrant again
			quad1 = quadralize_image(quad1, quad_images)
			
			f = 'final_quadrant.jpg'
			filesUtil.save_final_image(quad1, f)


			w, h = quad1.size
			opt = raw_input("Select Option\n 1. Hide image\n 2. Hide text\n")
			if opt == '1':
				im = Image.open(text_image)
				imw, imh = im.size
				if w < imw or h < imh:
					scale = 0.5
					size = (w * scale), (h * scale)
					im.thumbnail(size, Image.ANTIALIAS)
					text_image = 'scaled.jpg'
					filesUtil.save_final_image(im, text_image)
					

			print(text_image)
			with open(text_image, "rb") as imageFile:
				content = base64.b64encode(imageFile.read())
				generate_share(f, content)
			# divide_final_image(quad1_image)

			# generate shares for each quadrant
			# for f in glob.glob(QUADRANTS_FOLDER + '/*.jpg'):
			# 	generate_share(f)

		# decode operation
		else:
			# clear shares combined directory
			# filesUtil.delete_dir(OUT_DIR)
			# # while combining first 4 quadrants output file is quadrant1
			# out_file = os.path.join(OUT_DIR, quad_images[0] + '.jpg')
			# # decode first quadrant image
			# decode_shares(quad_images, out_file, False)
			# # decode final image
			# decode_shares(quad_im1, 'out.jpg', True)

			opt = raw_input("Select Option\n 1. Extract image\n 2. Extract text\n")
			if opt == '1':
				dec_file = 'HiddenImage.jpg'
			else:
				dec_file = 'HiddenText.txt'
			combine_shares('share1.jpg', 'share2.jpg', 'combined.jpg', dec_file)
		
	else:
		print('please provide image to process')




if __name__ == '__main__':
	main()