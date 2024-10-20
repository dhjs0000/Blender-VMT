import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk
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

class BlenderVersionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Blender 版本管理器")
        self.root.geometry("600x400")
        
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()
        
        self.style = ttk.Style()
        self.apply_theme(self.config.get('PREFERENCES', 'Theme', fallback='default'))
        
        self.create_menu()
        
        self.label = ttk.Label(root, text="选择一个 Blender 版本:")
        self.label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.tree = ttk.Treeview(root, columns=("path"), show="headings")
        self.tree.heading("path", text="路径")
        self.tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        self.button_launch = ttk.Button(root, text="启动 Blender", command=self.launch_blender)
        self.button_launch.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.button_add_version = ttk.Button(root, text="添加 Blender 版本", command=self.add_blender_version)
        self.button_add_version.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        self.button_edit_version = ttk.Button(root, text="编辑 Blender 版本", command=self.edit_blender_version)
        self.button_edit_version.grid(row=2, column=2, padx=10, pady=10, sticky="ew")
        
        self.button_delete_version = ttk.Button(root, text="删除 Blender 版本", command=self.delete_blender_version)
        self.button_delete_version.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        self.button_download_version = ttk.Button(root, text="下载 Blender 版本", command=self.download_blender_version)
        self.button_download_version.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.populate_versions()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="偏好设置", command=self.open_preferences)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)
    
    def open_preferences(self):
        pref_window = tk.Toplevel(self.root)
        pref_window.title("偏好设置")
        pref_window.geometry("500x400")
        
        notebook = ttk.Notebook(pref_window)
        notebook.pack(expand=True, fill='both')
        
        # 常规选项卡
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text='常规')
        
        auto_fetch_var = tk.BooleanVar(value=self.config.getboolean('PREFERENCES', 'AutoFetch', fallback=False))
        ttk.Checkbutton(general_frame, text="自动获取文件夹 Blender 版本列表", variable=auto_fetch_var).pack(anchor='w', padx=10, pady=5)
        
        # 主题选项卡
        theme_frame = ttk.Frame(notebook)
        notebook.add(theme_frame, text='主题')
        
        use_win32_var = tk.BooleanVar(value=False)
        theme_var = tk.StringVar(value=self.config.get('PREFERENCES', 'Theme', fallback='default'))
        themes = ['default', 'clam', 'alt', 'classic', 'win7', 'win10', 'win11']
        
        ttk.Checkbutton(theme_frame, text="使用Win32默认窗口", variable=use_win32_var, command=lambda: self.toggle_theme_options(theme_menu, use_win32_var)).pack(anchor='w', padx=10, pady=5)
        
        ttk.Label(theme_frame, text="选择主题:").pack(anchor='w', padx=10, pady=5)
        theme_menu = ttk.OptionMenu(theme_frame, theme_var, theme_var.get(), *themes)
        theme_menu.pack(anchor='w', padx=10, pady=5)
        
        def apply_theme():
            if use_win32_var.get():
                self.style.theme_use('winnative')
            else:
                self.apply_theme(theme_var.get())
        
        ttk.Button(theme_frame, text="应用主题", command=apply_theme).pack(pady=10)
        
        # 下载选项卡
        download_frame = ttk.Frame(notebook)
        notebook.add(download_frame, text='下载')
        
        source_url_var = tk.StringVar(value=self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/'))
        thread_count_var = tk.IntVar(value=self.config.getint('PREFERENCES', 'ThreadCount', fallback=4))
        
        ttk.Label(download_frame, text="Blender 版本源 URL:").pack(anchor='w', padx=10, pady=5)
        source_entry = ttk.Entry(download_frame, textvariable=source_url_var, width=50)
        source_entry.pack(anchor='w', padx=10, pady=5)
        
        ttk.Label(download_frame, text="下载线程数量:").pack(anchor='w', padx=10, pady=5)
        thread_entry = ttk.Entry(download_frame, textvariable=thread_count_var, width=10)
        thread_entry.pack(anchor='w', padx=10, pady=5)
        
        # 文件管理选项卡
        file_management_frame = ttk.Frame(notebook)
        notebook.add(file_management_frame, text='文件管理')
        
        folder_path_var = tk.StringVar(value=self.config.get('PREFERENCES', 'FolderPath', fallback=''))
        
        ttk.Label(file_management_frame, text="Blender 版本列表文件夹路径:").pack(anchor='w', padx=10, pady=5)
        entry = ttk.Entry(file_management_frame, textvariable=folder_path_var, width=50)
        entry.pack(anchor='w', padx=10, pady=5)
        
        def browse_folder():
            selected_folder = filedialog.askdirectory(title="选择 Blender 版本列表文件夹")
            if selected_folder:
                folder_path_var.set(selected_folder)
        
        ttk.Button(file_management_frame, text="浏览", command=browse_folder).pack(anchor='w', padx=10, pady=5)
        
        def save_preferences():
            if 'PREFERENCES' not in self.config:
                self.config['PREFERENCES'] = {}
            self.config['PREFERENCES']['AutoFetch'] = str(auto_fetch_var.get())
            self.config['PREFERENCES']['FolderPath'] = folder_path_var.get()
            self.config['PREFERENCES']['SourceURL'] = source_url_var.get()
            self.config['PREFERENCES']['ThreadCount'] = str(thread_count_var.get())
            self.config['PREFERENCES']['Theme'] = theme_var.get() if not use_win32_var.get() else 'winnative'
            self.save_config()
            self.populate_versions()
            pref_window.destroy()
        
        ttk.Button(pref_window, text="保存", command=save_preferences).pack(pady=10)
    
    def toggle_theme_options(self, theme_menu, use_win32_var):
        if use_win32_var.get():
            theme_menu.config(state='disabled')
        else:
            theme_menu.config(state='normal')
    
    def apply_theme(self, theme_name):
        if theme_name == 'winnative':
            self.style.theme_use('winnative')
        elif theme_name in ['win7', 'win10', 'win11']:
            self.customize_windows_theme(theme_name)
        else:
            self.style.theme_use(theme_name)
    
    def customize_windows_theme(self, theme_name):
        if theme_name == 'win7':
            self.style.configure("TButton", background="#F0F0F0", foreground="#000000", font=("宋体", 10))
            self.style.configure("TLabel", background="#F0F0F0", foreground="#000000", font=("宋体", 10))
        elif theme_name == 'win10':
            self.style.configure("TButton", background="#FFFFFF", foreground="#000000", font=("Microsoft YaHei UI", 10))
            self.style.configure("TLabel", background="#FFFFFF", foreground="#000000", font=("Microsoft YaHei UI", 10))
        elif theme_name == 'win11':
            self.style.configure("TButton", background="#F3F3F3", foreground="#000000", font=("Microsoft YaHei UI", 10))
            self.style.configure("TLabel", background="#F3F3F3", foreground="#000000", font=("Microsoft YaHei UI", 10))
    
    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        if 'VERSIONS' not in self.config:
            self.config['VERSIONS'] = {}
        if 'PREFERENCES' not in self.config:
            self.config['PREFERENCES'] = {
                'AutoFetch': 'False',
                'FolderPath': '',
                'SourceURL': 'https://mirrors.aliyun.com/blender/release/',
                'ThreadCount': '4',
                'Theme': 'default'
            }
        self.save_config()
    
    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
    
    def populate_versions(self):
        self.tree.delete(*self.tree.get_children())
        if self.config.getboolean('PREFERENCES', 'AutoFetch', fallback=False):
            folder_path = self.config.get('PREFERENCES', 'FolderPath', fallback='')
            if os.path.exists(folder_path):
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, 'blender.exe')):
                        version_name = item
                        self.config['VERSIONS'][version_name] = os.path.join(item_path, 'blender.exe')
                        self.save_config()
                        self.tree.insert("", "end", values=(version_name, item_path))
        for version_name, path in self.config['VERSIONS'].items():
            if not self.tree.exists(version_name):
                self.tree.insert("", "end", values=(version_name, path))
    
    def add_blender_version(self):
        file_path = filedialog.askopenfilename(title="选择 Blender 可执行文件", filetypes=[("Executable Files", "*.exe")])
        if file_path and os.path.exists(file_path):
            version_name = simpledialog.askstring("输入名称", "为此 Blender 版本输入一个名称:")
            if version_name:
                self.config['VERSIONS'][version_name] = file_path
                self.save_config()
                self.populate_versions()
            else:
                messagebox.showwarning("警告", "名称不能为空。")
        else:
            messagebox.showerror("错误", "无效的文件路径。")
    
    def edit_blender_version(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_version = self.tree.item(selected_item, "values")[0]
            new_name = simpledialog.askstring("编辑名称", f"当前名称: {selected_version}\n输入新名称:", initialvalue=selected_version)
            if new_name:
                new_path = filedialog.askopenfilename(title="选择新的 Blender 可执行文件", filetypes=[("Executable Files", "*.exe")], initialdir=os.path.dirname(self.config['VERSIONS'][selected_version]))
                if new_path and os.path.exists(new_path):
                    del self.config['VERSIONS'][selected_version]
                    self.config['VERSIONS'][new_name] = new_path
                    self.save_config()
                    self.populate_versions()
                else:
                    messagebox.showerror("错误", "无效的文件路径。")
            else:
                messagebox.showwarning("警告", "名称不能为空。")
        else:
            messagebox.showwarning("警告", "请选择一个 Blender 版本。")
    
    def delete_blender_version(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_version = self.tree.item(selected_item, "values")[0]
            confirm = messagebox.askyesno("确认删除", f"确定要删除 {selected_version} 吗？")
            if confirm:
                del self.config['VERSIONS'][selected_version]
                self.save_config()
                self.populate_versions()
        else:
            messagebox.showwarning("警告", "请选择一个 Blender 版本。")
    
    def download_blender_version(self):
        major_versions = self.get_major_versions()
        if not major_versions:
            messagebox.showerror("错误", "无法获取可用的 Blender 版本列表。")
            return
        
        # 使用 Listbox 和 Scrollbar 来显示大版本列表
        version_window = tk.Toplevel(self.root)
        version_window.title("选择大版本")
        
        scrollbar = tk.Scrollbar(version_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(version_window, yscrollcommand=scrollbar.set)
        for version in major_versions:
            listbox.insert(tk.END, version)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        def select_major_version():
            major_version = listbox.get(tk.ACTIVE)
            version_window.destroy()
            self.select_minor_version(major_version)
        
        ttk.Button(version_window, text="选择", command=select_major_version).pack(pady=10)
    
    def select_minor_version(self, major_version):
        minor_versions = self.get_minor_versions(major_version)
        if not minor_versions:
            messagebox.showerror("错误", f"无法获取 {major_version} 的小版本列表。")
            return
        
        # 使用 Listbox 和 Scrollbar 来显示小版本列表
        version_window = tk.Toplevel(self.root)
        version_window.title("选择小版本")
        
        scrollbar = tk.Scrollbar(version_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(version_window, yscrollcommand=scrollbar.set)
        for version in minor_versions:
            listbox.insert(tk.END, version)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=listbox.yview)
        
        def select_minor_version():
            minor_version = listbox.get(tk.ACTIVE)
            version_window.destroy()
            # 使用线程来处理下载
            threading.Thread(target=self.download_selected_version, args=(major_version, minor_version)).start()
        
        ttk.Button(version_window, text="选择", command=select_minor_version).pack(pady=10)
    
    def download_selected_version(self, major_version, minor_version):
        folder_path = self.config.get('PREFERENCES', 'FolderPath', fallback='')
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/')
        thread_count = self.config.getint('PREFERENCES', 'ThreadCount', fallback=4)
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "请先设置有效的 Blender 版本列表文件夹路径。")
            return
        
        # 使用选择的小版本文件名直接构建下载 URL
        url = f"{source_url}/{major_version}/{minor_version}"
        print(f"下载 URL: {url}")  # 调试信息
        
        # 创建下载进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("下载进度")
        
        progress_label = ttk.Label(progress_window, text="下载中...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)
        
        percentage_label = ttk.Label(progress_window, text="0%")
        percentage_label.pack(pady=5)
        
        total_size_label = ttk.Label(progress_window, text="文件大小: 0 MB")
        total_size_label.pack(pady=5)
        
        speed_label = ttk.Label(progress_window, text="速度: 0 KB/s")
        speed_label.pack(pady=5)
        
        downloaded_label = ttk.Label(progress_window, text="已下载: 0 MB")
        downloaded_label.pack(pady=5)
        
        thread_progress_frame = ttk.Frame(progress_window)
        thread_progress_frame.pack(pady=10)
        
        thread_progress_labels = []
        for i in range(thread_count):
            label = ttk.Label(thread_progress_frame, text=f"线程 {i+1}: 0 MB")
            label.pack(anchor='w')
            thread_progress_labels.append(label)
        
        try:
            response = requests.head(url)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar["maximum"] = total_size
            total_size_label.config(text=f"文件大小: {total_size / 1024 / 1024:.2f} MB")
            
            zip_path = os.path.join(folder_path, minor_version)
            start_time = time.time()
            downloaded_size = 0
            thread_downloaded_sizes = [0] * thread_count
            
            def download_chunk(start, end, file, thread_index):
                headers = {'Range': f'bytes={start}-{end}'}
                chunk_response = requests.get(url, headers=headers, stream=True)
                chunk_response.raise_for_status()
                for data in chunk_response.iter_content(block_size):
                    file.seek(start)
                    file.write(data)
                    nonlocal downloaded_size
                    downloaded_size += len(data)
                    thread_downloaded_sizes[thread_index] += len(data)
                    progress_bar["value"] = downloaded_size
                    percentage = (downloaded_size / total_size) * 100
                    percentage_label.config(text=f"{percentage:.2f}%")
                    elapsed_time = time.time() - start_time
                    speed = downloaded_size / 1024 / elapsed_time if elapsed_time > 0 else 0
                    speed_label.config(text=f"速度: {speed:.2f} KB/s")
                    downloaded_label.config(text=f"已下载: {downloaded_size / 1024 / 1024:.2f} MB")
                    thread_progress_labels[thread_index].config(text=f"线程 {thread_index+1}: {thread_downloaded_sizes[thread_index] / 1024 / 1024:.2f} MB")
                    progress_window.update_idletasks()
            
            with open(zip_path, 'wb') as file:
                file.truncate(total_size)
                chunk_size = total_size // thread_count  # 使用自定义线程数量
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = [
                        executor.submit(download_chunk, i, min(i + chunk_size, total_size) - 1, file, index)
                        for index, i in enumerate(range(0, total_size, chunk_size))
                    ]
                    for future in futures:
                        future.result()
            
            with zipfile.ZipFile(zip_path, 'r') as z:
                extract_path = os.path.join(folder_path, f"Blender {minor_version.split('-')[1]}")
                z.extractall(extract_path)
            
            # 检查解压后的文件夹结构并调整
            nested_folder = os.path.join(extract_path, os.listdir(extract_path)[0])
            if os.path.isdir(nested_folder):
                for item in os.listdir(nested_folder):
                    shutil.move(os.path.join(nested_folder, item), extract_path)
                os.rmdir(nested_folder)
            
            os.remove(zip_path)  # 删除下载的 zip 文件
            
            messagebox.showinfo("成功", f"Blender {minor_version.split('-')[1]} 下载并解压成功。")
            self.populate_versions()
        except requests.exceptions.RequestException as e:
            messagebox.showerror("下载错误", f"无法下载 Blender {minor_version.split('-')[1]}：{e}")
        except zipfile.BadZipFile:
            messagebox.showerror("解压错误", "下载的文件不是有效的 ZIP 文件。")
        finally:
            progress_window.destroy()
    
    def get_major_versions(self):
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/')
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
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/')
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
    
    def launch_blender(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_version = self.tree.item(selected_item, "values")[0]
            blender_exe = self.config['VERSIONS'].get(selected_version)
            print(f"尝试启动: {blender_exe}")  # 调试信息
            if blender_exe and os.path.exists(blender_exe):
                threading.Thread(target=self.run_blender_with_logging, args=(blender_exe,)).start()
            else:
                messagebox.showerror("错误", f"找不到 {selected_version} 的可执行文件。")
        else:
            messagebox.showwarning("警告", "请选择一个 Blender 版本。")
    
    def run_blender_with_logging(self, blender_exe):
        log_file = os.path.join(os.path.dirname(blender_exe), "blender_log.txt")
        with open(log_file, "w") as log:
            process = subprocess.Popen([blender_exe], stdout=log, stderr=log)
            process.wait()
        messagebox.showinfo("信息", f"Blender 已启动。日志记录在 {log_file}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BlenderVersionManager(root)
    root.mainloop()
