print(1)
import datetime
import os
import shutil
import sys
import platform
import json
import csv
import re
import subprocess
import webbrowser
print(2)
import flet as ft
print(3)


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # 打包后文件所在目录
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 开发环境文件所在目录
        return os.path.join(os.path.abspath("."), relative_path)


sys_win = os.name == 'nt'
if sys_win:  # Windows
    persist_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Extended Adobe DNG Converter")
    adc_dir_prompt = adc_dir = r"C:\Program Files\Adobe\Adobe DNG Converter\Adobe DNG Converter.exe"
    exiftool_path = resource_path('exiftool/windows/exiftool.exe')
else:  # macOS/Linux
    persist_dir = os.path.join(os.path.expanduser("~"), ".config", "Extended_Adobe_DNG_Converter")
    adc_dir = "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter"
    adc_dir_prompt = "/Applications/Adobe DNG Converter.app"
    exiftool_path = resource_path('exiftool/macos/exiftool')

RAW_EXTENSIONS = (
    'dng',  # Apple, Casio, DJI, DxO, Google, GoPro, Hasselblad, Huawei, Leica, LG, Light, Motorola, Nokia, OnePlus, OPPO, Parrot, Pentax, Pixii, Ricoh, Samsung, Sigma, Skydio, Sony, Xiaomi, Yuneec, Zeiss
    'tif',  # Canon, Mamiya, Phase One
    'crw', 'cr2', 'cr3',  # Canon
    'raw',  # Contax, Kodak, Leica, Panasonic
    'erf',  # Epson
    'raf',  # Fujifilm
    'gpr',  # GoPro
    '3fr', 'fff',  # Hasselblad
    'arw',  # Hasselblad, Sony
    'dcr', 'kdc',  # Kodak
    'mrw',  # Konica Minolta
    'mos',  # Leaf, Mamiya
    'iiq',  # Leaf, Mamiya, Phase One
    'rwl',  # Leica
    'mef', 'mfw',  # Mamiya
    'nef', 'nrw', 'nefx',  # Nikon
    'orf',  # OM Digital Solutions, Olympus
    'rw2',  # Panasonic
    'pef',  # Pentax
    'srw',  # Samsung
    'x3f',  # Sigma
)


def load_persist(file_name):
    file_dir = os.path.join(persist_dir, file_name)
    if os.path.exists(file_dir):
        with open(file_dir, "r") as f:
            return json.load(f)
    return {}


def save_persist(file_name, data):
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)
    file_dir = os.path.join(persist_dir, file_name)
    with open(file_dir, "w") as f:
        json.dump(data, f)


# 读取/创建配置文件
if os.path.isfile(persist_dir):
    os.remove(persist_dir)  # Fix error caused by previous build
if not os.path.exists(os.path.join(persist_dir, "config.json")):
    os.makedirs(persist_dir, exist_ok=True)
    shutil.copy(resource_path("config.json"), persist_dir)
config = load_persist("config.json")


