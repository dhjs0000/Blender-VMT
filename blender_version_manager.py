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

class BlenderVersionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Blender 版本管理器")
        
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()
        
        self.create_menu()
        
        self.label = tk.Label(root, text="选择一个 Blender 版本:")
        self.label.pack(pady=10)
        
        self.tree = ttk.Treeview(root)
        self.tree.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.tree.heading("#0", text="Blender 版本")
        
        self.button_launch = tk.Button(root, text="启动 Blender", command=self.launch_blender)
        self.button_launch.pack(pady=10)
        
        self.button_add_version = tk.Button(root, text="添加 Blender 版本", command=self.add_blender_version)
        self.button_add_version.pack(pady=10)
        
        self.button_edit_version = tk.Button(root, text="编辑 Blender 版本", command=self.edit_blender_version)
        self.button_edit_version.pack(pady=10)
        
        self.button_delete_version = tk.Button(root, text="删除 Blender 版本", command=self.delete_blender_version)
        self.button_delete_version.pack(pady=10)
        
        self.button_download_version = tk.Button(root, text="下载 Blender 版本", command=self.download_blender_version)
        self.button_download_version.pack(pady=10)
        
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
        
        auto_fetch_var = tk.BooleanVar(value=self.config.getboolean('PREFERENCES', 'AutoFetch', fallback=False))
        folder_path_var = tk.StringVar(value=self.config.get('PREFERENCES', 'FolderPath', fallback=''))
        source_url_var = tk.StringVar(value=self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/'))
        
        tk.Checkbutton(pref_window, text="自动获取文件夹 Blender 版本列表", variable=auto_fetch_var).pack(anchor='w', padx=10, pady=5)
        
        tk.Label(pref_window, text="Blender 版本列表文件夹路径:").pack(anchor='w', padx=10, pady=5)
        entry = tk.Entry(pref_window, textvariable=folder_path_var, width=50)
        entry.pack(anchor='w', padx=10, pady=5)
        
        tk.Label(pref_window, text="Blender 版本源 URL:").pack(anchor='w', padx=10, pady=5)
        source_entry = tk.Entry(pref_window, textvariable=source_url_var, width=50)
        source_entry.pack(anchor='w', padx=10, pady=5)
        
        def browse_folder():
            selected_folder = filedialog.askdirectory(title="选择 Blender 版本列表文件夹")
            if selected_folder:
                folder_path_var.set(selected_folder)
        
        tk.Button(pref_window, text="浏览", command=browse_folder).pack(anchor='w', padx=10, pady=5)
        
        def save_preferences():
            if 'PREFERENCES' not in self.config:
                self.config['PREFERENCES'] = {}
            self.config['PREFERENCES']['AutoFetch'] = str(auto_fetch_var.get())
            self.config['PREFERENCES']['FolderPath'] = folder_path_var.get()
            self.config['PREFERENCES']['SourceURL'] = source_url_var.get()
            self.save_config()
            self.populate_versions()
            pref_window.destroy()
        
        tk.Button(pref_window, text="保存", command=save_preferences).pack(pady=10)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        if 'VERSIONS' not in self.config:
            self.config['VERSIONS'] = {}
        if 'PREFERENCES' not in self.config:
            self.config['PREFERENCES'] = {
                'AutoFetch': 'False',
                'FolderPath': '',
                'SourceURL': 'https://mirrors.aliyun.com/blender/release/'
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
                        self.tree.insert("", "end", iid=version_name, text=version_name)
        for version_name in self.config['VERSIONS']:
            if not self.tree.exists(version_name):
                self.tree.insert("", "end", iid=version_name, text=version_name)
    
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
            selected_version = selected_item[0]
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
            selected_version = selected_item[0]
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
        
        tk.Button(version_window, text="选择", command=select_major_version).pack(pady=10)
    
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
        
        tk.Button(version_window, text="选择", command=select_minor_version).pack(pady=10)
    
    def download_selected_version(self, major_version, minor_version):
        folder_path = self.config.get('PREFERENCES', 'FolderPath', fallback='')
        source_url = self.config.get('PREFERENCES', 'SourceURL', fallback='https://mirrors.aliyun.com/blender/release/')
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "请先设置有效的 Blender 版本列表文件夹路径。")
            return
        
        # 使用选择的小版本文件名直接构建下载 URL
        url = f"{source_url}/{major_version}/{minor_version}"
        print(f"下载 URL: {url}")  # 调试信息
        
        # 创建下载进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("下载进度")
        
        progress_label = tk.Label(progress_window, text="下载中...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)
        
        speed_label = tk.Label(progress_window, text="速度: 0 KB/s")
        speed_label.pack(pady=5)
        
        downloaded_label = tk.Label(progress_window, text="已下载: 0 MB")
        downloaded_label.pack(pady=5)
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            progress_bar["maximum"] = total_size
            
            zip_path = os.path.join(folder_path, minor_version)
            start_time = time.time()
            downloaded_size = 0
            
            with open(zip_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded_size += len(data)
                    progress_bar["value"] = downloaded_size
                    elapsed_time = time.time() - start_time
                    speed = downloaded_size / 1024 / elapsed_time if elapsed_time > 0 else 0
                    speed_label.config(text=f"速度: {speed:.2f} KB/s")
                    downloaded_label.config(text=f"已下载: {downloaded_size / 1024 / 1024:.2f} MB")
                    progress_window.update_idletasks()
            
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
            selected_version = selected_item[0]
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
