flet pack main.py \
  --add-data "config.json:." \
  --add-data "languages.csv:." \
  --add-data "exiftool/windows/exiftool.exe:exiftool/windows" \
  --icon '/Applications/Adobe DNG Converter.app/Contents/Resources/DNG_App.icns' \
  --product-name "Extended Adobe DNG Converter" \
  --bundle-id "com.ibobby.extendedAdobeDngConverter"
