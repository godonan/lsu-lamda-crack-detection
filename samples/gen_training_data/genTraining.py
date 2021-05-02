"""
    Generates training dataset from paint-brushed dataset

    python3 genTraining.py --dataset=/path/to/dataset

    Expected Filesystem Structure:
    dataset <- Location as the optional --dataset argument
     ├── Annotations
     │ ├── 0
     │ │   ├── category1.jpg
     │ │   └── category2.jpg
     │ ├── ...
     │ └── 9
     │     ├── category1.jpg
     │     ├── category2.jpg
     │     └── category3.jpg
     └── Images
       ├── 0.jpg
       ├── ...
       └── 9.jpg

    If you do not pass the --dataset argument, the program will use the filesystem
    structure located at \dataset
"""
import glob
import os
import cv2
from pathlib import Path
import sys
import json
import argparse

ROOT_DIR = str(Path(__file__).resolve().parents[2])
print("ROOT DIR={}".format(ROOT_DIR))

sys.path.append(ROOT_DIR)
RESOURCE_DIR = os.path.join(ROOT_DIR, 'resources', 'img')

from gen_annotation import segcolor


def make_image_annotation(img, file_name, image_id, bbox):
    width, height = img.size
    image_annotation = {
        "file_name": file_name,
        "width": width,
        "height": height,
        "id": image_id
    }
    return image_annotation


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build JSON file.')
    parser.add_argument('-o', "--original", help="Directory of original images", required=True)
    parser.add_argument('-m', "--marked", help="Directory of marked images", required=True)
    argument = parser.parse_args()

    categories = []
    category_ids = {}

    original_dir = argument.original
    marked_dir = argument.marked

    subdirectories = glob.glob(os.path.join(marked_dir, "*", ""))
    anno_paths = {}
    category_id = 1
    folder_paths = {}
    for subdir in subdirectories:
        name = os.path.basename(os.path.normpath(subdir))
        category = {
            "supercategory": "material defect",
            "id": category_id,
            "name": name
        }
        category_ids[name] = category_id
        categories.append(category)
        marked_paths = glob.glob(subdir + '/*.tif')
        folder_paths[name] = marked_paths
        category_id += 1
    original_paths = glob.glob(original_dir + '/*.tif')

    images = []
    annotations = []

    image_id = 0
    last_id = 0
    for orig_file in original_paths:
        print("Analyzing Image {}".format(image_id))
        orig_filename = os.path.basename(orig_file)
        # Computes the image annotation
        orig_img = cv2.imread(orig_file)
        image = {
            "id": image_id,
            "width": orig_img.shape[0],
            "height": orig_img.shape[1],
            "file_name": orig_filename
        }
        images.append(image)
        for category in folder_paths:
            for marked_file in folder_paths[category]:
                marked_filename = os.path.basename(marked_file)
                if marked_filename != orig_filename:
                    continue
                print("Analyzing Category {}".format(category))
                mark_img = cv2.imread(marked_file)

                mask = segcolor.get_colors(mark_img)
                masks_categorized = segcolor.get_mask_categorized(mask)

                for color, submask in masks_categorized.items():
                    category_id = category_ids[category]
                    last_id, annotation = segcolor.make_submask_annotations(
                        submask,
                        image_id,
                        category_id,
                        last_id
                    )
                    annotations.extend(annotation)
                break
        image_id += 1

    coco = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    json_out = os.path.join(marked_dir, "annotations.json")
    with open(json_out, 'w') as outfile:
        json.dump(coco, outfile)
