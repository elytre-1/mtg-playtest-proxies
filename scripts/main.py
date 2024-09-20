import func

# TODO handle double-side cards
# TODO a function for altered proxies
# TODO handle number of copies

if __name__ == '__main__':
    # Get for your deck
    card_list_path = '../user/card_list.txt'
    list_of_cards, number_of_copies = func.getListOfCards(path=card_list_path)

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
