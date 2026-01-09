import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import sys
import threading
import shutil
import re
import queue
import tempfile
from datetime import datetime
import locale

class VideoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("音视频下载器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.download_path = self.get_default_download_path()
        self.is_debug = True
        self.resolved_url = ""
        self.resolved_is_direct = False
        self.current_process = None
        self.transcode_process = None
        self.stop_event = threading.Event()
        self._ffmpeg_encoder_cache = {}
        self._ffmpeg_encoder_probe_cache = {}
        self._gpu_vendor_cache = None
        
        self.log_queue = queue.Queue()
        self.tools_dir = self.get_tools_dir()
        
        self.yt_dlp_path = self.resolve_ytdlp_path()
        self.ffmpeg_path = self.resolve_ffmpeg_path()
        
        self.create_widgets()
        
        self.root.after(100, self._process_log_queue)

    def get_subprocess_encoding(self):
        forced = os.environ.get("YTD_OUTPUT_ENCODING", "").strip()
        if forced:
            return forced
        if os.name == "nt":
            try:
                enc = locale.getpreferredencoding(False)
            except Exception:
                enc = "mbcs"
            return enc or "mbcs"
        return "utf-8"

    def _set_resolved_url(self, url, is_direct=False):
        self.resolved_url = url
        self.resolved_is_direct = is_direct
        self.resolved_var.set(self.resolved_url)

    def get_creationflags(self):
        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            return subprocess.CREATE_NO_WINDOW
        return 0

    def get_startupinfo(self):
        if self.is_debug:
            return None
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo

    def is_hwaccel_enabled(self):
        v = os.environ.get("YTD_HWACCEL", "1").strip().lower()
        return v not in ("0", "false", "off", "no")

    def get_tools_dir(self):
        base = os.path.join(tempfile.gettempdir(), "ytd-tools")
        try:
            os.makedirs(base, exist_ok=True)
        except Exception:
            return None
        return base
        
    def get_resource_path(self, relative_path):
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        elif getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def resolve_ytdlp_path(self):
        bundled = self.get_resource_path("yt-dlp.exe")
        if os.path.exists(bundled):
            return self.ensure_tool_in_temp(bundled, "yt-dlp.exe")
        found = shutil.which("yt-dlp")
        if found:
            return found
        return bundled

    def resolve_ffmpeg_path(self):
        bundled = self.get_resource_path("ffmpeg.exe")
        if os.path.exists(bundled):
            return self.ensure_tool_in_temp(bundled, "ffmpeg.exe")
        found = shutil.which("ffmpeg")
        if found:
            return found
        return bundled

    def ensure_tool_in_temp(self, source_path, file_name):
        if not self.tools_dir:
            return source_path

        try:
            size = os.path.getsize(source_path)
            mtime = int(os.path.getmtime(source_path))
        except Exception:
            return source_path

        fingerprint_dir = os.path.join(self.tools_dir, f"{file_name}-{size}-{mtime}")
        try:
            os.makedirs(fingerprint_dir, exist_ok=True)
        except Exception:
            return source_path

        target_path = os.path.join(fingerprint_dir, file_name)
        if os.path.exists(target_path):
            return target_path

        tmp_path = target_path + ".tmp"
        try:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            shutil.copy2(source_path, tmp_path)
            os.replace(tmp_path, target_path)
            return target_path
        except Exception:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return source_path

    def get_ffmpeg_executable(self):
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            return self.ffmpeg_path
        found = shutil.which("ffmpeg")
        if found:
            self.ffmpeg_path = found
            return found
        return None

    def _get_gpu_vendor(self):
        if self._gpu_vendor_cache is not None:
            return self._gpu_vendor_cache

        vendor = None
        if os.name == "nt":
            try:
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
                ]
                r = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                    creationflags=self.get_creationflags(),
                )
                names = (r.stdout or "").upper()
                if "NVIDIA" in names:
                    vendor = "nvidia"
                elif "AMD" in names or "RADEON" in names:
                    vendor = "amd"
                elif "INTEL" in names:
                    vendor = "intel"
            except Exception:
                vendor = None

        self._gpu_vendor_cache = vendor
        return vendor

    def _ffmpeg_supports_encoder(self, ffmpeg_exe, encoder_name):
        key = (ffmpeg_exe, encoder_name)
        cached = self._ffmpeg_encoder_cache.get(key)
        if cached is not None:
            return cached

        try:
            r = subprocess.run(
                [ffmpeg_exe, "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                timeout=8,
                stdin=subprocess.DEVNULL,
                creationflags=self.get_creationflags(),
            )
            out = (r.stdout or "") + "\n" + (r.stderr or "")
            supported = encoder_name in out
        except Exception:
            supported = False

        self._ffmpeg_encoder_cache[key] = supported
        return supported

    def _probe_ffmpeg_encoder(self, ffmpeg_exe, encoder_name):
        key = (ffmpeg_exe, encoder_name)
        cached = self._ffmpeg_encoder_probe_cache.get(key)
        if cached is not None:
            return cached

        if not self._ffmpeg_supports_encoder(ffmpeg_exe, encoder_name):
            self._ffmpeg_encoder_probe_cache[key] = (False, "not present")
            return self._ffmpeg_encoder_probe_cache[key]

        sink = "NUL" if os.name == "nt" else "/dev/null"
        cmd = [
            ffmpeg_exe,
            "-hide_banner",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=128x128:r=30:d=0.2",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            encoder_name,
            "-t",
            "0.2",
            "-f",
            "null",
            sink,
        ]

        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                timeout=8,
                stdin=subprocess.DEVNULL,
                creationflags=self.get_creationflags(),
            )
            out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
            if r.returncode == 0:
                result = (True, "")
            else:
                hint = out.splitlines()[-1] if out else f"exit {r.returncode}"
                result = (False, hint)
        except Exception as e:
            result = (False, str(e))

        self._ffmpeg_encoder_probe_cache[key] = result
        return result

    def _pick_video_encoder(self, ffmpeg_exe):
        if not ffmpeg_exe or not os.path.exists(ffmpeg_exe):
            return ("libx264", [], "")

        if not self.is_hwaccel_enabled():
            return ("libx264", [], "")

        vendor = self._get_gpu_vendor()
        candidates = []

        if vendor == "nvidia":
            candidates = ["h264_nvenc", "h264_qsv", "h264_amf"]
        elif vendor == "intel":
            candidates = ["h264_qsv", "h264_nvenc", "h264_amf"]
        elif vendor == "amd":
            candidates = ["h264_amf", "h264_nvenc", "h264_qsv"]
        else:
            candidates = ["h264_nvenc", "h264_qsv", "h264_amf"]

        last_error = ""
        for enc in candidates:
            usable, hint = self._probe_ffmpeg_encoder(ffmpeg_exe, enc)
            if usable:
                return (enc, [], "")
            if hint:
                last_error = f"{enc}: {hint}"

        return ("libx264", [], last_error)

    def _build_transcode_cmd(self, ffmpeg_exe, input_file, output_file, prefer_hw=True):
        base = [
            ffmpeg_exe,
            "-hide_banner",
            "-nostdin",
            "-i",
            input_file,
        ]

        if prefer_hw:
            encoder, extra, note = self._pick_video_encoder(ffmpeg_exe)
        else:
            encoder, extra = ("libx264", [])
            note = ""

        if encoder == "libx264":
            video_args = ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"]
        else:
            video_args = ["-c:v", encoder] + extra

        audio_args = ["-c:a", "aac", "-b:a", "192k"]
        container_args = ["-movflags", "+faststart", "-threads", "0", "-y", output_file]
        return base + video_args + audio_args + container_args, encoder, note
    
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
        self.stop_event.set()
        self.log("正在终止任务（下载/合并/转码）...")

        def kill_tree(proc):
            if not proc:
                return
            try:
                if proc.poll() is not None:
                    return
            except Exception:
                return

            if os.name == "nt":
                try:
                    pid = proc.pid
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=5,
                        creationflags=self.get_creationflags(),
                    )
                except Exception:
                    pass
            else:
                try:
                    proc.terminate()
                except Exception:
                    pass

            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        kill_tree(self.transcode_process)
        kill_tree(self.current_process)

        self.log("已发送终止信号")
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
    
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

    def _try_get_direct_url(self, url, format_selector):
        try:
            cmd = [
                self.yt_dlp_path,
                "-f",
                format_selector,
                "-g",
                "--no-playlist",
                url,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                creationflags=self.get_creationflags(),
            )
            if result.returncode != 0:
                return []
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return lines
        except Exception:
            return []
    
    def resolve_url(self, url):
        self.log("正在解析视频地址...")
        try:
            cmd = [self.yt_dlp_path, "--flat-playlist", "--get-id", url]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                creationflags=self.get_creationflags(),
            )
            
            if result.returncode == 0:
                ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                is_playlist = len(ids) > 1
                self.log(f"解析成功: {url}")
                if is_playlist:
                    self.log(f"检测到播放列表，包含 {len(ids)} 个视频")
                    self._set_resolved_url(url, is_direct=False)
                    return True

                direct_lines = self._try_get_direct_url(url, "b[ext=mp4]/b")
                if not direct_lines:
                    direct_lines = self._try_get_direct_url(url, "bv*+ba/b")

                if direct_lines:
                    if len(direct_lines) == 1:
                        self._set_resolved_url(direct_lines[0], is_direct=True)
                        self.log("解析到合并直链（可能清晰度较低）")
                    else:
                        self._set_resolved_url(direct_lines[0], is_direct=True)
                        self.log("检测到分离的音视频直链，已填入视频直链，音频直链见日志")
                        for idx, link in enumerate(direct_lines, 1):
                            self.log(f"直链{idx}: {link}")
                else:
                    self._set_resolved_url(url, is_direct=False)
                return True
            else:
                cmd = [self.yt_dlp_path, "--dump-json", "--max-downloads", "1", url]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    encoding=self.get_subprocess_encoding(),
                    errors="replace",
                    creationflags=self.get_creationflags(),
                )
                
                if result.returncode == 0:
                    self.log(f"解析成功: {url}")
                    direct_lines = self._try_get_direct_url(url, "b[ext=mp4]/b")
                    if not direct_lines:
                        direct_lines = self._try_get_direct_url(url, "bv*+ba/b")

                    if direct_lines:
                        if len(direct_lines) == 1:
                            self._set_resolved_url(direct_lines[0], is_direct=True)
                            self.log("解析到合并直链（可能清晰度较低）")
                        else:
                            self._set_resolved_url(direct_lines[0], is_direct=True)
                            self.log("检测到分离的音视频直链，已填入视频直链，音频直链见日志")
                            for idx, link in enumerate(direct_lines, 1):
                                self.log(f"直链{idx}: {link}")
                    else:
                        self._set_resolved_url(url, is_direct=False)
                    return True
                else:
                    self.log(f"解析失败，但将尝试直接下载: {result.stderr}")
                    self._set_resolved_url(url, is_direct=False)
                    return True
        except Exception as e:
            self.log(f"解析错误，将尝试直接下载: {str(e)}")
            self._set_resolved_url(url, is_direct=False)
            return True
    
    def convert_to_mp4(self, input_file):
        self.log(f"正在转换文件: {input_file}")

        input_ext = os.path.splitext(input_file)[1].lower()
        if input_ext in ('.mp3', '.wav', '.m4a'):
            self.log(f"跳过转换（音频文件）: {input_file}")
            return input_file

        output_file = os.path.splitext(input_file)[0] + ".mp4"
        
        try:
            ffmpeg_exe = self.get_ffmpeg_executable()
            if not ffmpeg_exe:
                self.log("未找到 ffmpeg，跳过转换；请将 ffmpeg.exe 放到程序同目录或安装到 PATH。")
                return input_file

            prefer_hw = self.is_hwaccel_enabled()
            cmd, encoder, note = self._build_transcode_cmd(ffmpeg_exe, input_file, output_file, prefer_hw=prefer_hw)
            last_cmd = cmd
            if prefer_hw:
                if encoder != "libx264":
                    self.log(f"转码：使用硬件编码器 {encoder}（失败将回退 CPU）")
                else:
                    if note:
                        self.log(f"转码：硬件编码不可用（{note}），使用 CPU（libx264）")
                    else:
                        self.log("转码：未检测到可用硬件编码器，使用 CPU（libx264）")
            else:
                self.log("转码：已禁用硬件编码（YTD_HWACCEL=0）")
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                stdin=subprocess.DEVNULL,
                creationflags=self.get_creationflags(),
                startupinfo=self.get_startupinfo(),
            )
            self.transcode_process = proc
            
            for line in proc.stdout:
                if self.stop_event.is_set():
                    break
                if self.is_debug:
                    self.log(line.strip())
                import time
                time.sleep(0.001)
            
            if self.stop_event.is_set():
                try:
                    proc.kill()
                except Exception:
                    pass
                return input_file

            proc.wait()
            
            if proc.returncode != 0 and prefer_hw and encoder != "libx264":
                self.log("硬件转码失败，正在回退 CPU（libx264）重试...")
                cpu_cmd, _, _ = self._build_transcode_cmd(ffmpeg_exe, input_file, output_file, prefer_hw=False)
                last_cmd = cpu_cmd
                proc = subprocess.Popen(
                    cpu_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding=self.get_subprocess_encoding(),
                    errors="replace",
                    stdin=subprocess.DEVNULL,
                    creationflags=self.get_creationflags(),
                    startupinfo=self.get_startupinfo(),
                )
                self.transcode_process = proc
                for line in proc.stdout:
                    if self.stop_event.is_set():
                        break
                    if self.is_debug:
                        self.log(line.strip())
                    import time
                    time.sleep(0.001)
                if self.stop_event.is_set():
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return input_file
                proc.wait()

            if proc.returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode=proc.returncode,
                    cmd=' '.join(last_cmd)
                )
            
            if os.path.exists(output_file):
                os.remove(input_file)
                return output_file
            else:
                return input_file
        except Exception as e:
            self.log(f"转换失败: {str(e)}")
            return input_file
        finally:
            self.transcode_process = None
    
    def start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入下载链接")
            return

        self.stop_event.clear()
        self._set_resolved_url("", is_direct=False)
        
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def download_thread():
            try:
                if not self.resolve_url(url):
                    self.download_btn.config(state=tk.NORMAL)
                    return

                ffmpeg_exe = self.get_ffmpeg_executable()
                if not ffmpeg_exe:
                    self.log("警告: 未找到 ffmpeg；下载可能无法合并/转码。建议将 ffmpeg.exe 放到程序同目录或安装到 PATH。")

                if self.is_hwaccel_enabled():
                    vendor = self._get_gpu_vendor()
                    if vendor:
                        self.log(f"检测到显卡类型: {vendor}（将尝试硬件编码加速转码）")
                    else:
                        self.log("未能识别显卡类型（将尝试自动探测 ffmpeg 硬件编码器）")
                
                cmd = [
                    self.yt_dlp_path,
                    "-o", os.path.join(self.download_path, "%(title)s.%(ext)s"),
                    "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                    "--ignore-errors",
                    "--no-warnings",
                    "--newline",
                    "--concurrent-fragments", "10",
                    "--fragment-retries", "10",
                    "--retries", "5",
                    "--buffer-size", "16K",
                ]

                if ffmpeg_exe:
                    cmd.extend(["--ffmpeg-location", ffmpeg_exe])
                
                if self.is_debug:
                    cmd.append("-v")
                
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
                    encoding=self.get_subprocess_encoding(),
                    errors="replace",
                    stdin=subprocess.DEVNULL,
                    bufsize=1,
                    creationflags=self.get_creationflags(),
                    startupinfo=startupinfo
                )
                proc = self.current_process
                
                output = []
                downloaded_paths = set()
                downloaded_re = re.compile(r'^\[download\]\s+(.+?)\s+has already been downloaded\s*$')
                destination_re = re.compile(r'^\[download\]\s+Destination:\s+(.+?)\s*$')
                while True:
                    if self.stop_event.is_set():
                        break
                    line = proc.stdout.readline()
                    if not line:
                        break
                    stripped_line = line.strip()
                    if self.is_debug:
                        self.log(stripped_line)
                    output.append(stripped_line)

                    m = downloaded_re.match(stripped_line)
                    if m:
                        downloaded_paths.add(m.group(1))
                    else:
                        m = destination_re.match(stripped_line)
                        if m:
                            downloaded_paths.add(m.group(1))
                    
                    if "Invoking http downloader on" in stripped_line:
                        try:
                            url_match = re.search(r'(https://[^"\s`]+)', stripped_line)
                            if url_match:
                                if not self.resolved_is_direct:
                                    direct_url = url_match.group(1).strip('"`')
                                    self._set_resolved_url(direct_url, is_direct=True)
                                    self.log(f"提取到真实下载地址: {self.resolved_url}")
                        except Exception as e:
                            self.log(f"提取真实地址出错: {str(e)}")
                    
                    import time
                    time.sleep(0.001)
                
                proc.wait()

                if self.stop_event.is_set():
                    self.log("任务已终止")
                    return
                
                if proc.returncode != 0:
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
                            returncode=proc.returncode,
                            cmd=' '.join(cmd),
                            output=output_str
                        )
                
                downloaded_files = []
                for file in os.listdir(self.download_path):
                    if file.endswith(('.mp4', '.webm', '.mkv', '.flv', '.avi', '.mp3', '.wav', '.m4a')):
                        file_path = os.path.join(self.download_path, file)
                        if (datetime.now().timestamp() - os.path.getctime(file_path)) < 300:
                            downloaded_files.append(file_path)

                for p in downloaded_paths:
                    p = p.strip().strip('"')
                    if os.path.isabs(p) and os.path.exists(p):
                        downloaded_files.append(p)

                downloaded_files = list(dict.fromkeys(downloaded_files))
                
                converted_files = []
                for file_path in downloaded_files:
                    if self.stop_event.is_set():
                        break
                    if not file_path.lower().endswith('.mp4'):
                        converted_file = self.convert_to_mp4(file_path)
                        converted_files.append(converted_file)
                    else:
                        converted_files.append(file_path)

                if self.stop_event.is_set():
                    self.log("任务已终止")
                    return
                
                if not converted_files:
                    self.log("任务已结束：未发现新下载文件（可能文件已存在且未更新创建时间）。")

                total_files = len(converted_files)
                if total_files:
                    self.log(f"成功下载 {total_files} 个文件")
                message = f"已处理完成\n点击'是'打开下载文件夹，'否'关闭提示"
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
                if self.current_process is not None:
                    try:
                        if self.current_process.poll() is not None:
                            self.current_process = None
                    except Exception:
                        self.current_process = None
        
        threading.Thread(target=download_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloader(root)
    root.mainloop()
