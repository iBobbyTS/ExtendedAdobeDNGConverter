pip install -r requirements.txt
flet pack main.py --add-data "config.json:." --add-data "languages.csv:." --add-data "exiftool/windows/exiftool.exe:exiftool/windows" --product-name "Extended Adobe DNG Converter" --bundle-id "com.ibobby.extendedAdobeDngConverter"
