import shutil
import os

# function deletes a given directory
def delete_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

# function saves an image to given directory
def save_image(image, dir, file_name):
	# if not os.path.exists(dir):
	# 	os.makedirs(dir)
	# image.save(os.path.join(dir, file_name))
	pass

def save_final_image(image, file_name):
	image.save(file_name)