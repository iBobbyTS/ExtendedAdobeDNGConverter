import os
import json
import csv
import subprocess
import webbrowser

import flet as ft


if os.name == 'nt':  # Windows
    persist_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "aDNGcGUI")
    adc_dir_prompt = adc_dir = r"C:\Program Files\Adobe DNG Converter.exe"
    import platform
    if 'ARM' in platform.machine().upper():
        win_on_arm = True
else:  # macOS/Linux
    persist_dir = os.path.join(os.path.expanduser("~"), ".config", "aDNGcGUI")
    adc_dir = "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter"
    adc_dir_prompt = "/Applications/Adobe DNG Converter.app"


def load_config(file_name):
    file_dir = os.path.join(persist_dir, file_name)
    if os.path.exists(file_dir):
        with open(file_dir, "r") as f:
            return json.load(f)
    return {}


def save_config(file_name, data):
    if not os.path.exists(persist_dir):
        os.makedirs(persist_dir)
    file_dir = os.path.join(persist_dir, file_name)
    with open(file_dir, "w") as f:
        json.dump(data, f)


# 初始化默认语言
current_language = "lang-en"
# 读取语言包
LANGUAGES = {}
with open('languages.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    keys = next(reader)[1:]
    for i in keys:
        LANGUAGES[i] = {}
    for row in reader:
        for key in keys:
            LANGUAGES[key][row[0]] = row[keys.index(key) + 1].replace('\\n', '\n')

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


def update_language(page):
    global lang
    lang = LANGUAGES[current_language]
    # 标题
    page.title = lang["title"]
    page.appbar.title.value = lang["title"]
    # AppBar
    ctrl_language_selector.tooltip.message = lang['language_description']
    control_adc_website_button.text = lang['adc_website_button']
    if os.name == 'nt':
        control_adc_menu.items[1].text = lang['download_adc_windows_x64']
        control_adc_menu.items[2].text = lang['download_adc_windows_arm']
    else:
        control_adc_menu.items[1].text = lang['download_adc_mac']
    # 控件
    # 输入
    control_input_label.value = lang["input_label"]
    control_open_file_button.text = lang["open_file"]
    control_or_text_label.value = lang["or_text_label"]
    control_open_folder_button.text = lang["open_folder"]
    # 输出
    control_output_label.value = lang["output_folder_label"]
    control_open_output_folder_button.text = lang["open_folder"]
    # 开始转换按钮
    control_start_button.text = lang["start_button"]
    control_stop_button.text = lang["stop_button"]
    control_refresh_adc_button.text = lang["refresh_adc_button"]
    # 压缩类型
    control_compression_type_label.value = lang["compression_type_label"]
    for control in control_compression_type_selector.content.controls:
        control.label = lang[control.value]
    control_compression_type_description.tooltip.message = lang["compression_type_description"]
    # 压缩算法
    control_compression_algorithm_label.value = lang["compression_algorithm_label"]
    control_compression_algorithm_description.tooltip.message = lang["compression_algorithm_description"]
    # JXL 压缩质量
    control_compression_quality_label.value = 'JXL '+lang["compression_quality_label"]
    control_compression_quality_description.tooltip.message = lang["compression_quality_description"]
    control_compression_quality_slider_left_text.value = '0\n'+lang['compression_quality_slider_left_text']
    control_compression_quality_slider_right_text.value = '6\n'+lang['compression_quality_slider_right_text']
    # JXL 压缩率
    control_compression_effort_label.value = 'JXL '+lang["compression_effort_label"]
    control_compression_effort_description.tooltip.message = lang["compression_effort_description"]
    control_compression_effort_slider_left_text.value = lang['compression_effort_slider_left_text']
    control_compression_effort_slider_right_text.value = lang['compression_effort_slider_right_text']
    # 缩小
    control_resize_label.value = lang["resize_label"]
    control_resize_description.tooltip.message = lang["resize_description"]
    control_resize_radio.content.controls[0].label = lang["none"]
    control_resize_radio.content.controls[1].label = lang["limit_input_by_side"]
    control_resize_radio.content.controls[2].label = lang["limit_input_by_pixel_count"]
    control_limit_input_by_side.label = lang["limit_input_by_side"]
    control_limit_input_by_pixel_count.label = lang["limit_input_by_pixel_count"]
    # 解拜耳
    control_debayer_label.value = lang["debayer_label"]
    control_debayer_description.tooltip.message = lang["debayer_description"]
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
    control_clear_log_button.text = lang["clear_log_button"]
    # 更新页面
    page.update()


def add_to_log(e, text, newline=True):
    global log_count
    log_count += 1
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
#     if os.name == 'nt':
#         control_adc_selector.pick_files(
#             dialog_title=LANGUAGES[current_language]['please_select'] + 'Adobe DNG Converter.exe'
#         )
#     else:
#         control_adc_selector.get_directory_path(
#             dialog_title=LANGUAGES[current_language]['please_select'] + 'Adobe DNG Converter.app'
#         )


def file_selected(e):
    file_path = ','.join([_.path for _ in e.files])
    # 更新文本控件显示所选文件路径
    control_selected_file_text.value = file_path
    e.page.update()  # 更新页面


def folder_selected(e, control_text):
    # 更新文本控件显示所选文件夹路径
    control_text.value = e.path
    e.page.update()  # 更新页面


def compression_type_changed(e, compression_type_alt=None):
    # 只处理直接因压缩类型改变的参数，间接的靠call其他函数处理。
    global log_count
    log_count = 0
    compression_type = e.data if compression_type_alt is None else compression_type_alt
    # 显示/隐藏压缩相关控件
    flag = compression_type == 'uncompressed'
    for control in [
        control_compression_algorithm_container,
        control_compression_quality_container,
        control_compression_effort_container,
    ]:
        if control.visible is flag:
            control.visible = not flag
    # 有损压缩：显示缩小
    flag = compression_type == 'lossy'
    if control_resize_container.visible is not flag:
        control_resize_container.visible = flag
    # jpeg
    if control_compression_algorithm_selector.value == 'jpg':
        if compression_type == 'lossy':
            control_compression_algorithm_selector.value = 'jxl'
            compression_algorithm_change(e, 'jxl')


    if log_count and (compression_type_alt is None):
        add_to_log(e, '')
    e.page.update()


def compression_algorithm_change(e, algorithm_alt=None):
    global log_count
    log_count = 0
    algorithm = e.data if algorithm_alt is None else algorithm_alt
    if algorithm == 'jxl':
        if control_jxl_compression_parameter_container.visible is False:
            add_to_log(e, lang["log_show_compression_parameters_due_to_jxl"])
            control_jxl_compression_parameter_container.visible = True
        if control_dng_version_dropdown.value not in ('1.7', '1.7.1'):
            add_to_log(e, lang["log_set_dng_version_to_1_7_due_to_jxl"])
            control_dng_version_dropdown.value = '1.7'
        # 如果压缩类型==无损，隐藏压缩质量
        if control_compression_type_selector.value == 'lossless':
            if control_compression_quality_container.visible:
                add_to_log(e, lang["log_hide_compression_quality_due_to_jxl"])
                control_compression_quality_container.visible = False
        else:  # lossy
            if control_compression_quality_container.visible is False:
                add_to_log(e, lang["log_show_compression_quality_due_to_jxl"])
                control_compression_quality_container.visible = True
    elif algorithm == 'jpg':
        if control_jxl_compression_parameter_container.visible:
            add_to_log(e, lang["log_hide_compression_parameters_due_to_jpeg"])
            control_jxl_compression_parameter_container.visible = False
        if control_compression_type_selector.value == 'lossy':
            add_to_log(e, lang["log_set_to_lossless_due_to_jpeg"])
            control_compression_type_selector.value = 'lossless'
            compression_type_changed(e, 'lossless')
    if log_count and (algorithm_alt is None):
        add_to_log(e, '')
    e.page.update()


def compression_quality_slider_change(e):
    control_compression_quality_input.value = str(round(e.control.value, 1))
    e.page.update()


def compression_quality_input_change(e):
    if log_count:
        add_to_log(e, '')
    e.page.update()
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = float(ecv)
        if value < 0:
            add_to_log(e, lang["log_set_quality_to_0"])
            value = 0
        elif value > 6:
            add_to_log(e, lang["log_set_quality_to_6"])
            value = 6
    except ValueError:
        add_to_log(e, lang["log_quality_value_error"].format(ecv=ecv))
        value = 0.1
        e.control.value = '0.1'
    control_compression_quality_slider.value = value
    if log_count:
        add_to_log(e, '')
    e.page.update()


def compression_effort_slider_change(e):
    control_compression_effort_input.value = str(round(e.control.value))
    e.page.update()


def compression_effort_input_change(e):
    global log_count
    log_count = 0
    ecv = e.control.value
    if ecv == '':
        return
    try:
        value = int(ecv)
        if value < 1:
            add_to_log(e, lang["log_set_effort_to_1"])
            value = 1
        elif value > 9:
            add_to_log(e, lang["log_set_effort_to_9"])
            value = 9
    except ValueError:
        add_to_log(e, lang["log_effort_value_error"].format(ecv=ecv))
        value = 9
        e.control.value = '9'
    control_compression_effort_slider.value = value
    if log_count:
        add_to_log(e, '')
    e.page.update()


def resize_changed(e):
    if e.data == 'none':
        control_limit_input_by_side.visible = False
        control_limit_input_by_pixel_count.visible = False
    elif e.data == 'by_side':
        control_limit_input_by_side.visible = True
        control_limit_input_by_pixel_count.visible = False
    elif e.data == 'by_pixel_count':
        control_limit_input_by_side.visible = False
        control_limit_input_by_pixel_count.visible = True
    e.page.update()


def debayer_change(e):
    pass
    # global log_count
    # log_count = 0
    # compression_type = control_compression_type_selector.value
    # compression_algorithm = control_compression_algorithm_selector.value
    # if compression_type == 'lossy' and compression_algorithm == 'jpeg' and e.control.value is False:
    #     add_to_log(e, lang["log_set_debayer_to_true_due_to_debayer_self"])
    #     e.control.value = True
    # if log_count:
    #     add_to_log(e, '')
    # e.page.update()


def dng_version_change(e):
    global log_count
    log_count = 0
    if control_compression_algorithm_selector.value == 'jxl':
        if e.control.value not in ('1.7', '1.7.1'):
            add_to_log(e, lang["log_set_dng_version_to_1_7_due_to_self"])
            control_dng_version_dropdown.value = '1.7'
    if log_count:
        add_to_log(e, '')
    e.page.update()


def start_processing(e):
    global process
    control_start_button.visible = False
    control_stop_button.visible = True
    # 获取压缩参数
    compression_type = control_compression_type_selector.value
    compression_algorithm = control_compression_algorithm_selector.value
    compression_quality = control_compression_quality_input.value
    compression_effort = control_compression_effort_input.value
    debayer = control_debayer_checkbox.value
    jpeg_preview = control_jpeg_preview_radio.value
    fast_load_data = control_fast_load_data_checkbox.value
    embed_original_raw = control_embed_original_raw_checkbox.value
    camera_raw_compatibility = control_camera_raw_compatibility_dropdown.value
    dng_version = control_dng_version_dropdown.value
    parallel_processing = control_parallel_processing_checkbox.value
    args = []
    if compression_type == 'uncompressed':
        args.append('-u')
    else:
        if compression_algorithm == 'jpg':
            if compression_type == 'lossless':
                args.append('-jpg')
        elif compression_algorithm == 'jxl':
            args.append('-jxl')
    process = subprocess.Popen('ffmpeg -i "/Users/ibobby/Pictures/R62_7390 - 同步的片段.m4v" -preset veryslow "/Users/ibobby/Pictures/R62_7390 - 同步的片段-test.m4v"', stderr=subprocess.PIPE, text=True, shell=True)
    for line in process.stderr:
        add_to_log(e, line, False)
        control_log_text.page.update()
    e.page.update()


def stop_processing(e):
    if process:
        control_start_button.visible = True
        control_stop_button.visible = False
        process.terminate()
        add_to_log(e, "Process terminated")
        if log_count:
            add_to_log(e, '')
        e.control.page.update()


def clear_log(e):
    control_log_text.value = ""
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


def main(page):
    # 初始化
    global welcome_text_key, disables, log_count
    # AppBar
    global ctrl_language_selector
    global control_adc_website_button, control_adc_menu
    # 输入文件
    global control_input_label, control_selected_file_text, control_or_text_label, control_open_folder_button, control_open_file_button
    # 输出文件
    global control_output_label, control_output_folder_text, control_open_output_folder_button
    # 开始转换按钮
    global control_start_button, control_stop_button, control_refresh_adc_button
    # 压缩类型
    global control_compression_type_label, control_compression_type_description, control_compression_type_selector
    # 压缩算法
    global control_compression_algorithm_label, control_compression_algorithm_description, control_compression_algorithm_selector
    # 压缩质量
    global control_compression_quality_label, control_compression_quality_description, control_compression_quality_input, control_compression_quality_slider, control_compression_quality_slider_left_text, control_compression_quality_slider_left_text, control_compression_quality_slider_right_text, control_compression_quality_title_container, control_compression_quality_slider_container, control_compression_quality_container
    # 压缩率
    global control_compression_effort_label, control_compression_effort_description, control_compression_effort_input, control_compression_effort_slider, control_compression_effort_slider_left_text, control_compression_effort_slider_right_text, control_compression_effort_container
    # 压缩相关控件（用于在压缩类型为“未压缩”时隐藏）
    global control_compression_algorithm_container, control_compression_container, control_jxl_compression_parameter_container
    # 缩小
    global control_resize_label, control_resize_description, control_resize_radio, control_limit_input_by_side, control_limit_input_by_pixel_count, control_resize_container
    # 解拜耳
    global control_debayer_label, control_debayer_description, control_debayer_checkbox
    # JPEG 预览
    global control_jpeg_preview_label, control_jpeg_preview_description, control_jpeg_preview_radio
    # Fast load data
    global control_fast_load_data_label, control_fast_load_data_description, control_fast_load_data_checkbox
    # 嵌入原始RAW
    global control_embed_original_raw_label, control_embed_original_raw_description, control_embed_original_raw_checkbox
    # Camera RAW 兼容性
    global control_camera_raw_compatibility_label, control_camera_raw_compatibility_description, control_camera_raw_compatibility_dropdown
    # DNG 版本
    global control_dng_version_label, control_dng_version_description, control_dng_version_dropdown
    # 并行处理
    global control_parallel_processing_label, control_parallel_processing_description, control_parallel_processing_checkbox
    # 右侧日志
    # 清除日志按钮
    global control_clear_log_button
    # 日志
    global control_progress_text, control_progress_bar, control_log_text, control_log_scroll_column

    # 窗口
    page.window.width = 1000
    page.window.top = 0
    page.window.height = 1000
    # 初始化
    log_count = 0
    # 顶部App Bar
    # 语言选择
    ctrl_language_selector = ft.PopupMenuButton(
        icon=ft.icons.LANGUAGE,
        items=[
                ft.PopupMenuItem(text="简体中文", data="lang-zh-cn", on_click=lambda e: change_language(e, "lang-zh-cn")),
                ft.PopupMenuItem(text="English", data="lang-en", on_click=lambda e: change_language(e, "lang-en")),
            ],
        tooltip=ft.Tooltip(''),
    )
    control_adc_website_button = ft.PopupMenuItem(
        on_click=lambda e: webbrowser.open('https://helpx.adobe.com/ca/camera-raw/using/adobe-dng-converter.html')
    )
    control_adc_menu = ft.PopupMenuButton(
        content=ft.Text('Adobe DNG Converter'),
        items=[
            control_adc_website_button,
            *([
                ft.PopupMenuItem(on_click=lambda e: webbrowser.open('https://www.adobe.com/go/dng_converter_win')),
                ft.PopupMenuItem(on_click=lambda e: webbrowser.open('https://www.adobe.com/go/dng_converter_winarm')),
            ] if os.name == 'nt' else [
                ft.PopupMenuItem(on_click=lambda e: webbrowser.open('https://www.adobe.com/go/dng_converter_mac'))
            ])
        ],
        tooltip=ft.Tooltip(''),
    )
    page.appbar = ft.AppBar(
        title=ft.Text('title'),
        actions=[
            control_adc_menu,
            ctrl_language_selector,
        ]
    )

    # 输入
    # “输入文件” label
    control_input_label = ft.Text(key="input_file_label")
    # 显示选择的文件路径
    control_selected_file_text = ft.Text(key="selected_file")
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
    input_row = ft.Row(
        controls=[
            control_input_label,
            control_open_file_button,
            control_or_text_label,
            control_open_folder_button,
            input_file_picker,
            input_folder_picker
        ],
        alignment=ft.MainAxisAlignment.START
    )
    control_input_container = ft.Column([
        input_row,
        control_selected_file_text
    ])
    # 输出
    # “输出文件”标签
    control_output_label = ft.Text(key="output_folder_label")
    # 显示选择的文件路径
    control_output_folder_text = ft.Text(key="output_folder_text")
    # 文件选择器
    output_folder_picker = ft.FilePicker(
        on_result=lambda e: folder_selected(e, control_output_folder_text),
    )
    # 文件选择器按钮
    control_open_output_folder_button = ft.ElevatedButton(
        text='text',
        on_click=lambda e: output_folder_picker.get_directory_path()  # 打开文件选择器
    )
    output_row = ft.Row(
        controls=[
            control_output_label,
            control_open_output_folder_button,
            output_folder_picker
        ],
        alignment=ft.MainAxisAlignment.START
    )
    control_output_container = ft.Column([
        output_row,
        control_output_folder_text,
    ])
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

    # 压缩参数
    # 压缩类别
    control_compression_type_label = ft.Text(key="compression_type_label")
    control_compression_type_selector = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="uncompressed"),
            ft.Radio(value="lossless"),
            ft.Radio(value="lossy")
        ]),
        value="lossy",
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
    control_compression_algorithm_selector = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="jpg", label="JPEG"),
            ft.Radio(value="jxl", label="JPEG XL (JXL)")
        ]),
        value="jxl",
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
            value='0.1',
            keyboard_type=ft.KeyboardType.NUMBER,
            border=ft.InputBorder.NONE,
            on_change=compression_quality_input_change
        )
    control_compression_quality_slider = ft.Slider(
        min=0.1,
        max=6,
        value=0.1,
        on_change=compression_quality_slider_change,
        # on_change_end=compression_quality_slider_change,
        divisions=59,
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
        on_change=compression_effort_input_change
    )
    control_compression_effort_slider = ft.Slider(
        min=1,
        max=9,
        value=9,
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
        control_resize_label,
        control_resize_radio,
        control_limit_input_by_side,
        control_limit_input_by_pixel_count
    ], visible=False)

    # 解拜耳
    control_debayer_label = ft.Text(key="debayer_label")
    control_debayer_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_debayer_checkbox = ft.Checkbox(value=False, on_change=debayer_change)
    control_debayer_container = ft.Row([control_debayer_label, control_debayer_description, control_debayer_checkbox])

    # JPEG 预览
    control_jpeg_preview_label = ft.Text(key="jpeg_preview_label")
    control_jpeg_preview_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_jpeg_preview_radio = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="none"),
            ft.Radio(value="medium"),
            ft.Radio(value="full")
        ]),
        value="medium"
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
    control_fast_load_data_checkbox = ft.Checkbox(value=False)
    control_fast_load_data_container = ft.Row([control_fast_load_data_label, control_fast_load_data_description, control_fast_load_data_checkbox])
    # 嵌入原始RAW
    control_embed_original_raw_label = ft.Text(key="embed_original_raw_label")
    control_embed_original_raw_description = ft.Icon(name="help", tooltip=ft.Tooltip(''))
    control_embed_original_raw_checkbox = ft.Checkbox(value=False)
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
        ]
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
    control_dng_version_dropdown = ft.Dropdown(
        value='1.7',
        options=[
            ft.dropdown.Option(text='1.1'),
            ft.dropdown.Option(text='1.3'),
            ft.dropdown.Option(text='1.4'),
            ft.dropdown.Option(text='1.5'),
            ft.dropdown.Option(text='1.6'),
            ft.dropdown.Option(text='1.7'),
            ft.dropdown.Option(text='1.7.1')
        ],
        on_change=dng_version_change
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
    control_parallel_processing_checkbox = ft.Checkbox(value=False)
    control_parallel_processing_container = ft.Row([
        control_parallel_processing_label,
        control_parallel_processing_description,
        control_parallel_processing_checkbox
    ])
    # 左侧参数
    left_side = ft.Column(
        [
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
        expand=True,
        scroll=ft.ScrollMode.ALWAYS
    )
    # 右侧日志
    control_progress_text = ft.Text(key="progress_text", value='/')
    control_progress_bar = ft.ProgressBar(value=0.0)
    control_clear_log_button = ft.TextButton(on_click=clear_log)
    control_log_text = ft.Text(
        key="log_text",
        value="",
    )
    control_log_scroll_column = ft.Column([control_log_text], scroll=ft.ScrollMode.ALWAYS, expand=True, width=500)
    right_side = ft.Column(
        [
            ft.Column(
                [
                    control_progress_text,
                    control_progress_bar,
                    control_clear_log_button
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            control_log_scroll_column
        ],
        width=500
    )
    # 将控件添加到页面
    page.add(
        # 输入
        control_input_container,
        # 输出
        control_output_container,
        # 开始转换按钮
        control_start_stop_refresh_container,
        # 左侧参数
        ft.Row([left_side, right_side], expand=True)
    )
    # page.add(left_side)
    page.add(right_side)
    # 输出提示更新Adobe DNG Converter
    disables = [left_side, input_row, output_row]
    if os.path.exists(adc_dir):
        welcome_text_key = 'log_adobe_dng_converter_found'
    else:
        welcome_text_key = 'log_adobe_dng_converter_not_found'
        for i in disables:
            i.disabled = True
        control_start_button.visible = False
        control_refresh_adc_button.visible = True
    log_welcome_text(page.window)
    # 初始化语言
    update_language(page)  # 已包含page.update()
    # page.update()


# 运行应用程序
ft.app(target=main)
