

import os
import numpy as np
from imageio import imread, imwrite

import argparse

max_value = 255 
header_len = 4*8 

def read_image(img_path):
    
    img = np.array(imread(img_path), dtype=np.uint8)
    orig_shape = img.shape
    return img.flatten(), orig_shape

def write_image(img_path, img_data, shape):
   
    img_data = np.reshape(img_data, shape)
    imwrite(img_path, img_data)

def bytes2array(byte_data):
   
    byte_array = np.frombuffer(byte_data, dtype=np.uint8)
    return np.unpackbits(byte_array)

def array2bytes(bit_array):
    
    byte_array = np.packbits(bit_array)
    return byte_array.tobytes()

def read_file(file_path):
    
    file_bytes = open(file_path, "rb").read()
    return bytes2array(file_bytes)

def write_file(file_path, file_bit_array):
    
    bytes_data = array2bytes(file_bit_array)
    f = open(file_path, 'wb')
    f.write(bytes_data)
    f.close()

def encode_data(image, file_data):
    
    or_mask = file_data
    and_mask = np.zeros_like(or_mask)
    and_mask = (and_mask + max_value - 1) + or_mask 
    res = np.bitwise_or(image, or_mask)
    res = np.bitwise_and(res, and_mask)
    return res

def decode_data(encoded_data):
    
    out_mask = np.ones_like(encoded_data)
    output = np.bitwise_and(encoded_data, out_mask)
    return output

def _main(args):
    
    if args.image is not None and args.file is not None:
        if args.encode:
            img_path = args.image
            file_path = args.file
            if not os.path.isfile(img_path):
                print("Image file does not exist")
                return
            if not os.path.isfile(file_path):
                print("File does not exist")
                return

            output_path = args.output
            extension = os.path.splitext(output_path)[1][1:]
            if extension == '': 
                output_path = output_path + '.png'
            elif extension != 'png':  
                li = output_path.rsplit(extension, 1)
                output_path = 'png'.join(li)

            image, shape_orig = read_image(img_path)
            file = read_file(file_path)
            file_len = file.shape[0]
            len_array = np.array([file_len], dtype=np.uint32).view(np.uint8)
            len_array = np.unpackbits(len_array)
            img_len = image.shape[0]

            if file_len >= img_len - header_len:  
                print("File too big, error")
                return
            else:  
                tmp = file
                file = np.random.randint(2, size=img_len, dtype=np.uint8)
                file[header_len:header_len+file_len] = tmp
                # file = np.pad(file, (header_len,img_len - file_len - header_len), 'constant', constant_values=(0, 0))

            file[:header_len] = len_array
            encoded_data = encode_data(image, file)

            write_image(output_path, encoded_data, shape_orig)
            print("Image bien encodée!")
            return

        if args.decode:
            img_path = args.image
            if not os.path.isfile(img_path):
                print("Image file does not exist")
                return
            file_path = args.file
            encoded_data, shape_orig = read_image(img_path)
            data = decode_data(encoded_data)
            el_array = np.packbits(data[:header_len])
            extracted_len = el_array.view(np.uint32)[0]
            data = data[header_len:extracted_len+header_len]
            write_file(file_path, data)
            print("Image est decodée")
            return

        print("Error, no action specified!")
        return

    print("Error, image or file not specified")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='hide keylogger inside an image')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-e',
        '--encode',
        help='If present the script will conceal the file in the image and produce a new encoded image',
        action="store_true")
    group.add_argument(
        '-d',
        '--decode',
        help='If present the script will decode the concealed data in the image and produce a new file with this data',
        action="store_true")
    parser.add_argument(
        '-i',
        '--image',
        help='Path to an image to use for concealing or file extraction')
    parser.add_argument(
        '-f',
        '--file',
        help='Path to the file to conceal or to extract')
    parser.add_argument(
        '-o',
        '--output',
        help='Path where to save the encoded image. Specify only the file name, or use .png extension; png extension will be added automatically',
        default='encoded.png')

    _main(parser.parse_args())