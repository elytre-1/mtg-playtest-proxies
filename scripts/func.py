from requests import get
from json import loads
from shutil import copyfileobj
import cv2
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import numpy as np
import textwrap
import re
from PyPDF2 import PdfMerger
import os

class minimalCardData():
    def __init__(self, card_to_search, **kwargs) -> None:
        '''
        INPUT:
            (str) card_name: full name of the card
        '''
        path = kwargs.get('path', '../assets/download/')

        # Load the card data from Scryfall
        card = loads(get(f"https://api.scryfall.com/cards/search?q={card_to_search}").text)
        self.name = card['data'][0]['name']

        # TODO check if there are weird characters in the name (typically accents)

        try:
            self.oracle_text = card['data'][0]['oracle_text']
            self.type_line = card['data'][0]['type_line']
            self.mana_cost = card['data'][0]['mana_cost']
            if 'Creature' in self.type_line:
                self.power = card['data'][0]['power']
                self.toughness = card['data'][0]['toughness']

            # Get the image URL
            img_url = card['data'][0]['image_uris']['art_crop']
            
            # Save the image
            with open(path+card_to_search+'.png', 'wb') as out_file:
                copyfileobj(get(img_url, stream = True).raw, out_file)

            # Transform the image for opencv2
            card_image = cv2.imread(path + card_to_search+'.png')
            self.image = cv2.cvtColor(card_image, cv2.COLOR_RGB2BGR)
            self.corrupted = False
        except:
            self.corrupted = True
            print('         Card type (double sided?) not supported yet!')


def getListOfCards(**kwargs):
    path = kwargs.get('path', '')
    list_of_cards = []
    number_of_copies = []
    
    with open(path) as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            copies = line.split(' ')[0]
            name_array = line.split('\n')[0]
            name_array = name_array.split(' ')[1:]
            name = ' '.join(name_array)
            list_of_cards.append(name)
            number_of_copies.append(copies)

    return list_of_cards, number_of_copies


def brightenCardImage(original_card_image):
    # Black and white
    gray_image = cv2.cvtColor(original_card_image, cv2.COLOR_BGR2GRAY)

    # Increase brightness
    brightness = 130
    contrast = 70
    brightened_image = np.int16(gray_image)
    brightened_image = brightened_image * (contrast/127+1) - contrast + brightness
    brightened_image = np.clip(brightened_image, 0, 255)
    brightened_image = np.uint8(brightened_image)

    # Conversion for use in PIL
    brightened_image = cv2.cvtColor(brightened_image, cv2.COLOR_BGR2RGBA)
    brightened_image = Image.fromarray(brightened_image)

    return brightened_image


