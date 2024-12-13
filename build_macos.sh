pip install -r requirements.txt
flet pack main.py \
  --add-data "config.json:." \
  --add-data "languages.csv:." \
  --add-data "exiftool/macos/lib:exiftool/macos/lib" \
  --add-data "exiftool/macos/exiftool:exiftool/macos" \
  --icon '/Applications/Adobe DNG Converter.app/Contents/Resources/DNG_App.icns' \
  --product-name "Extended Adobe DNG Converter" \
  --bundle-id "com.ibobby.extendedAdobeDngConverter"
