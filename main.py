import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import sys
import threading
import shutil
import re
import queue
from datetime import datetime

class VideoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("音视频下载器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.download_path = self.get_default_download_path()
        self.is_debug = True
        self.resolved_url = ""
        self.current_process = None
        
        self.log_queue = queue.Queue()
        
        self.yt_dlp_path = self.get_resource_path("yt-dlp.exe")
        self.ffmpeg_path = self.get_resource_path("ffmpeg.exe")
        
        self.create_widgets()
        
        self.root.after(100, self._process_log_queue)
        
    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_default_download_path(self):
        if os.name == 'nt':
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        url_frame = ttk.LabelFrame(main_frame, text="下载链接", padding="5")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=70)
        self.url_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.download_btn = ttk.Button(url_frame, text="开始下载", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_btn = ttk.Button(url_frame, text="终止任务", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        resolved_frame = ttk.LabelFrame(main_frame, text="解析地址", padding="5")
        resolved_frame.pack(fill=tk.X, pady=5)
        
        self.resolved_var = tk.StringVar()
        resolved_entry = ttk.Entry(resolved_frame, textvariable=self.resolved_var, width=60, state="readonly")
        resolved_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.copy_btn = ttk.Button(resolved_frame, text="复制", command=self.copy_resolved_url)
        self.copy_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        path_frame = ttk.LabelFrame(main_frame, text="下载路径", padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = ttk.Label(path_frame, text="如果你的默认下载路径改过请自定义路径:")
        path_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_path)
        browse_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        debug_frame = ttk.Frame(main_frame)
        debug_frame.pack(fill=tk.X, pady=5, anchor=tk.W)
        
        self.debug_var = tk.BooleanVar(value=True)
        debug_check = ttk.Checkbutton(debug_frame, text="调试模式", variable=self.debug_var, command=self.toggle_debug)
        debug_check.pack(side=tk.LEFT, padx=5, pady=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="输出日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=90)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
    def browse_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.path_var.set(path)
    
    def toggle_debug(self):
        self.is_debug = self.debug_var.get()
    
    def copy_resolved_url(self):
        if self.resolved_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.resolved_url)
            messagebox.showinfo("提示", "解析地址已复制到剪贴板")
    
    def stop_download(self):
        if self.current_process:
            self.log("正在终止下载任务...")
            try:
                pid = self.current_process.pid
                
                import subprocess as sp
                sp.run(["taskkill", "/F", "/T", "/PID", str(pid)], 
                      capture_output=True, text=True)
                
                import time
                time.sleep(1)
                
                if self.current_process.poll() is None:
                    self.current_process.kill()
                    time.sleep(0.5)
                
                self.log("下载任务已终止")
            except Exception as e:
                self.log(f"终止任务出错: {str(e)}")
            finally:
                self.download_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.current_process = None
    
    def log(self, message):
        self.log_queue.put(message)
    
    def _process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(100, self._process_log_queue)
    
    def resolve_url(self, url):
        self.log("正在解析视频地址...")
        try:
            cmd = [self.yt_dlp_path, "--flat-playlist", "--get-id", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.resolved_url = url
                self.resolved_var.set(self.resolved_url)
                self.log(f"解析成功: {url}")
                if result.stdout.strip():
                    video_count = len(result.stdout.strip().split('\n'))
                    self.log(f"检测到播放列表，包含 {video_count} 个视频")
                return True
            else:
                cmd = [self.yt_dlp_path, "--dump-json", "--max-downloads", "1", url]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    self.resolved_url = url
                    self.resolved_var.set(self.resolved_url)
                    self.log(f"解析成功: {url}")
                    return True
                else:
                    self.log(f"解析失败，但将尝试直接下载: {result.stderr}")
                    self.resolved_url = url
                    self.resolved_var.set(self.resolved_url)
                    return True
        except Exception as e:
            self.log(f"解析错误，将尝试直接下载: {str(e)}")
            self.resolved_url = url
            self.resolved_var.set(self.resolved_url)
            return True
    
    def convert_to_mp4(self, input_file):
        self.log(f"正在转换文件: {input_file}")
        output_file = os.path.splitext(input_file)[0] + ".mp4"
        
        try:
            cmd = [
                self.ffmpeg_path,
                "-hwaccel", "auto",
                "-hwaccel_output_format", "auto",
                "-i", input_file,
                "-c:v", "h264_nvenc",
                "-preset", "fast",
                "-c:a", "aac",
                "-strict", "experimental",
                "-threads", "0",
                "-y",
                output_file
            ]
            
            startupinfo = None
            if not self.is_debug:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo
            )
            
            for line in process.stdout:
                if self.is_debug:
                    self.log(line.strip())
                import time
                time.sleep(0.001)
            
            process.wait()
            
            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode=process.returncode,
                    cmd=' '.join(cmd)
                )
            
            if os.path.exists(output_file):
                os.remove(input_file)
                return output_file
            else:
                return input_file
        except Exception as e:
            self.log(f"转换失败: {str(e)}")
            return input_file
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入下载链接")
            return
        
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def download_thread():
            try:
                if not self.resolve_url(url):
                    self.download_btn.config(state=tk.NORMAL)
                    return
                
                cmd = [
                    self.yt_dlp_path,
                    "-o", os.path.join(self.download_path, "%(title)s.%(ext)s"),
                    "--ffmpeg-location", self.ffmpeg_path,
                    "--ignore-errors",
                    "--no-warnings",
                    "--concurrent-fragments", "10",
                    "--fragment-retries", "10",
                    "--retries", "5",
                    "--buffer-size", "16K",
                ]
                
                if self.is_debug:
                    cmd.extend(["-v", "U"])
                
                cmd.append(url)
                
                self.log(f"开始下载: {url}")
                self.log(f"下载命令: {' '.join(cmd)}")
                
                startupinfo = None
                if not self.is_debug:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    startupinfo=startupinfo
                )
                
                output = []
                while True:
                    line = self.current_process.stdout.readline()
                    if not line:
                        break
                    stripped_line = line.strip()
                    if self.is_debug:
                        self.log(stripped_line)
                    output.append(stripped_line)
                    
                    if "Invoking http downloader on" in stripped_line:
                        try:
                            url_match = re.search(r'(https://[^"\s`]+)', stripped_line)
                            if url_match:
                                self.resolved_url = url_match.group(1)
                                self.resolved_url = self.resolved_url.strip('"`')
                                self.resolved_var.set(self.resolved_url)
                                self.log(f"提取到真实下载地址: {self.resolved_url}")
                        except Exception as e:
                            self.log(f"提取真实地址出错: {str(e)}")
                    
                    import time
                    time.sleep(0.001)
                
                self.current_process.wait()
                
                if self.current_process.returncode != 0:
                    output_str = '\n'.join(output)
                    success_indicators = [
                        "has already been downloaded",
                        "100%",
                        "Download complete",
                        "Finished downloading",
                        "Merging formats",
                        "Deleting original file"
                    ]
                    
                    is_success = any(indicator in output_str for indicator in success_indicators)
                    
                    if is_success:
                        self.log("下载成功，忽略非零退出码")
                    else:
                        raise subprocess.CalledProcessError(
                            returncode=self.current_process.returncode,
                            cmd=' '.join(cmd),
                            output=output_str
                        )
                
                downloaded_files = []
                for file in os.listdir(self.download_path):
                    if file.endswith(('.mp4', '.webm', '.mkv', '.flv', '.avi', '.mp3', '.wav', '.m4a')):
                        file_path = os.path.join(self.download_path, file)
                        if (datetime.now().timestamp() - os.path.getctime(file_path)) < 300:
                            downloaded_files.append(file_path)
                
                converted_files = []
                for file_path in downloaded_files:
                    if not file_path.endswith('.mp4'):
                        converted_file = self.convert_to_mp4(file_path)
                        converted_files.append(converted_file)
                    else:
                        converted_files.append(file_path)
                
                if converted_files:
                    self.log(f"成功下载 {len(converted_files)} 个文件")
                    total_files = len(converted_files)
                    message = f"已成功下载 {total_files} 个文件\n点击'是'打开下载文件夹，'否'关闭提示"
                    if messagebox.askyesno("下载完成", message):
                        folder = self.download_path
                        if os.name == 'nt':
                            os.startfile(folder)
                        else:
                            subprocess.run(["open", folder])
            except subprocess.CalledProcessError as e:
                self.log(f"下载失败: {e.output}")
                error_msg = e.output[-1000:] if len(e.output) > 1000 else e.output
                messagebox.showerror("下载失败", f"下载过程中出错: {error_msg}")
            except Exception as e:
                self.log(f"下载错误: {str(e)}")
                messagebox.showerror("下载错误", f"下载过程中发生错误: {str(e)}")
            finally:
                self.download_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.current_process = None
        
        threading.Thread(target=download_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloader(root)
    root.mainloop()