def drawCard(brightened_image, card_data):
    # Card editing
    C_px_in = 3.5/1307 # (in/px) conversion rate
    dpi = 1307/3.5 # the dpi
    card_width_px, card_height_px = 936, 1307
    illustration_width_in, illustration_height_in = 2*1.07, 1.5*1.07
    illustration_width_px, illustration_height_px = int(illustration_width_in/C_px_in), int(illustration_height_in/C_px_in)

    # Set a font
    fontfile = '../assets/fonts/mtg-font/fonts/Mplantin.ttf'
    fontfile_bold = '../assets/fonts/mtg-font/fonts/Matrix-Bold.ttf'

    # Background
    card = Image.new("RGBA", (card_width_px, card_height_px), "white") # set the card background

    # Illustration
    brightened_image_resized = brightened_image.resize((illustration_width_px, illustration_height_px)) # resize the illustration
    x1 = int((card_width_px - illustration_width_px) / 2) #
    y1 = 145
    card.paste(brightened_image_resized,(x1, y1, x1+illustration_width_px, y1+illustration_height_px), mask=brightened_image_resized)

    # Select the layout depending on the card
    if ('Creature' in card_data.type_line) and ('Legendary' in card_data.type_line) :
        layout = Image.open('../assets/layouts/layout-creature-legendary.png')
    elif ('Creature' in card_data.type_line) and (not 'Legendary' in card_data.type_line) :
        layout = Image.open('../assets/layouts/layout-creature-regular.png')
    elif (not 'Creature' in card_data.type_line) and (not 'Legendary' in card_data.type_line) :
        layout = Image.open('../assets/layouts/layout-noncreature-regular.png')
    elif (not 'Creature' in card_data.type_line) and ('Legendary' in card_data.type_line) :
        layout = Image.open('../assets/layouts/layout-noncreature-legendary.png')

    card.paste(layout, mask=layout)

    # Name
    name_font_size = 45
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(fontfile_bold, name_font_size)
    draw.text((70, 93), card_data.name, (88,88,88), font=font, anchor='lm')

    # Type
    type_font_size = 40
    font = ImageFont.truetype(fontfile_bold, type_font_size)
    draw.text((70, 771), card_data.type_line, (88,88,88), font=font, anchor='lm')

    # Power and Toughness
    if 'Creature' in card_data.type_line:
        power_toughness_fontsize = 55
        font = ImageFont.truetype(fontfile, power_toughness_fontsize)
        draw.text((813, 1210), card_data.power+'/'+card_data.toughness, (88,88,88), font=font, align='center' , anchor='mm')

    # Oracle text
    oracle_font_size = 34
    font = ImageFont.truetype(fontfile, oracle_font_size)
    paragraphs = card_data.oracle_text.split('\n')
    x0 = 80
    y0 = 810
    y = y0
    line_counter = 0
    for paragraph in paragraphs:
        lines = textwrap.wrap(paragraph, width=50, replace_whitespace=True)
        line_counter += 0.5
        for line in lines:
            y = y0 + line_counter*oracle_font_size*1.2
            draw.text((x0, y), line, font=font, fill=(88,88,88))
            line_counter += 1

    # Manacost
    # TODO replace manacost by symbols
    mana_cost_font_size = 44
    font = ImageFont.truetype(fontfile, mana_cost_font_size)

    # Get the number of symbols
    symbols_path = '../assets/layouts/symbols/'
    mana_symbols = re.findall(r'{\w+}', card_data.mana_cost)
    mana_symbols_table = ['{W}',
                          '{B}',
                          '{U}',
                          '{G}',
                          '{R}']
    mana_symbols_image = [symbols_path+'W.png',
                          symbols_path+'B.png',
                          symbols_path+'U.png',
                          symbols_path+'G.png',
                          symbols_path+'R.png',
                          symbols_path+'I.png',]
    x0 = 810
    y0 = 76
    mana_symbol_width_px = 45
    mana_symbol_height_px = 45
    xoffset = int(mana_symbol_width_px*1.15)
    for i, mana_symbol in enumerate(reversed(mana_symbols)):
        # Load the right symbol
        x = x0-i*xoffset
        if mana_symbol in mana_symbols_table:
            mana_color = mana_symbol.split('{')[1]
            mana_color = mana_color.split('}')[0]
            mana_color_path = symbols_path + mana_color + '.png'
            mana_symbol_image = Image.open(mana_color_path)
            mana_symbol_image = mana_symbol_image.resize((mana_symbol_width_px, mana_symbol_height_px)) # resize the mana symbol
            card.paste(mana_symbol_image,(x, y0, x+mana_symbol_width_px, y0+mana_symbol_height_px), mask=mana_symbol_image)
        else:
            mana_number = mana_symbol.split('{')[1]
            mana_number = mana_number.split('}')[0]
            mana_color_path = symbols_path + 'i.png'
            mana_symbol_image = Image.open(mana_color_path)
            mana_symbol_image = mana_symbol_image.resize((mana_symbol_width_px, mana_symbol_height_px)) # resize the mana symbol
            card.paste(mana_symbol_image,(x, y0, x+mana_symbol_width_px, y0+mana_symbol_height_px), mask=mana_symbol_image)
            draw.text((x+11, y0+7), mana_number, (88,88,88), font=font, align='right', anchor='lt')

    
    card.save('../output/'+card_data.name+'.png')


