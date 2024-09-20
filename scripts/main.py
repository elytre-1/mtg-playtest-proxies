# Import required methods
from requests import get
from json import loads
from shutil import copyfileobj
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import numpy as np
import cv2
import textwrap
from matplotlib import font_manager
import func

# TODO handle double-side cards

if __name__ == '__main__':
    # Get for your deck
    list_of_cards, number_of_copies = func.getListOfCards(path='../user/card_list.txt')

    # Create a .png for every card
    for copies, card_name in zip(number_of_copies, list_of_cards):
        print('    Creating '+ card_name +'... ')
        
        # Load data
        card_data = func.minimalCardData(card_name)

        if not card_data.corrupted:
            # Adapt the original image
            brightened_image = func.brightenCardImage(card_data.image)

            # Draw and save the card
            func.drawCard(brightened_image, card_data)

    # Create pages to print
    func.A4layout(list_of_cards)

    # TODO A function for altered proxies