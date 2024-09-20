# mtg-playtest-proxies
This project is an attempt to generate a single file, cheap to print and decent looking playtest proxy for MTG cards. It is based on the Scryfall API, gets the card images, automatically change their brightness, and redraw the card in a custom layout. The user will be able to print their proxies from a .pdf file.

## Workflow
1. Import your card list in  `./user/`. The format is  `[number of copies] [card name]`. Edit the `card_list_path` variable if necessary.
2. Run `python ./script/main.py`
3. Get your .pdf file in `./output/`

## Dependencies
Dependencies include the following python libraries:
- requests
- json
- shutil
- cv2
- PIL
- numpy
- textwrap
- re
- PyPDF2