def A4layout(list_of_cards, **kwargs):
    dpi = kwargs.get('dpi', 300)
    set_name = kwargs.get('set_name', 'my_proxies')
    root = '../output/'

    # A4 layout dimensions
    a4_width_in = 8.3 # (in)
    a4_height_in = 11.7 # (in)
    a4_width_px = int(a4_width_in * dpi) # (px) conversion in pixels
    a4_height_px = int(a4_height_in * dpi) # (px) conversion in pixels
    
    # Card dimensions
    card_width_in = 2.5 # (in)
    card_height_in = 3.5 # (in)
    card_width_px = int(card_width_in * dpi) # (px) conversion in pixels
    card_height_px = int(card_height_in * dpi) # (px) conversion in pixels

    

    # Create a background
    a4_background = Image.new('RGB',
                              (a4_width_px, a4_height_px),   # A4 at 72dpi
                              (255, 255, 255))  # color
    
    # Compute the cards position in the layout
    n_width = 3 # number of cards to print along the x dimension (width)
    n_height = 3 # number of cards to print along the y dimension (height)
    max_number_of_cards = n_width * n_height
    margin_width_px = (a4_width_px - n_width * card_width_px) / 2 # margin to center the cards
    margin_height_px = (a4_height_px - n_height * card_height_px) / 2 # margin to center the cards
    x0 = margin_width_px # position of the first image
    y0 = margin_height_px # position of the first image
    position_x = [] # array of x-position for any page
    position_y = [] # array of y-position for any page

    for i in range(n_width):
        for j in range(n_height):
            x = int(x0 + j * card_width_px)
            y = int(y0 + i * card_height_px)
            position_x.append(x)
            position_y.append(y)

    # Load and paste all cards of the set in the page
    page_index = 1
    position_index = 0
    pdf_file_list = [] # a list to store pdf file
    for i, card_name in enumerate(list_of_cards):
        print('    Formatting ' + card_name + '...')

        # Load and format the card
        card_image = Image.open(root+card_name+'.png') # Load the image
        card_image_resized = card_image.resize((card_width_px, card_height_px)) # resize the illustration
        
        # Paste the card at the right location
        x = position_x[position_index]
        y = position_y[position_index]
        a4_background.paste(card_image_resized,(x, y, x+card_width_px, y+card_height_px),
                            mask=card_image_resized)
        
        if (i % (max_number_of_cards - 1) == 0 and i != 0) or i == len(list_of_cards)-1:
            # Draw cutting lines
            cutting_line_color = (200, 200, 200)
            cutting_line_length = 50
            
            draw_line = ImageDraw.Draw(a4_background)
            # Draw vertical lines
            y1_top = 0
            y2_top = cutting_line_length
            y1_bot = a4_height_px
            y2_bot = a4_height_px-cutting_line_length
            for i in range(5):
                x = margin_width_px+i*card_width_px                
                draw_line.line(((x, y1_top), (x, y2_top)), fill=cutting_line_color, width = 10) 
                draw_line.line(((x, y1_bot), (x, y2_bot)), fill=cutting_line_color, width = 10) 
            
            # Draw horizontal lines
            x1_left = 0
            x2_left = cutting_line_length
            x1_right = a4_width_px
            x2_right = a4_width_px-cutting_line_length
            for i in range(5):
                y = margin_height_px+i*card_height_px                
                draw_line.line(((x1_left, y), (x2_left, y)), fill=cutting_line_color, width = 10) 
                draw_line.line(((x1_right, y), (x2_right, y)), fill=cutting_line_color, width = 10) 
            
            # If the page if filled with cards, or the last card is reached, save the page
            pdf_file_name = '../output/'+set_name+'_page_'+str(page_index)+'.pdf'
            png_file_name = '../output/'+set_name+'_page_'+str(page_index)+'.png'
            pdf_file_list.append(pdf_file_name)
            a4_background.save(pdf_file_name, 'PDF', quality=100)
            a4_background.save(png_file_name)

            page_index += 1 # Update the page index
            position_index = 0 # Reset the position index

            # Reset the background
            a4_background = Image.new('RGB',
                                      (a4_width_px, a4_height_px), # A4 dimensions
                                      (255, 255, 255))  # color
        else:
            position_index += 1


    # Merge the pdfs
    merger = PdfMerger()
    for pdf in pdf_file_list:
        merger.append(pdf)
    merger.write('../output/'+set_name+'.pdf')
    merger.close()

    # Remove former pdf
    for pdf in pdf_file_list:
        os.remove(pdf)