# 初始化默认语言
print(config)
current_language = config['language']
# 读取语言包
language_csv_path = resource_path('languages.csv')
LANGUAGES = {}
with open(language_csv_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    keys = next(reader)[1:]
    for i in keys:
        LANGUAGES[i] = {}
    for row in reader:
        for key in keys:
            LANGUAGES[key][row[0]] = row[keys.index(key) + 1].replace('\\n', '\n')
lang = LANGUAGES[current_language]
disabled_controls = {}


# value keys
camera_raw_compatibility_dict = {
    '2.4': '-cr2.4',
    '4.1': '-cr4.1',
    '4.6': '-cr4.6',
    '5.4': '-cr5.4',
    '6.6': '-cr6.6',
    '7.1': '-cr7.1',
    '11.2': '-cr11.2',
    '12.4': '-cr12.4',
    '13.2': '-cr13.2',
    '14.0': '-cr14.0',
    '15.3': '-cr15.3',
}
dng_version_dict = {
    '1.1': '-dng1.1',
    '1.3': '-dng1.3',
    '1.4': '-dng1.4',
    '1.5': '-dng1.5',
    '1.6': '-dng1.6',
    '1.7': '-dng1.7',
    '1.7.1': '-dng1.7.1',
}
jpeg_preview_dict = {
    'none': '-p0',
    'medium': '-p1',
    'full': '-p2'
}


def get_compression_parm_from_ui() -> dict:
    result = {
        'compression_type': control_compression_type_selector.value,
        'compression_algorithm': control_compression_algorithm_selector.value,
        'compression_quality': control_compression_quality_slider.value,
        'compression_effort': control_compression_effort_slider.value,
        'resize': control_resize_radio.value,
        'limit_input_by_side': control_limit_input_by_side.value,
        'limit_input_by_pixel_count': control_limit_input_by_pixel_count.value,
        'debayer': control_debayer_checkbox.value,
        'jpeg_preview': control_jpeg_preview_radio.value,
        'fast_load_data': control_fast_load_data_checkbox.value,
        'embed_original_raw': control_embed_original_raw_checkbox.value,
        'camera_raw_compatibility': control_camera_raw_compatibility_dropdown.value,
        'dng_version': control_dng_version_dropdown.value,
        'parallel_processing': control_parallel_processing_checkbox.value
    }
    return result

def delete_preset(e):
    name = control_preset_selector.value
    if name == 'custom':
        return
    for index, item in enumerate(control_preset_selector.options):
        if item.text == name:
            control_preset_selector.options.pop(index)
            break
    config['presets'].pop(name, None)
    config['preset'] = 'custom'
    control_preset_selector.value = 'custom'
    save_persist("config.json", config)
    e.page.update()


def save_config():
    config['language'] = current_language
    config['last_input'] = control_selected_file_text.value
    config['include_subfolder_checkbox'] = control_include_subfolder_checkbox.value
    config['skip_existing_checkbox'] = control_skip_existing_checkbox.value
    config['last_output'] = control_output_folder_text.value
    config['same_as_input_checkbox'] = control_same_as_input_checkbox.value
    config['output_name'] = control_output_name_format_input.value
    config['general_tooltip'] = control_general_tooltip_switch.value
    config['disabled_tooltip'] = control_disabled_tooltip_switch.value
    config['preset'] = control_preset_selector.value
    # save file paths
    config.update(get_compression_parm_from_ui())
    save_persist("config.json", config)


def update_language(page):
    global lang
    lang = LANGUAGES[current_language]
    # 标题
    page.title = lang["title"]
    page.appbar.title.value = lang["title"]
    # AppBar
    ctrl_language_selector.tooltip.message = lang['language_description']
    control_adc_website_button.text = lang['adc_website_button']
    if sys_win:
        import platform
        if 'ARM' in platform.machine().upper():
            control_adc_menu.items[1].text = lang['download_adc_windows_arm']
        else:
            control_adc_menu.items[1].text = lang['download_adc_windows_x64']
    else:
        control_adc_menu.items[1].text = lang['download_adc_mac']
    control_darkmode_selector.tooltip.message = lang['darkmode_description']
    # 控件
    # 输入
    control_input_label.value = lang["input_label"]
    control_open_file_button.text = lang["open_file"]
    control_or_text_label.value = lang["or_text_label"]
    control_open_folder_button.text = lang["open_folder"]
    control_include_subfolder_checkbox.label = lang["include_subfolder_label"]
    control_skip_existing_checkbox.label = lang["skip_existing_label"]
    # 输出
    control_output_label.value = lang["output_folder_label"]
    control_same_as_input_checkbox.label = lang["same_as_input_label"]
    control_open_output_folder_button.text = lang["open_folder"]
    # 输出文件名格式
    control_output_name_format_label.value = lang["output_name_format_label"]
    control_output_name_format_inserter_label.value = lang["output_name_format_inserter_label"]
    control_output_extension_label.value = lang["output_extension_label"]
    control_output_name_format_inserter_dropdown.options[0].text = lang["original_file_name"]
    control_output_name_format_inserter_dropdown.options[1].text = lang["original_file_name_lower_case"]
    control_output_name_format_inserter_dropdown.options[3].text = lang["output_name_format_inserter_dropdown_3"]
    _ = lang["output_name_format_inserter_dropdown_3_key"]
    if sys_win:
        _ = _.replace('%-m', '%#m')
    control_output_name_format_inserter_dropdown.options[3].key = _
    control_output_name_format_inserter_dropdown.options[4].text = lang["year"]
    control_output_name_format_inserter_dropdown.options[5].text = lang["output_name_format_inserter_dropdown_5"]
    control_output_name_format_inserter_dropdown.options[6].text = lang["output_name_format_inserter_dropdown_6"]
    control_output_name_format_inserter_dropdown.options[7].text = lang["output_name_format_inserter_dropdown_7"]
    control_output_name_format_inserter_dropdown.options[8].text = lang["output_name_format_inserter_dropdown_8"]
    control_output_name_format_inserter_dropdown.options[9].text = lang["day"]
    control_output_name_format_inserter_dropdown.options[10].text = lang["hour"]
    control_output_name_format_inserter_dropdown.options[11].text = lang["minute"]
    control_output_name_format_inserter_dropdown.options[12].text = lang["second"]
    control_output_name_format_inserter_dropdown.options[13].text = lang["output_name_format_inserter_dropdown_13"]
    # 开始转换按钮
    control_start_button.text = lang["start_button"]
    control_stop_button.text = lang["stop_button"]
    control_refresh_adc_button.text = lang["refresh_adc_button"]
    # 帮助信息
    control_tooltip_label.value = lang["tooltip_label"]
    control_general_tooltip_label.value = lang["general_tooltip_label"]
    control_disabled_tooltip_label.value = lang["disabled_tooltip_label"]
    # 预设
    control_preset_label.value = lang["preset_label"]
    control_preset_selector.options[0].text = lang["preset_custom"]
    control_preset_dialog_add_preset_label.value = lang["preset_dialog_add_preset_label"]
    control_preset_dialog_discard_button.tooltip = lang["preset_dialog_discard_button"]
    control_preset_dialog_save_button.tooltip = lang["preset_dialog_save_button"]
    # 压缩类型
    control_compression_type_label.value = lang["compression_type_label"]
    for control in control_compression_type_selector.content.controls:
        control.label = lang[control.value]
    control_compression_type_description.tooltip.message = lang["compression_type_description"]
    # if control_compression_type_selector_lossless.tooltip.message != '':
    #     control_compression_type_selector_lossless.tooltip.message = lang['compression_type_lossless_disabled']
    # if control_compression_type_selector_lossy.tooltip.message != '':
    #     control_compression_type_selector_lossy.tooltip.message = lang['compression_type_lossy_disabled']
    # 压缩算法
    control_compression_algorithm_label.value = lang["compression_algorithm_label"]
    control_compression_algorithm_description.tooltip.message = lang["compression_algorithm_description"]
    # if control_compression_algorithm_selector_jpeg.tooltip.message != '':
    #     control_compression_algorithm_selector_jpeg.tooltip.message = lang['compression_algorithm_jpeg_disabled']
    # JXL 压缩质量
    control_compression_quality_label.value = lang["compression_quality_label"]
    control_compression_quality_description.tooltip.message = lang["compression_quality_description"]
    control_compression_quality_slider_left_text.value = '0.1\n'+lang['compression_quality_slider_left_text']
    control_compression_quality_slider_right_text.value = '6\n'+lang['compression_quality_slider_right_text']
    # JXL 压缩率
    control_compression_effort_label.value = lang["compression_effort_label"]
    control_compression_effort_description.tooltip.message = lang["compression_effort_description"]
    control_compression_effort_slider_left_text.value = lang['compression_effort_slider_left_text']
    control_compression_effort_slider_right_text.value = lang['compression_effort_slider_right_text']
    # 缩小
    control_resize_label.value = lang["resize_label"]
    control_resize_description.tooltip.message = lang["resize_description"]
    control_resize_radio.content.controls[0].label = lang["none"]
    control_resize_radio.content.controls[1].label = lang["limit_input_by_side"]
    control_resize_radio.content.controls[2].label = lang["limit_input_by_pixel_count"]
    control_limit_input_by_side.label = lang["enter_side_length"]
    control_limit_input_by_pixel_count.label = lang["enter_pixel_count"]
    # 解拜耳
    control_debayer_label.value = lang["debayer_label"]
    control_debayer_description.tooltip.message = lang["debayer_description"]
    # if control_debayer_checkbox.tooltip.message != '':
    #     control_debayer_checkbox.tooltip.message = lang['debayer_disabled']
    # JPEG 预览
    control_jpeg_preview_label.value = lang["jpeg_preview_label"]
    control_jpeg_preview_description.tooltip.message = lang["jpeg_preview_description"]
    control_jpeg_preview_radio.content.controls[0].label = lang["none"]
    control_jpeg_preview_radio.content.controls[1].label = lang["medium_size"]
    control_jpeg_preview_radio.content.controls[2].label = lang["full_size"]
    # Fast load data
    control_fast_load_data_label.value = lang["fast_load_data_label"]
    control_fast_load_data_description.tooltip.message = lang["fast_load_data_description"]
    # 嵌入原始RAW
    control_embed_original_raw_label.value = lang["embed_original_raw_label"]
    control_embed_original_raw_description.tooltip.message = lang["embed_original_raw_description"]
    # Camera RAW 兼容性
    control_camera_raw_compatibility_label.value = lang["camera_raw_compatibility_label"]
    control_camera_raw_compatibility_description.tooltip.message = lang["camera_raw_compatibility_description"]
    # DNG 版本
    control_dng_version_label.value = lang["dng_version_label"]
    control_dng_version_description.tooltip.message = lang["dng_version_description"]
    # 并行处理
    control_parallel_processing_label.value = lang["parallel_processing_label"]
    control_parallel_processing_description.tooltip.message = lang["parallel_processing_description"]
    # 右侧日志
    # 清除日志按钮
    control_log_error_warning_description.tooltip.message = lang["log_error_warning_description"] + (lang['log_error_warning_description_windows_specific'] if sys_win else '')
    control_log_error.label = lang["log_error"]
    control_log_warning.label = lang["log_warning"]
    control_clear_log_button.text = lang["clear_log_button"]
    # 已禁用组件的说明
    update_disabled_tooltip()
    # 更新页面
    page.update()


def update_disabled_tooltip():
    global disabled_controls
    if control_disabled_tooltip_switch.value:
        for tooltip_key, control in disabled_controls.items():
            control.tooltip.message = lang[tooltip_key]
    else:
        for control in disabled_controls.values():
            control.tooltip.message = ''


def add_to_log(e, text, newline=True):
    control_log_text.value = control_log_text.value + text + ('\n' if newline else '')
    control_log_scroll_column.scroll_to(-1)
    e.page.update()


def change_language(e, language):
    # 更改当前语言并更新界面
    global current_language
    current_language = language
    update_language(e.page)
    log_welcome_text(e)


# def locate_adc_on_click(e):
#     if sys_win:
#         control_adc_selector.pick_files(
#             dialog_title=LANGUAGES[current_language]['please_select'] + 'Adobe DNG Converter.exe'
#         )
#     else:
#         control_adc_selector.get_directory_path(
#             dialog_title=LANGUAGES[current_language]['please_select'] + 'Adobe DNG Converter.app'
#         )


def file_selected(e):
    if not e.files:
        return
    file_path = json.dumps([_.path for _ in e.files], ensure_ascii=False)
    # 更新文本控件显示所选文件路径
    control_selected_file_text.value = file_path
    if control_same_as_input_checkbox.value:
        control_output_folder_text.value = os.path.split(e.files[0].path)[0]
    e.page.update()  # 更新页面



def folder_selected(e, control_text):
    if control_text.key == 'selected_folder_text' and control_same_as_input_checkbox.value:
        control_output_folder_text.value = e.path
    control_text.value = e.path
    e.page.update()  # 更新页面


def general_tooltip_switch_on_change(e):
    if isinstance(e, ft.ControlEvent):
        enable = e.data == 'true'
    else:
        enable = e.value
    control_compression_type_description.visible = enable
    control_compression_algorithm_description.visible = enable
    control_compression_quality_description.visible = enable
    control_compression_effort_description.visible = enable
    control_resize_description.visible = enable
    control_debayer_description.visible = enable
    control_jpeg_preview_description.visible = enable
    control_fast_load_data_description.visible = enable
    control_embed_original_raw_description.visible = enable
    control_camera_raw_compatibility_description.visible = enable
    control_dng_version_description.visible = enable
    control_parallel_processing_description.visible = enable
    e.page.update()


def disabled_tooltip_switch_on_change(e):
    if isinstance(e, ft.ControlEvent):
        enable = e.data == 'true'
    else:
        enable = e.value
    if enable:
        update_disabled_tooltip()
    else:
        for control in disabled_controls.values():
            control.tooltip.message = ''
    e.page.update()


class CompressionTypeContainer:
    class Lossless:
        @staticmethod
        def enable():
            control_compression_type_selector_lossless.disabled = False
            control_compression_type_selector_lossless.tooltip.message = ''
            disabled_controls.pop('compression_type_lossless_disabled', None)

        @staticmethod
        def disable():
            control_compression_type_selector_lossless.disabled = True
            if control_disabled_tooltip_switch.value:
                control_compression_type_selector_lossless.tooltip.message = lang['compression_type_lossless_disabled']
            disabled_controls['compression_type_lossless_disabled'] = control_compression_type_selector_lossless

    class Lossy:
        @staticmethod
        def enable():
            control_compression_type_selector_lossy.disabled = False
            control_compression_type_selector_lossy.tooltip.message = ''
            disabled_controls.pop('compression_type_lossy_disabled', None)

        @staticmethod
        def disable():
            control_compression_type_selector_lossy.disabled = True
            if control_disabled_tooltip_switch.value:
                control_compression_type_selector_lossy.tooltip.message = lang['compression_type_lossy_disabled']
            disabled_controls['compression_type_lossy_disabled'] = control_compression_type_selector_lossy


class CompressionAlgorithmContainer:
    @staticmethod
    def enable():
        control_compression_algorithm_container.disabled = False
        if control_compression_algorithm_selector.value == '':
            control_compression_algorithm_selector.value = 'jxl'

    @staticmethod
    def disable():
        control_compression_algorithm_container.disabled = True
        control_compression_algorithm_selector.value = ''


class CompressionAlgorithmSelectorJpeg:
    @staticmethod
    def enable():
        control_compression_algorithm_selector_jpeg.disabled = False
        control_compression_algorithm_selector_jpeg.tooltip.message = ''
        disabled_controls.pop('compression_algorithm_jpeg_disabled', None)

    @staticmethod
    def disable():
        control_compression_algorithm_selector_jpeg.disabled = True
        if control_disabled_tooltip_switch.value:
            control_compression_algorithm_selector_jpeg.tooltip.message = lang['compression_algorithm_jpeg_disabled']
        disabled_controls['compression_algorithm_jpeg_disabled'] = control_compression_algorithm_selector_jpeg


class CompressionQualityContainer:
    @staticmethod
    def enable():
        control_compression_quality_container.disabled = False
        if control_compression_quality_input.value == '0':
            control_compression_quality_input.value = str(round(control_compression_quality_slider.value, 1))

    @staticmethod
    def disable():
        control_compression_quality_container.disabled = True
        control_compression_quality_input.value = '0'


class CompressionEffortContainer:
    @staticmethod
    def enable():
        control_compression_effort_container.disabled = False
        if control_compression_effort_input.value == '0':
            control_compression_effort_input.value = str(round(control_compression_effort_slider.value))

    @staticmethod
    def disable():
        control_compression_effort_container.disabled = True
        control_compression_effort_input.value = '0'


class DebayerContainer:
    @staticmethod
    def enable():
        control_debayer_container.disabled = False
        control_debayer_checkbox.tooltip.message = ''
        disabled_controls.pop('debayer_disabled', None)

    @staticmethod
    def disable():
        control_debayer_container.disabled = True
        control_debayer_checkbox.value = True
        if control_disabled_tooltip_switch.value:
            control_debayer_checkbox.tooltip.message = lang['debayer_disabled']
        disabled_controls['debayer_disabled'] = control_debayer_checkbox


class ResizeContainer:
    @staticmethod
    def enable():
        control_resize_container.disabled = False
        control_limit_input_by_side.visible = control_resize_radio.value == 'by_side'
        control_limit_input_by_pixel_count.visible = control_resize_radio.value == 'by_pixel_count'

    @staticmethod
    def disable():
        control_resize_container.disabled = True
        control_resize_radio.value = 'none'
        control_limit_input_by_side.visible = False
        control_limit_input_by_pixel_count.visible = False


class DNGVersion:
    @staticmethod
    def disable_old_versions():
        for i in control_dng_version_dropdown_option_old:
            i.visible = False
        if control_dng_version_dropdown.value not in ('1.7', '1.7.1'):
            control_dng_version_dropdown.value = '1.7'

    @staticmethod
    def enable_old_versions():
        for i in control_dng_version_dropdown_option_old:
            i.visible = True


def set_preset_to_custom(*args, **kwargs):
    control_preset_selector.value = 'custom'


def output_same_as_input_changed(e):
    check = control_same_as_input_checkbox.value
    control_open_output_folder_button.disabled = check
    if check:
        inp = control_selected_file_text.value
        if inp[0] == '[':
            control_output_folder_text.value = os.path.split(json.loads(inp)[0])[0]
        else:
            control_output_folder_text.value = inp
    e.page.update()


def compression_type_changed(e, compression_type_alt=None):
    set_preset_to_custom()
    compression_type = e.data if compression_type_alt is None else compression_type_alt
    # 如果是从JPEG切换过来，需要启用有损压缩radio
    if control_compression_algorithm_selector.value != 'jpg':
        CompressionTypeContainer.Lossy.enable()
    # 如果是未压缩，禁用压缩算法选择器
    if compression_type == 'uncompressed':
        CompressionAlgorithmContainer.disable()
    else:
        CompressionAlgorithmContainer.enable()
    # 如果(有损)，强制算法为jxl
    if compression_type == 'lossy':
        control_compression_algorithm_selector.value = 'jxl'
        CompressionAlgorithmSelectorJpeg.disable()
    else:
        CompressionAlgorithmSelectorJpeg.enable()
    # 未压缩、无损JPEG、有损JXL显示解拜耳
    if compression_type == 'uncompressed' or (compression_type == 'lossless' and control_compression_algorithm_selector.value == 'jpg') or (compression_type == 'lossy' and control_compression_algorithm_selector.value == 'jxl'):
        DebayerContainer.enable()
    else:
        # 无损JXL
        DebayerContainer.disable()
    # 有损JXL显示压缩质量
    if (compression_type == 'lossy' and control_compression_algorithm_selector.value == 'jxl') and (control_debayer_checkbox.value):
        CompressionQualityContainer.enable()
    else:
        CompressionQualityContainer.disable()
    # 如果(压缩&&算法==JXL)，显示JXL压缩率
    if (compression_type != 'uncompressed' and control_compression_algorithm_selector.value == 'jxl') and (control_debayer_checkbox.value):
        CompressionEffortContainer.enable()
    else:
        CompressionEffortContainer.disable()
    # 如果是(压缩&&jxl&&rgb_：显示缩小
    if compression_type != 'uncompressed' and control_compression_algorithm_selector.value == 'jxl' and control_debayer_checkbox.value:
        ResizeContainer.enable()
    else:
        ResizeContainer.disable()
    if control_compression_algorithm_selector.value == 'jxl':
        DNGVersion.disable_old_versions()
    else:
        DNGVersion.enable_old_versions()
    e.page.update()


def compression_algorithm_change(e, algorithm_alt=None):
    set_preset_to_custom()
    algorithm = e.data if algorithm_alt is None else algorithm_alt
    if algorithm == 'jxl':
        CompressionTypeContainer.Lossy.enable()
        if control_compression_type_selector.value == 'lossy':
            CompressionQualityContainer.enable()
            DebayerContainer.enable()
        else:
            CompressionQualityContainer.disable()
            DebayerContainer.disable()
        if control_debayer_checkbox.value:
            ResizeContainer.enable()
            CompressionEffortContainer.enable()
        else:
            ResizeContainer.disable()
            CompressionEffortContainer.disable()
        DNGVersion.disable_old_versions()
    elif algorithm == 'jpg':
        # disable lossy radio
        CompressionTypeContainer.Lossy.disable()
        CompressionQualityContainer.disable()
        CompressionEffortContainer.disable()
        DebayerContainer.enable()
        ResizeContainer.disable()
        DNGVersion.enable_old_versions()
    e.page.update()


def compression_quality_slider_change(e):
    set_preset_to_custom()
    current_value = e.control.value
    control_compression_quality_input.value = str(round(current_value, 1))
    e.page.update()

def compression_quality_input_change(e):
    set_preset_to_custom()
    e.page.update()
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = float(ecv)
        if value < 0.1:
            value = 0.1
        elif value > 6:
            value = 6
        control_compression_quality_slider.value = value
        e.page.update()
    except Exception as e:
        print(e)


def compression_quality_input_submit(e):
    set_preset_to_custom()
    if log_count:
        add_to_log(e, '')
    e.page.update()
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = float(ecv)
        if value < 0.1:
            add_to_log(e, lang["log_set_quality_to_0"])
            value = 0.1
            e.control.value = '0.1'
        elif value > 6:
            add_to_log(e, lang["log_set_quality_to_6"])
            value = 6
            e.control.value = '6'
    except ValueError:
        add_to_log(e, lang["log_quality_value_error"].format(ecv=ecv))
        value = 0.1
        e.control.value = '0.1'
    control_compression_quality_slider.value = value
    if log_count:
        add_to_log(e, '')
    e.page.update()


def compression_effort_slider_change(e):
    set_preset_to_custom()
    control_compression_effort_input.value = str(round(e.control.value))
    e.page.update()


def compression_effort_input_change(e):
    set_preset_to_custom()
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = int(ecv)
        if value < 1:
            value = 1
            e.control.value = '1'
        elif value > 9:
            value = 9
            e.control.value = '9'
        control_compression_effort_slider.value = value
        e.page.update()
    except Exception as e:
        print(e)


def compression_effort_input_submit(e):
    set_preset_to_custom()
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = int(ecv)
        if value < 1:
            add_to_log(e, lang["log_set_effort_to_1"])
            value = 1
            e.control.value = '1'
        elif value > 9:
            add_to_log(e, lang["log_set_effort_to_9"])
            value = 9
            e.control.value = '9'
    except ValueError:
        add_to_log(e, lang["log_effort_value_error"].format(ecv=ecv))
        value = 9
        e.control.value = '9'
    control_compression_effort_slider.value = value
    e.page.update()


def resize_changed(e):
    set_preset_to_custom()
    if isinstance(e, ft.ControlEvent):
        resize = e.data
    else:
        resize = e.value
    if resize == 'none':
        control_limit_input_by_side.visible = False
        control_limit_input_by_pixel_count.visible = False
    elif resize == 'by_side':
        control_limit_input_by_side.visible = True
        control_limit_input_by_pixel_count.visible = False
    elif resize == 'by_pixel_count':
        control_limit_input_by_side.visible = False
        control_limit_input_by_pixel_count.visible = True
    e.page.update()


def debayer_changed(e):
    set_preset_to_custom()
    if isinstance(e, ft.ControlEvent):
        debayer = e.data == 'true'
    else:
        debayer = e.value
    if control_compression_algorithm_selector.value == 'jxl':
        if debayer:
            CompressionTypeContainer.Lossless.enable()
            ResizeContainer.enable()
            CompressionEffortContainer.enable()
            CompressionQualityContainer.enable()
        else:
            CompressionTypeContainer.Lossless.disable()
            ResizeContainer.disable()
            CompressionEffortContainer.disable()
            CompressionQualityContainer.disable()
    elif control_compression_algorithm_selector.value == 'jpg':
        ResizeContainer.disable()
        # CompressionEffortContainer.disable()
    e.page.update()


def apply_config_to_ui(e, conf=None):
    if conf is None:
        conf = config
        control_selected_file_text.value = conf['last_input']
        control_include_subfolder_checkbox.value = config['include_subfolder_checkbox']
        control_skip_existing_checkbox.value = config['skip_existing_checkbox']
        control_output_folder_text.value = conf['last_output']
        control_same_as_input_checkbox.value = config['same_as_input_checkbox']
        if config['same_as_input_checkbox']:
            control_open_output_folder_button.disabled = True
        control_output_name_format_input.value = conf['output_name']
        control_general_tooltip_switch.value = conf['general_tooltip']
        general_tooltip_switch_on_change(control_general_tooltip_switch)
        control_disabled_tooltip_switch.value = conf['disabled_tooltip']
        disabled_tooltip_switch_on_change(control_disabled_tooltip_switch)
    control_compression_type_selector.value = conf['compression_type']
    control_compression_algorithm_selector.value = conf['compression_algorithm']
    control_compression_quality_slider.value = conf['compression_quality']
    control_compression_quality_input.value = str(round(conf['compression_quality'], 1))
    control_compression_effort_slider.value = conf['compression_effort']
    control_compression_effort_input.value = str(conf['compression_effort'])
    control_resize_radio.value = conf['resize']
    control_limit_input_by_side.value = conf['limit_input_by_side']
    control_limit_input_by_pixel_count.value = conf['limit_input_by_pixel_count']
    resize_changed(control_resize_radio)
    control_debayer_checkbox.value = conf['debayer']
    debayer_changed(control_debayer_checkbox)
    control_jpeg_preview_radio.value = conf['jpeg_preview']
    control_fast_load_data_checkbox.value = conf['fast_load_data']
    control_embed_original_raw_checkbox.value = conf['embed_original_raw']
    control_camera_raw_compatibility_dropdown.value = conf['camera_raw_compatibility']
    control_dng_version_dropdown.value = conf['dng_version']
    control_parallel_processing_checkbox.value = conf['parallel_processing']
    compression_type_changed(control_compression_type_selector, conf['compression_type'])
    compression_algorithm_change(control_compression_algorithm_selector, conf['compression_algorithm'])
    control_preset_selector.value = conf['preset']
    e.page.update()


def preset_save(e):
    name = control_preset_dialog_preset_name_input.value
    control_preset_dialog_preset_name_input.value = ''
    if name in config['presets']:
        config['presets'][name].update(get_compression_parm_from_ui())
        control_preset_selector.value = name
    else:
        config['presets'][name] = get_compression_parm_from_ui()
        config['presets'][name]['preset'] = name
        control_preset_selector.options.append(ft.dropdown.Option(text=name))
    save_persist("config.json", config)
    control_preset_selector.value = name
    e.page.close(control_add_preset_dialog)
    e.page.update()


def change_preset(e):
    if e.data == control_preset_selector.options[0].key:
        return
    apply_config_to_ui(e, config['presets'][e.data])


def get_capture_time_of_raw_file(file_path):
    global process
    process = subprocess.Popen([exiftool_path, '-DateTimeOriginal', '-s3', file_path], stdout=subprocess.PIPE)
    out, _ = process.communicate()
    return datetime.datetime.strptime(out.decode('utf-8').strip(), '%Y:%m:%d %H:%M:%S')


def start_processing(e):
    global process, break_process, log
    break_process = False
    control_start_button.visible = False
    control_stop_button.visible = True
    e.page.update()
    # 获取文件
    input_path = control_selected_file_text.value
    include_subfolder = control_include_subfolder_checkbox.value
    skip_existing = control_skip_existing_checkbox.value
    output_path = control_output_folder_text.value
    output_file_format = control_output_name_format_input.value
    if output_file_format == '':
        output_file_format = '%F'
    ext = control_output_extension_radio.value
    # 获取压缩参数
    compression_type = control_compression_type_selector.value
    compression_algorithm = control_compression_algorithm_selector.value
    compression_quality = control_compression_quality_input.value
    compression_effort = control_compression_effort_input.value
    debayer = control_debayer_checkbox.value
    jpeg_preview = jpeg_preview_dict[control_jpeg_preview_radio.value]
    fast_load_data = control_fast_load_data_checkbox.value
    embed_original_raw = control_embed_original_raw_checkbox.value
    camera_raw_compatibility = control_camera_raw_compatibility_dropdown.value
    dng_version = control_dng_version_dropdown.value
    parallel_processing = control_parallel_processing_checkbox.value
    args = [adc_dir]
    if compression_type == 'uncompressed':
        args.append('-u')
        if debayer:
            args.append('-l')
    else:
        if compression_algorithm == 'jpg':
            args.append('-c')
            if debayer:
                args.append('-l')
        elif compression_algorithm == 'jxl':
            if not debayer and compression_type == 'lossy':
                args.append('-lossyMosaicJXL')
            elif not debayer and (compression_type == 'lossless'):
                raise Exception('Lossless compression with JXL and no debayering is not supported')
            else:
                args.extend(('-lossy', '-jxl'))
                args.extend(('-jxl_effort', str(compression_effort)))
                if compression_type == 'lossless':
                    args.extend(('-jxl_distance', '0'))
                else:
                    args.extend(('-jxl_distance', str(compression_quality)))
            if control_resize_radio.value == 'by_side':
                args.extend(('-side', control_limit_input_by_side.value))
            elif control_resize_radio.value == 'by_pixel_count':
                args.extend(('-count', control_limit_input_by_pixel_count.value))
    args.append(jpeg_preview)
    if fast_load_data:
        args.append('-fl')
    if embed_original_raw:
        args.append('-e')
    args.append(camera_raw_compatibility_dict[camera_raw_compatibility])
    args.append(dng_version_dict[dng_version])
    if parallel_processing:
        args.append('-mp')
    files = list(os.walk(input_path))
    index_format_parm = re.findall(r"%\((\d+),(\d+)\)d", output_file_format)
    index_format = re.findall(r"%\(\d+,\d+\)d", output_file_format)
    if index_format:
        index_format = index_format[0]
    file_numbering_index = 0
    if index_format_parm:
        index_format_parm = [int(i) for i in index_format_parm[0]]
        file_numbering_index = index_format_parm[1]
    file_count = 0
    for root, _, file_list in files:
        for f in file_list:
            if f.endswith(RAW_EXTENSIONS):
                file_count += 1
    process_count = 0
    control_log_text.value = control_log_text.value + '\n'
    control_progress_text.value = f'0/{file_count}'
    control_progress_bar.value = 0
    e.page.update()
    for root, _, file_list in files:
        subfolder_name = root.removeprefix(input_path).removeprefix('/')
        output_folder = os.path.join(output_path, subfolder_name)
        output_folder = output_folder.removesuffix('/').removeprefix('\\')
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        for file in file_list:
            if break_process:
                break
            if not file.endswith(RAW_EXTENSIONS):
                continue
            input_file = os.path.join(root, file)
            name, _ = os.path.splitext(file)
            output_file_name = output_file_format.replace('%F', name).replace('%f', name.lower())
            if index_format:
                output_file_name = output_file_name.replace(index_format, f'{file_numbering_index:0{index_format_parm[0]}d}')
            input_file_capture_time = get_capture_time_of_raw_file(input_file)
            output_file_name = input_file_capture_time.strftime(output_file_name)
            output_file_name = output_file_name + ext
            output_file_path = os.path.join(output_folder, output_file_name)
            if os.path.exists(output_file_path) and skip_existing:
                add_to_log(e, f"{output_file_path} exists, skipping")
                continue
            file_numbering_index += 1
            _ = args+['-d', output_folder, '-o', output_file_name, input_file]
            add_to_log(e, output_file_name, True)
            log = False
            process = subprocess.Popen(_, stderr=subprocess.PIPE, text=True, shell=False)
            for line in process.stderr:
                if line.startswith('***') and line.endswith('***\n'):
                    if control_log_error.value and 'Error' in line:
                        log = True
                        add_to_log(e, line, False)
                        control_log_text.page.update()
                    elif control_log_warning.value and 'Warning' in line:
                        log = True
                        add_to_log(e, line, False)
                        control_log_text.page.update()
                else:
                    log = True
                    add_to_log(e, line, True)
                    control_log_text.page.update()
            if not break_process:
                if log:
                    control_log_text.value = control_log_text.value.removesuffix('\n') + f'\n{output_file_name} - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n'
                else:
                    control_log_text.value = control_log_text.value.removesuffix('\n')+f' - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
                control_log_scroll_column.scroll_to(-1)
                process_count += 1
                control_progress_text.value = f'{process_count}/{file_count}'
                control_progress_bar.value = process_count/file_count
            e.page.update()
        if break_process:
            break
        if not include_subfolder:
            break
    if not break_process:
        add_to_log(e, f'{input_path} is done converting.', True)
    else:
        break_process = False
    control_stop_button.visible = False
    control_start_button.visible = True
    e.page.update()


def stop_processing(e):
    global break_process
    if process:
        control_start_button.visible = True
        control_stop_button.visible = False
        process.terminate()
        break_process = True
        add_to_log(e, "Process terminated")
        if log_count:
            add_to_log(e, '')
        e.control.page.update()


def clear_log(e):
    global log
    control_log_text.value = ""
    log = True
    e.page.update()


def log_welcome_text(e):
    add_to_log(e, LANGUAGES[current_language][welcome_text_key].format(dir=adc_dir_prompt)+'\n')


def refresh_adc_location(e):
    global welcome_text_key
    if os.path.exists(adc_dir):
        for i in disables:
            i.disabled = False
        control_start_button.visible = True
        control_refresh_adc_button.visible = False
        welcome_text_key = "log_adobe_dng_converter_found_thank_you"
    else:
        welcome_text_key = "log_adobe_dng_converter_still_not_found"
    log_welcome_text(e)


def insert_name_format(e):
    control_output_name_format_input.value += control_output_name_format_inserter_dropdown.value
    # control_output_name_format_inserter_dropdown.value = ''
    e.page.update()


def change_theme(e, theme):
    e.page.theme_mode = theme
    e.page.update()


def main(page):
    # 初始化
    global welcome_text_key, disables, log_count
    # AppBar
    global ctrl_language_selector
    global control_adc_website_button, control_adc_menu, control_darkmode_selector
    # 输入文件
    global control_input_label, control_selected_file_text, control_or_text_label, control_open_folder_button, control_open_file_button, control_include_subfolder_checkbox, control_skip_existing_checkbox
    # 输出文件
    global control_output_label, control_output_folder_text, control_open_output_folder_button, control_same_as_input_checkbox
    # 输出格式
    global control_output_name_format_label, control_output_name_format_input, control_output_extension_label, control_output_extension_radio, control_output_name_format_inserter_label, control_output_name_format_inserter_dropdown
    # 开始转换按钮
    global control_start_button, control_stop_button, control_refresh_adc_button
    # 帮助信息
    global control_tooltip_label, control_general_tooltip_label, control_general_tooltip_switch, control_disabled_tooltip_label, control_disabled_tooltip_switch
    # 预设
    global control_preset_label, control_preset_selector
    # 预设弹出窗口
    global control_preset_dialog_add_preset_label, control_preset_dialog_preset_name_input, control_preset_dialog_discard_button, control_preset_dialog_save_button, control_add_preset_dialog
    # 压缩类型
    global control_compression_type_label, control_compression_type_description, control_compression_type_selector, control_compression_type_selector_lossless, control_compression_type_selector_lossy
    # 压缩算法
    global control_compression_algorithm_label, control_compression_algorithm_description, control_compression_algorithm_selector, control_compression_algorithm_selector_jpeg, control_compression_algorithm_selector_jxl
    # 压缩质量
    global control_compression_quality_label, control_compression_quality_description, control_compression_quality_input, control_compression_quality_slider, control_compression_quality_slider_left_text, control_compression_quality_slider_left_text, control_compression_quality_slider_right_text, control_compression_quality_title_container, control_compression_quality_slider_container, control_compression_quality_container
    # 压缩率
    global control_compression_effort_label, control_compression_effort_description, control_compression_effort_input, control_compression_effort_slider, control_compression_effort_slider_left_text, control_compression_effort_slider_right_text, control_compression_effort_container
    # 压缩相关控件（用于在压缩类型为“未压缩”时隐藏）
    global control_compression_algorithm_container, control_compression_container, control_jxl_compression_parameter_container
    # 缩小
    global control_resize_label, control_resize_description, control_resize_radio, control_limit_input_by_side, control_limit_input_by_pixel_count, control_resize_container
    # 解拜耳
    global control_debayer_label, control_debayer_description, control_debayer_checkbox, control_debayer_container
    # JPEG 预览
    global control_jpeg_preview_label, control_jpeg_preview_description, control_jpeg_preview_radio
    # Fast load data
    global control_fast_load_data_label, control_fast_load_data_description, control_fast_load_data_checkbox
    # 嵌入原始RAW
    global control_embed_original_raw_label, control_embed_original_raw_description, control_embed_original_raw_checkbox
    # Camera RAW 兼容性
    global control_camera_raw_compatibility_label, control_camera_raw_compatibility_description, control_camera_raw_compatibility_dropdown
    # DNG 版本
    global control_dng_version_label, control_dng_version_description, control_dng_version_dropdown_option_old, control_dng_version_dropdown
    # 并行处理
    global control_parallel_processing_label, control_parallel_processing_description, control_parallel_processing_checkbox
    # 右侧日志
    # 清除日志按钮
    global control_clear_log_button
    # 日志
    global control_progress_text, control_progress_bar, control_log_text, control_log_scroll_column, control_log_error_warning_description, control_log_error, control_log_warning

    # 窗口
    page.window.width = 1250
    page.window.height = 1000
    page.window.min_height = 400  # 设置窗口最小高度为400像素
    page.window.min_width = 1215  # 设置窗口最小高度为400像素
    page.window.top = 0
    page.window.left = 0

    # 初始化
    log_count = 0
    # 顶部App Bar
    # 语言选择
    ctrl_language_selector = ft.PopupMenuButton(
        icon=ft.Icons.LANGUAGE,
        items=[
                ft.PopupMenuItem(text="简体中文", data="lang-zh-cn", on_click=lambda e: change_language(e, "lang-zh-cn")),
                ft.PopupMenuItem(text="English", data="lang-en", on_click=lambda e: change_language(e, "lang-en")),
            ],
        tooltip=ft.Tooltip(''),
    )
    control_adc_website_button = ft.PopupMenuItem(
        on_click=lambda e: webbrowser.open('https://helpx.adobe.com/ca/camera-raw/using/adobe-dng-converter.html')
    )
    system = platform.system()
    if system == 'Windows':
        if 'ARM' in platform.machine().upper():
            download_link = 'https://www.adobe.com/go/dng_converter_winarm'
        else:
            download_link = 'https://www.adobe.com/go/dng_converter_win'
    elif system == 'Darwin':
        download_link = 'https://www.adobe.com/go/dng_converter_mac'
    else:
        raise Exception('Unsupported OS')
    control_adc_menu = ft.PopupMenuButton(
        content=ft.Text('Adobe DNG Converter'),
        items=[
            control_adc_website_button,
            ft.PopupMenuItem(on_click=lambda e: webbrowser.open(download_link))
        ],
        tooltip=ft.Tooltip(''),
    )
    # 深色模式
    control_darkmode_selector = ft.PopupMenuButton(
        icon=ft.Icons.DARK_MODE_OUTLINED,
        items=[
            ft.PopupMenuItem(text="浅色模式", on_click=lambda e: change_theme(e, ft.ThemeMode.LIGHT)),
            ft.PopupMenuItem(text="深色模式", on_click=lambda e: change_theme(e, ft.ThemeMode.DARK)),
            ft.PopupMenuItem(text="跟随系统", on_click=lambda e: change_theme(e, ft.ThemeMode.SYSTEM)),
        ],
        tooltip=ft.Tooltip(''),
    )
    page.appbar = ft.AppBar(
        title=ft.Text('title'),
        actions=[
            control_adc_menu,
            control_darkmode_selector,
            ctrl_language_selector,
        ]
    )

    # 输入
    # “输入文件” label
    control_input_label = ft.Text(key="input_file_label")
    # 显示选择的文件路径
    control_selected_file_text = ft.Text(config['last_input'], key="selected_folder_text")
    # 文件选择器
    input_file_picker = ft.FilePicker(
        on_result=file_selected
    )
    # 文件选择器按钮
    control_open_file_button = ft.ElevatedButton(
        text='text',
        on_click=lambda e: input_file_picker.pick_files(allow_multiple=True)  # 打开文件选择器
    )
    control_or_text_label = ft.Text(key="or_text_label")
    # 文件夹选择器
    input_folder_picker = ft.FilePicker(
        on_result=lambda e: folder_selected(e, control_selected_file_text),
    )
    # 文件夹选择器按钮
    control_open_folder_button = ft.ElevatedButton(
        text='text',
        on_click=lambda e: input_folder_picker.get_directory_path()  # 打开文件选择器
    )
    # 包含子目录
    control_include_subfolder_checkbox = ft.Checkbox(value=False)
    # 跳过已存在
    control_skip_existing_checkbox = ft.Checkbox(value=False)
    control_input_container = ft.Column([
        control_input_label,
        ft.Row(
            controls=[
                control_open_file_button,
                control_or_text_label,
                control_open_folder_button,
                input_file_picker,
                input_folder_picker
            ],
            alignment=ft.MainAxisAlignment.START
        ),
        control_include_subfolder_checkbox,
        control_skip_existing_checkbox,
        control_selected_file_text
    ])
    # 输出
    # “输出文件”标签
    control_output_label = ft.Text()
    # 文件选择器
    output_folder_picker = ft.FilePicker(
        on_result=lambda e: folder_selected(e, control_output_folder_text),
    )
    # 文件选择器按钮
    control_open_output_folder_button = ft.ElevatedButton(
        text='text',
        on_click=lambda e: output_folder_picker.get_directory_path()  # 打开文件选择器
    )
    # 显示选择的文件路径
    control_output_folder_text = ft.Text(config['last_output'], key="output_folder_text")
    control_same_as_input_checkbox = ft.Checkbox(value=False, on_change=output_same_as_input_changed)
    control_output_container = ft.Column([
        control_output_label,
        control_same_as_input_checkbox,
        control_open_output_folder_button,
        output_folder_picker,
        control_output_folder_text,
    ])
    # 文件名格式
    control_output_name_format_label = ft.Text()
    control_output_name_format_input = ft.TextField()
    control_output_name_format_inserter_label = ft.Text()
    control_output_name_format_inserter_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option(key='%F)'),
            ft.dropdown.Option(key='%f)'),
            ft.dropdown.Option(key='%Y-%m-%d-%H%M%S', text='YYYY-MM-DD-HHMMSS'),
            ft.dropdown.Option(key='%b. %d, %Y %H-%M-%S'),
            ft.dropdown.Option(key='%Y'),
            ft.dropdown.Option(key='%B'),
            ft.dropdown.Option(key='%m'),
            ft.dropdown.Option(key='%#m' if sys_win else '%-m'),
            ft.dropdown.Option(key='%b'),
            ft.dropdown.Option(key='%d'),
            ft.dropdown.Option(key='%H'),
            ft.dropdown.Option(key='%M'),
            ft.dropdown.Option(key='%S'),
            ft.dropdown.Option(key='%(4,100)d'),
        ],
        on_change=insert_name_format
    )
    control_output_extension_label = ft.Text()
    control_output_extension_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value='.dng', label='.dng'),
            ft.Radio(value='.DNG', label='.DNG'),
        ]),
        value='.dng'
    )
    control_output_name_format_container = ft.Column([
        control_output_name_format_label,
        control_output_name_format_input,
        ft.Row([
            control_output_name_format_inserter_label,
            control_output_name_format_inserter_dropdown
        ]),
        control_output_extension_label,
        control_output_extension_radio
    ])
    # 压缩参数
    # 说明开关
    control_tooltip_label = ft.Text('')
    control_general_tooltip_label = ft.Text('')
    control_general_tooltip_switch = ft.Switch(
        on_change=general_tooltip_switch_on_change
    )
    control_disabled_tooltip_label = ft.Text('')
    control_disabled_tooltip_switch = ft.Switch(
        on_change=disabled_tooltip_switch_on_change
    )
    control_tooltip_container = ft.Column([
        control_tooltip_label,
        ft.Row([
            control_general_tooltip_label,
            control_general_tooltip_switch,
            control_disabled_tooltip_label,
            control_disabled_tooltip_switch
        ])
    ])
    # 预设
    control_preset_label = ft.Text()
    control_preset_selector = ft.Dropdown(
        options=[
            ft.dropdown.Option(key='custom'),
        ],
        on_change=change_preset,
    )
    control_preset_selector.value = 'custom'
    for preset in config['presets'].keys():
        control_preset_selector.options.append(ft.dropdown.Option(text=preset))
    # 弹出窗口
    control_preset_dialog_add_preset_label = ft.Text()
    control_preset_dialog_preset_name_input = ft.TextField()
    control_preset_dialog_discard_button = ft.IconButton(
        icon=ft.Icons.CLOSE,
        on_click=lambda e: page.close(control_add_preset_dialog)
    )
    control_preset_dialog_save_button = ft.IconButton(
        icon=ft.Icons.CHECK,
        on_click=preset_save
    )
    control_add_preset_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(),
        actions=[
            control_preset_dialog_add_preset_label,
            control_preset_dialog_preset_name_input,
            ft.Row([
                control_preset_dialog_discard_button,
                control_preset_dialog_save_button
            ])
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER
    )
    control_preset_container = ft.Column([
        control_preset_label,
        ft.Row([
            control_preset_selector,
            ft.IconButton(
                icon=ft.Icons.ADD,
                on_click=lambda e: page.open(control_add_preset_dialog)
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE_FOREVER,
                on_click=delete_preset
            )
        ])
    ])
    # 压缩类别
    control_compression_type_label = ft.Text(key="compression_type_label")
    control_compression_type_selector_lossless = ft.Radio(value="lossless", tooltip=ft.Tooltip(''))
    control_compression_type_selector_lossy = ft.Radio(value="lossy", tooltip=ft.Tooltip(''))
    control_compression_type_selector = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="uncompressed", label="Uncompressed"),
            control_compression_type_selector_lossless,
            control_compression_type_selector_lossy
        ]),
        on_change=compression_type_changed
    )
    control_compression_type_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_compression_type_container = ft.Column([
        ft.Row([
            control_compression_type_label, control_compression_type_description
        ]),
        control_compression_type_selector
    ])
    # 压缩算法
    control_compression_algorithm_label = ft.Text(key="compression_algorithm_label")
    control_compression_algorithm_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_compression_algorithm_selector_jpeg = ft.Radio(value="jpg", label="JPEG", tooltip=ft.Tooltip(lang['compression_algorithm_jpeg_disabled']), disabled=True)
    control_compression_algorithm_selector_jxl = ft.Radio(value="jxl", label="JPEG XL (JXL)")
    control_compression_algorithm_selector = ft.RadioGroup(
        content=ft.Row([
            control_compression_algorithm_selector_jpeg,
            control_compression_algorithm_selector_jxl
        ]),
        on_change=compression_algorithm_change
    )
    control_compression_algorithm_container = ft.Column([
        ft.Row([
            control_compression_algorithm_label, control_compression_algorithm_description
        ]),
        control_compression_algorithm_selector
    ])
    # JXL 压缩质量
    control_compression_quality_label = ft.Text(key="compression_quality_label")
    control_compression_quality_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_compression_quality_input = ft.TextField(
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            on_change=compression_quality_input_change,
            on_submit=compression_quality_input_submit,
        )
    control_compression_quality_slider = ft.Slider(
        min=0.1,
        max=6,
        on_change=compression_quality_slider_change,
    )
    control_compression_quality_slider_left_text = ft.Text(text_align=ft.TextAlign.CENTER)
    control_compression_quality_slider_right_text = ft.Text(text_align=ft.TextAlign.CENTER)
    control_compression_quality_title_container = ft.Row([control_compression_quality_label, ft.Container(content=control_compression_quality_input, width=50)])
    control_compression_quality_slider_container = ft.Row(
        controls=[
            control_compression_quality_slider_left_text,
            control_compression_quality_slider,
            control_compression_quality_slider_right_text,
        ]
    )
    control_compression_quality_container = ft.Column([
        ft.Row([
            control_compression_quality_label,
            control_compression_quality_description,
            ft.Container(content=control_compression_quality_input, width=50)
        ]),
        control_compression_quality_slider_container,
    ])
    # JXL 压缩率
    control_compression_effort_label = ft.Text(key="compression_effort_label")
    control_compression_effort_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_compression_effort_input = ft.TextField(
        value='9',
        keyboard_type=ft.KeyboardType.NUMBER,
        border=ft.InputBorder.NONE,
        on_change=compression_effort_input_change,
        on_submit=compression_effort_input_submit
    )
    control_compression_effort_slider = ft.Slider(
        min=1,
        max=9,
        value=9,
        divisions=8,
        on_change=compression_effort_slider_change
    )
    control_compression_effort_slider_left_text = ft.Text(text_align=ft.TextAlign.CENTER)
    control_compression_effort_slider_right_text = ft.Text(text_align=ft.TextAlign.CENTER)
    control_compression_effort_slider_container = ft.Row(
        controls=[
            control_compression_effort_slider_left_text,
            control_compression_effort_slider,
            control_compression_effort_slider_right_text,
        ],
    )
    control_compression_effort_container = ft.Column([
        ft.Row([
            control_compression_effort_label,
            control_compression_effort_description,
            ft.Container(content=control_compression_effort_input, width=50)
        ]),
        control_compression_effort_slider_container
    ])
    # 压缩参数
    control_jxl_compression_parameter_container = ft.Column([
        # 压缩质量
        control_compression_quality_container,
        # 压缩率
        control_compression_effort_container
    ])
    control_compression_container = ft.Column([
        control_compression_algorithm_container,
        control_jxl_compression_parameter_container
    ])
    # 缩小
    control_resize_label = ft.Text(key="resize_label")
    control_resize_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_resize_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="none"),
            ft.Radio(value="by_side"),
            ft.Radio(value="by_pixel_count")
        ]),
        value="none",
        on_change=resize_changed,
    )
    control_limit_input_by_side = ft.TextField(
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False
    )
    control_limit_input_by_pixel_count = ft.TextField(
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False
    )
    control_resize_container = ft.Column([
        ft.Row([control_resize_label, control_resize_description]),
        control_resize_radio,
        control_limit_input_by_side,
        control_limit_input_by_pixel_count
    ])

    # 解拜耳
    control_debayer_label = ft.Text(key="debayer_label")
    control_debayer_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_debayer_checkbox = ft.Checkbox(value=False, on_change=debayer_changed, tooltip=ft.Tooltip(''))
    control_debayer_container = ft.Row([control_debayer_label, control_debayer_description, control_debayer_checkbox])

    # JPEG 预览
    control_jpeg_preview_label = ft.Text(key="jpeg_preview_label")
    control_jpeg_preview_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_jpeg_preview_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="none"),  # none
            ft.Radio(value="medium"),  # medium
            ft.Radio(value="full")   # full
        ]),
        value="-p1",
        on_change=set_preset_to_custom
    )
    control_jpeg_preview_container = ft.Column([
        ft.Row([
            control_jpeg_preview_label,
            control_jpeg_preview_description
        ]),
        control_jpeg_preview_radio
    ])
    # Fast load data
    control_fast_load_data_label = ft.Text(key="fast_load_data_label")
    control_fast_load_data_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_fast_load_data_checkbox = ft.Checkbox(value=False, on_change=set_preset_to_custom)
    control_fast_load_data_container = ft.Row([control_fast_load_data_label, control_fast_load_data_description, control_fast_load_data_checkbox])
    # 嵌入原始RAW
    control_embed_original_raw_label = ft.Text(key="embed_original_raw_label")
    control_embed_original_raw_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_embed_original_raw_checkbox = ft.Checkbox(value=False, on_change=set_preset_to_custom)
    control_embed_original_raw_container = ft.Row([control_embed_original_raw_label, control_embed_original_raw_description, control_embed_original_raw_checkbox])

    # Camera RAW 兼容性
    control_camera_raw_compatibility_label = ft.Text(key="camera_raw_compatibility_label")
    control_camera_raw_compatibility_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_camera_raw_compatibility_dropdown = ft.Dropdown(
        value='15.3',
        options=[
            ft.dropdown.Option(text='2.4'),
            ft.dropdown.Option(text='4.1'),
            ft.dropdown.Option(text='4.6'),
            ft.dropdown.Option(text='5.4'),
            ft.dropdown.Option(text='6.6'),
            ft.dropdown.Option(text='7.1'),
            ft.dropdown.Option(text='11.2'),
            ft.dropdown.Option(text='12.4'),
            ft.dropdown.Option(text='13.2'),
            ft.dropdown.Option(text='14.0'),
            ft.dropdown.Option(text='15.3'),
        ],
        on_change=set_preset_to_custom
    )
    control_camera_raw_compatibility_container = ft.Column([
        ft.Row([
            control_camera_raw_compatibility_label,
            control_camera_raw_compatibility_description
        ]),
        control_camera_raw_compatibility_dropdown
    ])
    # DNG 版本
    control_dng_version_label = ft.Text(key="dng_version_label")
    control_dng_version_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_dng_version_dropdown_option_old = [
            ft.dropdown.Option(text='1.1'),
            ft.dropdown.Option(text='1.3'),
            ft.dropdown.Option(text='1.4'),
            ft.dropdown.Option(text='1.5'),
            ft.dropdown.Option(text='1.6'),
    ]
    control_dng_version_dropdown = ft.Dropdown(
        value='1.7',
        options=[
            *control_dng_version_dropdown_option_old,
            ft.dropdown.Option(text='1.7'),
            ft.dropdown.Option(text='1.7.1')
        ],
        on_change=set_preset_to_custom
    )
    control_dng_version_container = ft.Column([
        ft.Row([
            control_dng_version_label,
            control_dng_version_description,
        ]),
        control_dng_version_dropdown
    ])
    # 嵌入原始RAW
    control_parallel_processing_label = ft.Text(key="parallel_processing_label")
    control_parallel_processing_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_parallel_processing_checkbox = ft.Checkbox(value=False, on_change=set_preset_to_custom)
    control_parallel_processing_container = ft.Row([
        control_parallel_processing_label,
        control_parallel_processing_description,
        control_parallel_processing_checkbox
    ])
    # 参数列
    compression_column = ft.Column(
        [
            # 帮助信息
            control_tooltip_container, ft.Divider(),
            # 预设
            control_preset_container, ft.Divider(),
            # 压缩类型
            control_compression_type_container,
            # 压缩信息
            control_compression_container,
            # 缩小
            control_resize_container,
            # 解拜耳
            control_debayer_container,
            # JPEG 预览
            control_jpeg_preview_container,
            # Fast load data
            control_fast_load_data_container,
            # 嵌入原始RAW
            control_embed_original_raw_container,
            # Camera RAW 兼容性
            control_camera_raw_compatibility_container,
            # DNG 版本
            control_dng_version_container,
            # 并行处理
            control_parallel_processing_container
        ],
        # expand=True,
        width=460,
        scroll=ft.ScrollMode.ALWAYS
    )
    # 日志列
    # 开始转换按钮
    control_start_button = ft.TextButton(on_click=start_processing)
    control_stop_button = ft.TextButton(on_click=stop_processing, visible=False)
    control_refresh_adc_button = ft.TextButton(on_click=refresh_adc_location, visible=False)
    control_start_stop_refresh_container = ft.Row(
        [
            control_start_button,
            control_stop_button,
            control_refresh_adc_button
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    control_progress_text = ft.Text(key="progress_text", value='/')
    control_progress_bar = ft.ProgressBar(value=0.0)
    control_clear_log_button = ft.TextButton(on_click=clear_log)
    control_log_text = ft.Text(
        key="log_text",
        value="",
    )
    control_log_scroll_column = ft.Column([control_log_text], scroll=ft.ScrollMode.ALWAYS, expand=True, width=1000)
    control_log_warning = ft.Switch(value=False, label_position=ft.LabelPosition.LEFT)
    control_log_error = ft.Switch(value=False, label_position=ft.LabelPosition.LEFT)
    control_log_error_warning_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    log_row = ft.Row([control_log_error_warning_description, control_log_warning, control_log_error], alignment=ft.MainAxisAlignment.CENTER)
    log_column = ft.Column(
        [
            ft.Column(
                [
                    # 开始转换按钮
                    control_start_stop_refresh_container,
                    control_progress_text,
                    control_progress_bar,
                    log_row,
                    control_clear_log_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            control_log_scroll_column
        ],
        # width=500
        expand=True,
    )
    # file column
    io_column = ft.Column(
        [
            # 输入
            control_input_container,
            ft.Divider(),
            # 输出
            control_output_container,
            ft.Divider(),
            # 文件名格式
            control_output_name_format_container
        ],
        width=400,
        alignment=ft.MainAxisAlignment.START,
        # scroll=ft.ScrollMode.ALWAYS
    )
    # 将控件添加到页面
    page.add(
        ft.Row([io_column, compression_column, log_column], expand=True)
    )
    # 输出提示更新Adobe DNG Converter
    disables = [compression_column, control_input_container, control_output_container]
    if os.path.exists(adc_dir):
        welcome_text_key = 'log_adobe_dng_converter_found'
    else:
        welcome_text_key = 'log_adobe_dng_converter_not_found'
        for i in disables:
            i.disabled = True
        control_start_button.visible = False
        control_refresh_adc_button.visible = True
    log_welcome_text(page.window)
    # load config
    apply_config_to_ui(page.window)
    # 初始化语言
    update_language(page)  # 已包含page.update()
    # page.update()


# 运行应用程序
ft.app(target=main)
break_process = True
save_config()
