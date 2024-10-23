import os
import wx
import wx.adv  # 导入 wx.adv 模块
import configparser
import requests
import zipfile
import io
from bs4 import BeautifulSoup
import threading
import shutil
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor

# 常量定义
CONFIG_FILE = "config.ini"
ICON_PATH = "Blender-VMT [256x256].ico"
ICON_TYPE = wx.BITMAP_TYPE_ICO
DEFAULT_THEME = 'Light'
SOURCE_URL = 'https://mirrors.aliyun.com/blender/release/'
VERSION_MANAGER_NAME = "Blender 版本管理器"
VERSION_MANAGER_VERSION = "v0.1.3"
VERSION_MANAGER_DESCRIPTION = "一个用于管理 Blender 版本的工具。\n\n本软件完全免费开源、禁止在没有许可的情况下商用。"
VERSION_MANAGER_COPYRIGHT = "(C) 2024 dhjs0000"
VERSION_MANAGER_WEBSITE = "https://space.bilibili.com/430218185"

class BlenderVersionManager(wx.Frame):
    def __init__(self, parent, title):
        super(BlenderVersionManager, self).__init__(parent, title=title, size=(600, 400))
        
        self.config_file = CONFIG_FILE
        self.config = configparser.ConfigParser()
        self.load_config()
        
        # 设置窗口图标
        self.SetIcon(wx.Icon(ICON_PATH, ICON_TYPE))
        
        self.init_ui()
        self.apply_theme(self.config.get('PREFERENCES', 'Theme', fallback=DEFAULT_THEME))  # 应用主题
        self.Centre()
        self.Show()
    
    def apply_theme(self, theme):
        # 根据主题设置背景和前景颜色
        if theme == 'Dark':
            bg_color = wx.Colour(45, 45, 48)
            fg_color = wx.Colour(255, 255, 255)
        else:  # Light theme
            bg_color = wx.Colour(255, 255, 255)
            fg_color = wx.Colour(0, 0, 0)
        
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        
        # 更新所有子控件的颜色
        for child in self.GetChildren():
            child.SetBackgroundColour(bg_color)
            child.SetForegroundColour(fg_color)
            if isinstance(child, wx.Panel):
                for subchild in child.GetChildren():
                    subchild.SetBackgroundColour(bg_color)
                    subchild.SetForegroundColour(fg_color)
        
        self.Refresh()
    
    def init_ui(self):
        panel = wx.Panel(self)
        
        # 垂直排列图标按钮
        vbox_buttons = wx.BoxSizer(wx.VERTICAL)
        
        # 创建并绑定按钮
        self.launch_button = wx.BitmapButton(panel, bitmap=self.scale_bitmap("icons/launch.png", 36, 36), size=(48, 48))
        self.launch_button.SetToolTip("启动 Blender")
        self.launch_button.Bind(wx.EVT_BUTTON, self.launch_blender)
        vbox_buttons.Add(self.launch_button, 0, wx.BOTTOM, 5)
        
        self.add_button = wx.BitmapButton(panel, bitmap=self.scale_bitmap("icons/add.png", 36, 36), size=(48, 48))
        self.add_button.SetToolTip("添加 Blender 版本")
        self.add_button.Bind(wx.EVT_BUTTON, self.add_blender_version)
        vbox_buttons.Add(self.add_button, 0, wx.BOTTOM, 5)
        
        self.edit_button = wx.BitmapButton(panel, bitmap=self.scale_bitmap("icons/edit.png", 36, 36), size=(48, 48))
        self.edit_button.SetToolTip("编辑 Blender 版本")
        self.edit_button.Bind(wx.EVT_BUTTON, self.edit_blender_version)
        vbox_buttons.Add(self.edit_button, 0, wx.BOTTOM, 5)
        
        self.delete_button = wx.BitmapButton(panel, bitmap=self.scale_bitmap("icons/delete.png", 36, 36), size=(48, 48))
        self.delete_button.SetToolTip("删除 Blender 版本")
        self.delete_button.Bind(wx.EVT_BUTTON, self.delete_blender_version)
        vbox_buttons.Add(self.delete_button, 0, wx.BOTTOM, 5)
        
        self.download_button = wx.BitmapButton(panel, bitmap=self.scale_bitmap("icons/download.png", 36, 36), size=(48, 48))
        self.download_button.SetToolTip("下载 Blender 版本")
        self.download_button.Bind(wx.EVT_BUTTON, self.download_blender_version)
        vbox_buttons.Add(self.download_button, 0, wx.BOTTOM, 5)
        
        # 水平排列按钮和选择列表
        hbox_main = wx.BoxSizer(wx.HORIZONTAL)
        hbox_main.Add(vbox_buttons, 0, wx.ALL, 10)
        
        # 创建版本列表
        self.version_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.version_list.InsertColumn(0, 'Blender 版本', width=150)
        self.version_list.InsertColumn(1, '路径', width=400)
        hbox_main.Add(self.version_list, 1, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(hbox_main)
        
        self.create_menu_bar()
        self.populate_versions()
    
    def create_menu_bar(self):
        # 创建菜单栏
        menubar = wx.MenuBar()
        
        file_menu = wx.Menu()
        preferences_item = file_menu.Append(wx.ID_PREFERENCES, '偏好设置')
        self.Bind(wx.EVT_MENU, self.open_preferences, preferences_item)
        
        about_menu = wx.Menu()
        about_item = about_menu.Append(wx.ID_ABOUT, '关于')
        self.Bind(wx.EVT_MENU, self.show_about_dialog, about_item)
        
        menubar.Append(file_menu, '&文件')
        menubar.Append(about_menu, '&帮助')
        
        self.SetMenuBar(menubar)
    
    def show_about_dialog(self, event):
        # 显示关于对话框
        info = wx.adv.AboutDialogInfo()
        info.SetName(VERSION_MANAGER_NAME)
        info.SetVersion(VERSION_MANAGER_VERSION)
        info.SetDescription(VERSION_MANAGER_DESCRIPTION)
        info.SetCopyright(VERSION_MANAGER_COPYRIGHT)
        info.SetWebSite(VERSION_MANAGER_WEBSITE)
        wx.adv.AboutBox(info)
    
    def open_preferences(self, event):
        # 打开偏好设置对话框
        pref_dialog = PreferencesDialog(self, "偏好设置", self.config)
        pref_dialog.ShowModal()
        pref_dialog.Destroy()
        self.populate_versions()
    
    def load_config(self):
        # 加载配置文件
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        if 'VERSIONS' not in self.config:
            self.config['VERSIONS'] = {}
        if 'PREFERENCES' not in self.config:
            self.config['PREFERENCES'] = {
                'AutoFetch': 'False',
                'FolderPath': '',
                'SourceURL': SOURCE_URL,
                'ThreadCount': '4'
            }
        self.save_config()
    
    def save_config(self):
        # 保存配置文件
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    def populate_versions(self):
        # 填充版本列表
        self.version_list.DeleteAllItems()
        existing_versions = set(self.config['VERSIONS'].keys())
        
        if self.config.getboolean('PREFERENCES', 'AutoFetch', fallback=False):
            folder_path = self.config.get('PREFERENCES', 'FolderPath', fallback='')
            if os.path.exists(folder_path):
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, 'blender.exe')):
                        version_name = item
                        if version_name not in existing_versions:
                            self.config['VERSIONS'][version_name] = os.path.join(item_path, 'blender.exe')
                            self.save_config()
        
        for version_name, path in self.config['VERSIONS'].items():
            index = self.version_list.InsertItem(self.version_list.GetItemCount(), version_name)
            self.version_list.SetItem(index, 1, path)
    
    def add_blender_version(self, event):
        # 添加新的 Blender 版本
        with wx.FileDialog(self, "选择 Blender 可执行文件", wildcard="Executable files (*.exe)|*.exe",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            file_path = fileDialog.GetPath()
            version_name = wx.GetTextFromUser("为此 Blender 版本输入一个名称:", "输入名称")
            if version_name:
                self.config['VERSIONS'][version_name] = file_path
                self.save_config()
                self.populate_versions()
            else:
                wx.MessageBox("名称不能为空。", "警告", wx.ICON_WARNING)
    
    def edit_blender_version(self, event):
        # 编辑选定的 Blender 版本
        selected_item = self.version_list.GetFirstSelected()
        if selected_item != -1:
            selected_version = self.version_list.GetItemText(selected_item)
            current_path = self.config['VERSIONS'][selected_version]
            
            # 创建并显示编辑对话框
            edit_dialog = EditVersionDialog(self, "编辑 Blender 版本", selected_version, current_path)
            if edit_dialog.ShowModal() == wx.ID_OK:
                new_name, new_path = edit_dialog.get_version_info()
                if new_name and new_path:
                    del self.config['VERSIONS'][selected_version]
                    self.config['VERSIONS'][new_name] = new_path
                    self.save_config()
                    self.populate_versions()
            edit_dialog.Destroy()
        else:
            wx.MessageBox("请选择一个 Blender 版本。", "警告", wx.ICON_WARNING)
    
    def delete_blender_version(self, event):
        # 删除选定的 Blender 版本
        selected_item = self.version_list.GetFirstSelected()
        if selected_item != -1:
            selected_version = self.version_list.GetItemText(selected_item)
            confirm = wx.MessageBox(f"确定要删除 {selected_version} 吗？", "确认删除", wx.YES_NO | wx.ICON_QUESTION)
            if confirm == wx.YES:
                del self.config['VERSIONS'][selected_version]
                self.save_config()
                self.populate_versions()
        else:
            wx.MessageBox("请选择一个 Blender 版本。", "警告", wx.ICON_WARNING)
    
    def download_blender_version(self, event):
        # 下载 Blender 版本
        major_versions = self.get_major_versions()
        if not major_versions:
            wx.MessageBox("无法获取可用的 Blender 版本列表。", "错误", wx.ICON_ERROR)
            return
        
        version_window = wx.SingleChoiceDialog(self, "选择大版本", "选择大版本", major_versions)
        if version_window.ShowModal() == wx.ID_OK:
            major_version = version_window.GetStringSelection()
            self.select_minor_version(major_version)
    
    def select_minor_version(self, major_version):
        # 选择小版本
        minor_versions = self.get_minor_versions(major_version)
        if not minor_versions:
            wx.MessageBox(f"无法获取 {major_version} 的小版本列表。", "错误", wx.ICON_ERROR)
            return
        
        version_window = wx.SingleChoiceDialog(self, "选择小版本", "选择小版本", minor_versions)
        if version_window.ShowModal() == wx.ID_OK:
            minor_version = version_window.GetStringSelection()
            wx.CallAfter(self.download_selected_version, major_version, minor_version)
    
    def download_selected_version(self, major_version, minor_version):
        # 下载选定的 Blender 版本
        folder_path = self.config.get('PREFERENCES', 'FolderPath', fallback='')
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback=SOURCE_URL)
        thread_count = self.config.getint('PREFERENCES', 'ThreadCount', fallback=4)
        if not os.path.exists(folder_path):
            wx.MessageBox("请先设置有效的 Blender 版本列表文件夹路径。", "错误", wx.ICON_ERROR)
            return
        
        url = f"{source_url}/{major_version}/{minor_version}"
        print(f"下载 URL: {url}")  # 调试信息
        
        progress_dialog = wx.ProgressDialog("下载进度", "正在下载...", maximum=100, parent=self, style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME)
        
        def download():
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                block_size = 1024
                zip_path = os.path.join(folder_path, minor_version)
                start_time = time.time()
                downloaded_size = 0
                
                with open(zip_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        file.write(data)
                        downloaded_size += len(data)
                        progress = int((downloaded_size / total_size) * 100)  # 确保进度是整数
                        wx.CallAfter(progress_dialog.Update, progress, f"已下载: {downloaded_size / 1024 / 1024:.2f} MB")
                
                if downloaded_size != total_size:
                    raise Exception("下载不完整，文件大小不匹配。")
                
                with zipfile.ZipFile(zip_path, 'r') as z:
                    extract_path = os.path.join(folder_path, f"Blender {minor_version.split('-')[1]}")
                    z.extractall(extract_path)
                
                nested_folder = os.path.join(extract_path, os.listdir(extract_path)[0])
                if os.path.isdir(nested_folder):
                    for item in os.listdir(nested_folder):
                        shutil.move(os.path.join(nested_folder, item), extract_path)
                    os.rmdir(nested_folder)
                
                os.remove(zip_path)
                wx.CallAfter(wx.MessageBox, f"Blender {minor_version.split('-')[1]} 下载并解压成功。", "成功", wx.ICON_INFORMATION)
                wx.CallAfter(self.populate_versions)
            except requests.exceptions.RequestException as e:
                wx.CallAfter(wx.MessageBox, f"无法下载 Blender {minor_version.split('-')[1]}：{e}", "下载错误", wx.ICON_ERROR)
            except zipfile.BadZipFile:
                wx.CallAfter(wx.MessageBox, "下载的文件不是有效的 ZIP 文件。", "解压错误", wx.ICON_ERROR)
            except Exception as e:
                wx.CallAfter(wx.MessageBox, str(e), "下载错误", wx.ICON_ERROR)
            finally:
                wx.CallAfter(progress_dialog.Destroy)
        
        threading.Thread(target=download).start()
    
    def get_major_versions(self):
        # 获取大版本列表
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback=SOURCE_URL)
        try:
            response = requests.get(source_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            versions = [a.text.strip('/') for a in soup.find_all('a') if a.text.startswith('Blender')]
            print(f"获取到的大版本列表: {versions}")  # 调试信息
            return versions
        except requests.exceptions.RequestException as e:
            print(f"获取版本列表失败：{e}")
            return []
    
    def get_minor_versions(self, major_version):
        # 获取小版本列表
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback=SOURCE_URL)
        try:
            response = requests.get(f"{source_url}/{major_version}/")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            versions = [a.text.strip('/') for a in soup.find_all('a') if a.text.startswith(f"blender-{major_version.split('Blender')[-1]}")]
            print(f"获取到的小版本列表: {versions}")  # 调试信息
            return versions
        except requests.exceptions.RequestException as e:
            print(f"获取小版本列表失败：{e}")
            return []
    
    def launch_blender(self, event):
        # 启动选定的 Blender 版本
        selected_item = self.version_list.GetFirstSelected()
        if selected_item != -1:
            selected_version = self.version_list.GetItemText(selected_item)
            blender_exe = self.config['VERSIONS'].get(selected_version)
            if blender_exe and os.path.exists(blender_exe):
                threading.Thread(target=self.run_blender_with_logging, args=(blender_exe,)).start()
            else:
                wx.MessageBox(f"找不到 {selected_version} 的可执行文件。", "错误", wx.ICON_ERROR)
        else:
            wx.MessageBox("请选择一个 Blender 版本。", "警告", wx.ICON_WARNING)
    
    def run_blender_with_logging(self, blender_exe):
        # 运行 Blender 并记录日志
        log_file = os.path.join(os.path.dirname(blender_exe), "blender_log.txt")
        with open(log_file, "w") as log:
            process = subprocess.Popen([blender_exe], stdout=log, stderr=log)
            process.wait()
        wx.CallAfter(wx.MessageBox, f"Blender 已启动。日志记录在 {log_file}", "信息", wx.ICON_INFORMATION)
    
    def scale_bitmap(self, image_path, target_width, target_height):
        # 缩放图标以适应按钮大小
        image = wx.Image(image_path, wx.BITMAP_TYPE_ANY)
        original_width, original_height = image.GetSize()
        
        # 计算缩放比例
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        
        # 根据最小比例缩放图像
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        
        image = image.Scale(new_width, new_height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

class PreferencesDialog(wx.Dialog):
    def __init__(self, parent, title, config):
        super(PreferencesDialog, self).__init__(parent, title=title, size=(500, 400))
        
        self.config = config
        self.init_ui()
    
    def init_ui(self):
        notebook = wx.Notebook(self)
        
        # 常规选项卡
        general_panel = wx.Panel(notebook)
        notebook.AddPage(general_panel, "常规")
        
        auto_fetch_var = wx.CheckBox(general_panel, label="自动获取文件夹 Blender 版本列表")
        auto_fetch_var.SetValue(self.config.getboolean('PREFERENCES', 'AutoFetch', fallback=False))
        
        theme_choice = wx.Choice(general_panel, choices=["Light", "Dark"])
        theme_choice.SetStringSelection(self.config.get('PREFERENCES', 'Theme', fallback='Light'))
        
        general_sizer = wx.BoxSizer(wx.VERTICAL)
        general_sizer.Add(auto_fetch_var, 0, wx.ALL, 10)
        general_sizer.Add(wx.StaticText(general_panel, label="主题选择(实验性):"), 0, wx.ALL, 10)
        general_sizer.Add(theme_choice, 0, wx.ALL, 10)
        general_panel.SetSizer(general_sizer)
        
        # 下载选项卡
        download_panel = wx.Panel(notebook)
        notebook.AddPage(download_panel, "下载")
        
        source_url_var = wx.TextCtrl(download_panel, value=self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/'))
        thread_count_var = wx.SpinCtrl(download_panel, value=str(self.config.getint('PREFERENCES', 'ThreadCount', fallback=4)), min=1, max=10)
        
        download_sizer = wx.BoxSizer(wx.VERTICAL)
        download_sizer.Add(wx.StaticText(download_panel, label="Blender 版本源 URL:"), 0, wx.ALL, 10)
        download_sizer.Add(source_url_var, 0, wx.ALL | wx.EXPAND, 10)
        download_sizer.Add(wx.StaticText(download_panel, label="下载线程数(实验性 概率卡死):"), 0, wx.ALL, 10)
        download_sizer.Add(thread_count_var, 0, wx.ALL, 10)
        download_panel.SetSizer(download_sizer)
        
        # 文件管理选项卡
        file_management_panel = wx.Panel(notebook)
        notebook.AddPage(file_management_panel, "文件管理")
        
        folder_path_var = wx.TextCtrl(file_management_panel, value=self.config.get('PREFERENCES', 'FolderPath', fallback=''))
        browse_button = wx.Button(file_management_panel, label="浏览")
        browse_button.Bind(wx.EVT_BUTTON, lambda event: self.browse_folder(folder_path_var))
        
        file_management_sizer = wx.BoxSizer(wx.VERTICAL)
        file_management_sizer.Add(wx.StaticText(file_management_panel, label="Blender 版本列表文件夹路径:"), 0, wx.ALL, 10)
        file_management_sizer.Add(folder_path_var, 0, wx.ALL | wx.EXPAND, 10)
        file_management_sizer.Add(browse_button, 0, wx.ALL, 10)
        file_management_panel.SetSizer(file_management_sizer)
        
        # 确认按钮
        save_button = wx.Button(self, label="保存")
        save_button.Bind(wx.EVT_BUTTON, lambda event: self.save_preferences(auto_fetch_var, source_url_var, thread_count_var, folder_path_var, theme_choice))
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(save_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(main_sizer)
    
    def browse_folder(self, folder_path_var):
        # 浏览文件夹
        with wx.DirDialog(self, "选择 Blender 版本列表文件夹", style=wx.DD_DEFAULT_STYLE) as dirDialog:
            if dirDialog.ShowModal() == wx.ID_CANCEL:
                return
            folder_path_var.SetValue(dirDialog.GetPath())
    
    def save_preferences(self, auto_fetch_var, source_url_var, thread_count_var, folder_path_var, theme_choice):
        # 保存偏好设置
        self.config['PREFERENCES']['AutoFetch'] = str(auto_fetch_var.GetValue())
        self.config['PREFERENCES']['SourceURL'] = source_url_var.GetValue()
        self.config['PREFERENCES']['ThreadCount'] = str(thread_count_var.GetValue())
        self.config['PREFERENCES']['FolderPath'] = folder_path_var.GetValue()
        self.config['PREFERENCES']['Theme'] = theme_choice.GetStringSelection()
        
        # 立即应用主题
        self.GetParent().apply_theme(theme_choice.GetStringSelection())
        
        self.EndModal(wx.ID_OK)

class EditVersionDialog(wx.Dialog):
    def __init__(self, parent, title, version_name, version_path):
        super(EditVersionDialog, self).__init__(parent, title=title, size=(400, 200))
        
        self.version_name = version_name
        self.version_path = version_path
        
        self.init_ui()
    
    def init_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # 版本名称输入
        name_label = wx.StaticText(self, label="版本名称:")
        self.name_text = wx.TextCtrl(self, value=self.version_name)
        vbox.Add(name_label, 0, wx.ALL, 5)
        vbox.Add(self.name_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # 版本路径输入
        path_label = wx.StaticText(self, label="版本路径:")
        self.path_text = wx.TextCtrl(self, value=self.version_path)
        vbox.Add(path_label, 0, wx.ALL, 5)
        vbox.Add(self.path_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # 确认和取消按钮
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, label="确认")
        cancel_button = wx.Button(self, wx.ID_CANCEL, label="取消")
        hbox.Add(ok_button, 0, wx.ALL, 5)
        hbox.Add(cancel_button, 0, wx.ALL, 5)
        
        vbox.Add(hbox, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizer(vbox)
    
    def get_version_info(self):
        # 获取版本信息
        return self.name_text.GetValue(), self.path_text.GetValue()

if __name__ == "__main__":
    app = wx.App(False)
    frame = BlenderVersionManager(None, "Blender 版本管理器")
    app.MainLoop()
