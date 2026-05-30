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
import urllib.request
import json
import hashlib
import base64
import time
import random
import string
from urllib.parse import urlencode, urlparse
from http.cookiejar import CookieJar

class XBogus:
    def __init__(self, user_agent=None):
        self._array = [
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, 10, 11, 12, 13, 14, 15
        ]
        self._character = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
        self._ua_key = b"\x00\x01\x0c"
        self._user_agent = (
            user_agent if user_agent else
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        )

    @property
    def user_agent(self):
        return self._user_agent

    def _md5_str_to_array(self, md5_str):
        if isinstance(md5_str, str) and len(md5_str) > 32:
            return [ord(char) for char in md5_str]
        array = []
        idx = 0
        while idx < len(md5_str):
            array.append((self._array[ord(md5_str[idx])] << 4) | self._array[ord(md5_str[idx + 1])])
            idx += 2
        return array

    def _md5(self, input_data):
        if isinstance(input_data, str):
            data = self._md5_str_to_array(input_data)
        else:
            data = input_data
        md5_hash = hashlib.md5()
        md5_hash.update(bytes(data))
        return md5_hash.hexdigest()

    def _md5_encrypt(self, url_path):
        hashed = self._md5(self._md5_str_to_array(self._md5(url_path)))
        return self._md5_str_to_array(hashed)

    def _encoding_conversion(self, a, b, c, e, d, t, f, r, n, o, i, _, x, u, s, l, v, h, p):
        payload = [a]
        payload.append(int(i))
        payload.extend([b, _, c, x, e, u, d, s, t, l, f, v, r, h, n, p, o])
        return bytes(payload).decode("ISO-8859-1")

    def _encoding_conversion2(self, a, b, c):
        return chr(a) + chr(b) + c

    @staticmethod
    def _rc4_encrypt(key, data):
        s = list(range(256))
        j = 0
        encrypted = bytearray()
        for i in range(256):
            j = (j + s[i] + key[i % len(key)]) % 256
            s[i], s[j] = s[j], s[i]
        i = j = 0
        for byte in data:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            encrypted.append(byte ^ s[(s[i] + s[j]) % 256])
        return encrypted

    def _calculation(self, a1, a2, a3):
        x3 = ((a1 & 255) << 16) | ((a2 & 255) << 8) | (a3 & 255)
        return (
            self._character[(x3 & 16515072) >> 18]
            + self._character[(x3 & 258048) >> 12]
            + self._character[(x3 & 4032) >> 6]
            + self._character[x3 & 63]
        )

    def build(self, url):
        ua_md5_array = self._md5_str_to_array(
            self._md5(
                base64.b64encode(
                    self._rc4_encrypt(self._ua_key, self._user_agent.encode("ISO-8859-1"))
                ).decode("ISO-8859-1")
            )
        )
        empty_md5_array = self._md5_str_to_array(
            self._md5(self._md5_str_to_array("d41d8cd98f00b204e9800998ecf8427e"))
        )
        url_md5_array = self._md5_encrypt(url)
        timer = int(time.time())
        ct = 536919696
        new_array = [
            64, 0.00390625, 1, 12,
            url_md5_array[14], url_md5_array[15],
            empty_md5_array[14], empty_md5_array[15],
            ua_md5_array[14], ua_md5_array[15],
            timer >> 24 & 255, timer >> 16 & 255, timer >> 8 & 255, timer & 255,
            ct >> 24 & 255, ct >> 16 & 255, ct >> 8 & 255, ct & 255,
        ]
        xor_result = new_array[0]
        for value in new_array[1:]:
            if isinstance(value, float):
                value = int(value)
            xor_result ^= value
        new_array.append(xor_result)
        array3 = []
        array4 = []
        idx = 0
        while idx < len(new_array):
            value = new_array[idx]
            array3.append(value)
            if idx + 1 < len(new_array):
                array4.append(new_array[idx + 1])
            idx += 2
        merged = array3 + array4
        garbled = self._encoding_conversion2(
            2, 255,
            self._rc4_encrypt(
                "ÿ".encode("ISO-8859-1"),
                self._encoding_conversion(*merged).encode("ISO-8859-1"),
            ).decode("ISO-8859-1"),
        )
        xb = ""
        idx = 0
        while idx < len(garbled):
            xb += self._calculation(ord(garbled[idx]), ord(garbled[idx + 1]), ord(garbled[idx + 2]))
            idx += 3
        signed_url = f"{url}&X-Bogus={xb}"
        return signed_url, xb, self._user_agent


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
        self._ytdlp_ready = threading.Event()
        
        self.yt_dlp_path = self.resolve_ytdlp_path()
        self.ffmpeg_path = self.resolve_ffmpeg_path()
        self.deno_path = self.resolve_deno_path()
        
        self.create_widgets()
        
        self.root.after(100, self._process_log_queue)
        
        threading.Thread(target=self._init_tools_background, daemon=True).start()

    _DOUYIN_HOSTS = (
        "douyin.com", "www.douyin.com", "v.douyin.com",
        "v.iesdouyin.com", "iesdouyin.com", "live.douyin.com",
    )
    _DOUYIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    _douyin_cookies = None

    def _extract_url_from_text(self, text):
        urls = re.findall(r'https?://[^\s<>"\'`]+', text)
        if not urls:
            return text.strip()
        for u in urls:
            u = u.rstrip('.,;:!?)')
            try:
                parsed = urlparse(u)
                host = (parsed.netloc or "").lower()
                for dh in self._DOUYIN_HOSTS:
                    if host == dh or host.endswith("." + dh):
                        return u
            except Exception:
                continue
        return urls[0].rstrip('.,;:!?)')

    def is_douyin_url(self, url):
        try:
            parsed = urlparse(url)
            host = (parsed.netloc or "").lower()
            for dh in self._DOUYIN_HOSTS:
                if host == dh or host.endswith("." + dh):
                    return True
        except Exception:
            pass
        if re.search(r'v\.douyin\.com/\w+', url):
            return True
        if re.search(r'https?://[^\s]*douyin\.com[^\s]*', url):
            return True
        return False

    def _douyin_resolve_short_url(self, short_url):
        if not short_url.lower().startswith(("http://", "https://")):
            short_url = "https://" + short_url
        try:
            req = urllib.request.Request(short_url, method="GET")
            req.add_header("User-Agent", self._DOUYIN_UA)
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
            resp = opener.open(req, timeout=10)
            return resp.url
        except Exception as e:
            self.log(f"抖音短链解析失败: {e}")
            return short_url

    def _douyin_extract_video_id(self, url):
        m = re.search(r"/video/(\d+)", url)
        if m:
            return m.group(1)
        m = re.search(r"modal_id=(\d+)", url)
        if m:
            return m.group(1)
        m = re.search(r"/note/(\d+)", url)
        if m:
            return m.group(1)
        return None

    def _douyin_gen_false_ms_token(self):
        return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(182)) + "=="

    def _douyin_default_query(self, ms_token=""):
        if not ms_token:
            ms_token = self._douyin_gen_false_ms_token()
        return {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "update_version_code": "170400",
            "pc_client_type": "1",
            "pc_libra_divert": "Windows",
            "version_code": "290100",
            "version_name": "29.1.0",
            "cookie_enabled": "true",
            "screen_width": "1536",
            "screen_height": "864",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "139.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "139.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "16",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "200",
            "support_h265": "1",
            "support_dash": "1",
            "uifid": "",
            "msToken": ms_token,
        }

    _DOUYIN_BUILTIN_COOKIES = """# Netscape HTTP Cookie File
.douyin.com	TRUE	/	TRUE	1814716717	enter_pc_once	1
.douyin.com	TRUE	/	TRUE	1809778556	UIFID_TEMP	ed3eadd74fe8fd7fe8cc39b2f8425a87324d41d3f6a0cfdc014da4c26c654051065d72af61505a404a3eb5e32a10024eaf2509626757a6b7ad6b62871bffde1e35cc21bd2bd59bf7d819651a72bb8df068a018907fbaa11b08ff10ea30129f81
www.douyin.com	FALSE	/	FALSE	1780402560	s_v_web_id	verify_mnivanp0_7j02PMZo_sqPD_4SuM_9tP8_rOv7z4XI8Qmj
.douyin.com	TRUE	/	FALSE	1814716719	hevc_supported	true
.douyin.com	TRUE	/	FALSE	1780761521	is_dash_user	1
www.douyin.com	FALSE	/	TRUE	1809778562	fpk1	U2FsdGVkX1+VGt6i0I5pK/QSw3JVtKz44ikHPauWbIeLQ81lQomiqfSmAl+o5a4YohcXNPNYe17Jf930S94iBQ==
www.douyin.com	FALSE	/	TRUE	1809778562	fpk2	91e1a2a41c0741f7f47615ab9de2fb8a
.douyin.com	TRUE	/	TRUE	1780402564	passport_csrf_token	9b7d7ff2d272c1d977a3e46d61b8ceb4
.douyin.com	TRUE	/	FALSE	1780402564	passport_csrf_token_default	9b7d7ff2d272c1d977a3e46d61b8ceb4
.douyin.com	TRUE	/	FALSE	1785340719	bd_ticket_guard_client_web_domain	2
.douyin.com	TRUE	/	TRUE	1809778577	passport_assist_user	CkElDtFokN6RsTh1ucDyoI-skfPEjTG9AmIUW7m7civJ-4t5PjzYy7Obnc3Ul9Q1GTn9uF5_WE727gByVwE9rG5-UxpKCjwAAAAAAAAAAAAAUEIGUbf9xkjoiKiXATGnTQQvp4up3_yNgYlG7cow4US9MBB2h-kIVD064eomBVlSHcwQ1uuNDhiJr9ZUIAEiAQN5uown
.douyin.com	TRUE	/	FALSE	1785586577	n_mh	9H_yvogdptrUfobKuiDagDqZlsbMXdgxuxwLD4LWIMQ
.douyin.com	TRUE	/	TRUE	1784555795	uid_tt	aa75aefd304049c21a45c1952d1e1d63
.douyin.com	TRUE	/	TRUE	1784555795	uid_tt_ss	aa75aefd304049c21a45c1952d1e1d63
.douyin.com	TRUE	/	TRUE	1784555795	sid_tt	55dfd0903f47313a4af2704dde361c88
.douyin.com	TRUE	/	TRUE	1784555795	sessionid	55dfd0903f47313a4af2704dde361c88
.douyin.com	TRUE	/	TRUE	1784555795	sessionid_ss	55dfd0903f47313a4af2704dde361c88
.douyin.com	TRUE	/	TRUE	1784555795	sid_guard	55dfd0903f47313a4af2704dde361c88%7C1779371795%7C5184000%7CMon%2C+20-Jul-2026+13%3A56%3A35+GMT
.douyin.com	TRUE	/	TRUE	1784555795	sid_ucp_v1	1.0.0-KDJjYTQ1NzdhOWE4MjAwM2M3YTZlODQ4YzA4NzM5MWI4MWU2ZWU3ZmYKIQjk0NCJkczpARCTnrzQBhjvMSAMMJ2nxLAGOAdA9AdIBBoCbHEiIDU1ZGZkMDkwM2Y0NzMxM2E0YWYyNzA0ZGRlMzYxYzg4
.douyin.com	TRUE	/	TRUE	1784555795	ssid_ucp_v1	1.0.0-KDJjYTQ1NzdhOWE4MjAwM2M3YTZlODQ4YzA4NzM5MWI4MWU2ZWU3ZmYKIQjk0NCJkczpARCTnrzQBhjvMSAMMJ2nxLAGOAdA9AdIBBoCbHEiIDU1ZGZkMDkwM2Y0NzMxM2E0YWYyNzA0ZGRlMzYxYzg4
.douyin.com	TRUE	/	FALSE	1806842656	d_ticket	36b86ccdfde731f5f83f6cab7591f5bff7d72
.douyin.com	TRUE	/	FALSE	1811692726	odin_tt	646ba2e4fc3935e1b2b614b9c12d25b380a85b536e23aab065ef238c5762fcf4044c7885333c968ddd0b123d95bf214e793515b86c85d7cb11ea8f19f67f262005e4cdcb620d27c8818ca12db1123f56
.douyin.com	TRUE	/	TRUE	1811260717	ttwid	1%7CZgqhiL5yJvJoiMobdE6j1E94K0RcFz4OtUKuxl1KDvQ%7C1780107272%7C3da01d1cf9bad400d3dd4f371a13779abf8a29bfe01d6c85a51adb28f97caa05
.douyin.com	TRUE	/	TRUE	1809778577	UIFID	ed3eadd74fe8fd7fe8cc39b2f8425a87324d41d3f6a0cfdc014da4c26c654051065d72af61505a404a3eb5e32a10024ef846163fc69a25eb883f9a407975e5bba4e463a62788790d76a54d468b5cdb5479f9c9e27808f373ca4d829c3416f31f62290ea00c8e931648aa84bf72e9e210c71e8bf111d60c97cee7eb9f85457c5d451a56610e15eddd879ae265a2be57127a51f0eb8d7b45ae5e0e62cc8086cf74f5a7d5e67c96b71d0a3c9b5594ace75f
.douyin.com	TRUE	/	FALSE	1785340719	bd_ticket_guard_client_data	eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCSWYyOFprRDBmclFMYTgxUEEvT1JBYmJNS243UnoxRm53cUIvWEZ5WVRTZHBYU3hUalhzNmFFK2sybm5Lbkh6eEx4cTdBRStDN1BPVmtzeGIzci9TTHM9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D
"""

    def _douyin_parse_cookie_file(self, content):
        cookies = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                if name and value:
                    cookies[name] = value
        return cookies

    def _douyin_fetch_cookies(self):
        if self._douyin_cookies:
            return self._douyin_cookies

        cookies = self._douyin_parse_cookie_file(self._DOUYIN_BUILTIN_COOKIES)
        if cookies:
            self.log(f"已加载内置抖音Cookie ({len(cookies)}项)")
            self._douyin_cookies = cookies
            return cookies

        try:
            cookie_jar = CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
            ttwid_payload = json.dumps({
                "region": "cn",
                "aid": 1768,
                "needFid": False,
                "service": "www.douyin.com",
                "migrate_info": {"ticket": "", "source": "node"},
                "cbUrlProtocol": "https",
                "union": True,
            }).encode("utf-8")
            req2 = urllib.request.Request(
                "https://ttwid.bytedance.com/ttwid/union/register/",
                data=ttwid_payload,
                method="POST",
            )
            req2.add_header("User-Agent", self._DOUYIN_UA)
            req2.add_header("Content-Type", "application/json")
            resp2 = opener.open(req2, timeout=10)
            cookies = {}
            for cookie in cookie_jar:
                cookies[cookie.name] = cookie.value
            set_cookies = resp2.headers.get_all("Set-Cookie") if hasattr(resp2.headers, "get_all") else []
            for hdr in (set_cookies or []):
                for part in hdr.split(","):
                    part = part.strip()
                    if part.startswith("ttwid="):
                        val = part.split(";")[0].split("=", 1)[1]
                        cookies["ttwid"] = val
            self.log(f"自动获取抖音Cookie: {', '.join(cookies.keys())}")
            self._douyin_cookies = cookies
            return cookies
        except Exception as e:
            self.log(f"获取抖音Cookie失败: {e}")
            return {}

    def _douyin_generate_cookie_file(self):
        cookies = self._douyin_fetch_cookies()
        if not cookies:
            return None
        cookie_file = os.path.join(tempfile.gettempdir(), "ytd_douyin_cookies.txt")
        try:
            with open(cookie_file, "w") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for name, value in cookies.items():
                    f.write(f".douyin.com\tTRUE\t/\tFALSE\t0\t{name}\t{value}\n")
            return cookie_file
        except Exception:
            return None

    def _douyin_get_real_mstoken(self):
        try:
            conf_url = "https://raw.githubusercontent.com/Johnserf-Seed/f2/main/f2/conf/conf.yaml"
            req = urllib.request.Request(conf_url)
            req.add_header("User-Agent", self._DOUYIN_UA)
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
            import importlib
            yaml_mod = None
            try:
                yaml_mod = importlib.import_module("yaml")
            except ImportError:
                pass
            if yaml_mod:
                data = yaml_mod.safe_load(raw) or {}
                ms_conf = data.get("f2", {}).get("douyin", {}).get("msToken", {})
                required = {"url", "magic", "version", "dataType", "ulr", "strData"}
                if required.issubset(ms_conf.keys()):
                    payload = json.dumps({
                        "magic": ms_conf["magic"],
                        "version": ms_conf["version"],
                        "dataType": ms_conf["dataType"],
                        "strData": ms_conf["strData"],
                        "ulr": ms_conf["ulr"],
                        "tspFromClient": int(time.time() * 1000),
                    }).encode("utf-8")
                    req2 = urllib.request.Request(ms_conf["url"], data=payload, method="POST")
                    req2.add_header("Content-Type", "application/json; charset=utf-8")
                    req2.add_header("User-Agent", self._DOUYIN_UA)
                    with urllib.request.urlopen(req2, timeout=15) as resp2:
                        from http.cookies import SimpleCookie
                        set_cookies = resp2.headers.get_all("Set-Cookie") if hasattr(resp2.headers, "get_all") else []
                        for hdr in (set_cookies or []):
                            sc = SimpleCookie()
                            sc.load(hdr)
                            morsel = sc.get("msToken")
                            if morsel and morsel.value and len(morsel.value.strip()) in (164, 184):
                                return morsel.value.strip()
        except Exception:
            pass
        return ""

    def _douyin_get_video_detail(self, aweme_id):
        cookies = self._douyin_fetch_cookies()

        real_ms = self._douyin_get_real_mstoken()
        if real_ms:
            cookies["msToken"] = real_ms
            self.log("已获取真实msToken")

        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items()) if cookies else ""

        signer = XBogus(self._DOUYIN_UA)
        headers = {
            "User-Agent": self._DOUYIN_UA,
            "Referer": "https://www.douyin.com/?recommend=1",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if cookie_str:
            headers["Cookie"] = cookie_str

        delays = [1, 2, 5]
        for aid in ("6383", "1128"):
            for attempt in range(3):
                params = self._douyin_default_query(cookies.get("msToken", ""))
                params["aweme_id"] = aweme_id
                params["aid"] = aid
                query = urlencode(params)
                base_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?{query}"
                signed_url, _, ua = signer.build(base_url)
                req_headers = {**headers, "User-Agent": ua}
                req = urllib.request.Request(signed_url, method="GET", headers=req_headers)
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        raw = resp.read()
                        if not raw:
                            self.log(f"抖音API返回空响应(aid={aid}, 尝试{attempt+1}/3)，可能被反爬...")
                            if attempt < 2:
                                time.sleep(delays[attempt])
                            continue
                        try:
                            import gzip
                            raw = gzip.decompress(raw)
                        except Exception:
                            pass
                        try:
                            data = json.loads(raw.decode("utf-8"))
                        except json.JSONDecodeError:
                            self.log(f"抖音API返回非JSON内容(aid={aid}, 长度={len(raw)})")
                            break
                        detail = data.get("aweme_detail")
                        if detail:
                            return detail
                        self.log(f"抖音API无视频详情(aid={aid}, status_code={data.get('status_code')})")
                        break
                except Exception as e:
                    self.log(f"抖音API请求失败(aid={aid}, 尝试{attempt+1}/3): {e}")
                    if attempt < 2:
                        time.sleep(delays[attempt])
                    continue
        return None

    def _douyin_extract_no_watermark_url(self, aweme_data):
        video = aweme_data.get("video", {})
        play_addr = video.get("play_addr", {})
        bit_rates = video.get("bit_rate")
        if isinstance(bit_rates, list) and bit_rates:
            entries = []
            for entry in bit_rates:
                if not isinstance(entry, dict):
                    continue
                pa = entry.get("play_addr")
                if not isinstance(pa, dict):
                    continue
                try:
                    br = int(entry.get("bit_rate") or 0)
                except (TypeError, ValueError):
                    br = 0
                width = int(pa.get("width") or entry.get("width") or 0)
                entries.append((br, width, pa))
            if entries:
                entries.sort(key=lambda t: (-t[0], -t[1]))
                play_addr = entries[0][2]

        url_list = play_addr.get("url_list") or []
        url_list.sort(key=lambda u: 0 if "watermark=0" in u else 1)

        signer = XBogus(self._DOUYIN_UA)
        for candidate in url_list:
            parsed = urlparse(candidate)
            wm_hints = ("tplv-dy-water", "dy-water", "owner_watermark", "watermark_image", "watermark=1", "playwm")
            is_wm = any(h in candidate.lower() for h in wm_hints)
            if is_wm:
                continue
            if parsed.netloc.endswith("douyin.com"):
                if "X-Bogus=" not in candidate:
                    signed_url, _, ua = signer.sign_url(candidate) if hasattr(signer, 'sign_url') else signer.build(candidate)
                    return signed_url, ua
                return candidate, self._DOUYIN_UA
            return candidate, self._DOUYIN_UA

        for candidate in url_list:
            parsed = urlparse(candidate)
            if parsed.netloc.endswith("douyin.com"):
                if "X-Bogus=" not in candidate:
                    signed_url, _, ua = signer.build(candidate)
                    return signed_url, ua
                return candidate, self._DOUYIN_UA
            return candidate, self._DOUYIN_UA

        uri = play_addr.get("uri") or video.get("vid") or video.get("download_addr", {}).get("uri")
        if uri:
            params = {
                "video_id": uri,
                "ratio": "1080p",
                "line": "0",
                "is_play_url": "1",
                "watermark": "0",
                "source": "PackSourceEnum_PUBLISH",
            }
            query = urlencode(params)
            base_url = f"https://www.douyin.com/aweme/v1/play/?{query}"
            signed_url, _, ua = signer.build(base_url)
            return signed_url, ua

        return None, None

    def _douyin_detect_media_type(self, aweme_data):
        if (aweme_data.get("image_post_info")
            or aweme_data.get("images")
            or aweme_data.get("image_list")):
            return "gallery"
        aweme_type = aweme_data.get("aweme_type")
        if isinstance(aweme_type, int) and aweme_type in (2, 68, 150):
            return "gallery"
        return "video"

    def _douyin_collect_image_urls(self, aweme_data):
        urls = []
        image_post = aweme_data.get("image_post_info")
        items = []
        if isinstance(image_post, dict):
            for key in ("images", "image_list"):
                candidate = image_post.get(key)
                if isinstance(candidate, list) and candidate:
                    items = candidate
                    break
        if not items:
            items = aweme_data.get("images") or aweme_data.get("image_list") or []
        for item in items:
            if not isinstance(item, dict):
                continue
            for src_key in ("watermark_free_download_url_list", "origin_image",
                            "display_image", "download_url", "download_addr", "download_url_list"):
                source = item.get(src_key)
                url = self._douyin_extract_first_url(source)
                if url:
                    urls.append(url)
                    break
        return urls

    def _douyin_extract_first_url(self, source):
        if isinstance(source, dict):
            url_list = source.get("url_list") or source.get("urlList")
            if isinstance(url_list, list):
                for u in url_list:
                    if isinstance(u, str) and u:
                        return u
        elif isinstance(source, list):
            for u in source:
                if isinstance(u, str) and u:
                    return u
        elif isinstance(source, str) and source:
            return source
        return None

    def _douyin_sanitize_filename(self, filename, max_length=80):
        filename = filename.replace("\n", " ").replace("\r", " ")
        filename = re.sub(r'[<>:"/\\|?*#\x00-\x1f]', "_", filename)
        filename = re.sub(r"_+", "_", filename)
        filename = re.sub(r" +", " ", filename)
        filename = filename.strip("._- ")
        if len(filename) > max_length:
            filename = filename[:max_length].rstrip("._- ")
        return filename or "untitled"

    def _douyin_download_file(self, url, save_path, ua=None):
        headers = {
            "User-Agent": ua or self._DOUYIN_UA,
            "Referer": "https://www.douyin.com/",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Origin": "https://www.douyin.com",
        }
        cookies = self._douyin_cookies or {}
        if cookies:
            headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
        req = urllib.request.Request(url, method="GET", headers=headers)
        tmp_path = None
        try:
            save_dir = os.path.dirname(save_path)
            os.makedirs(save_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=save_dir)
            os.close(fd)
            with urllib.request.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                last_pct = -1
                with open(tmp_path, "wb") as f:
                    while True:
                        if self.stop_event.is_set():
                            self.log("下载已取消")
                            return False
                        chunk = resp.read(262144)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded * 100 // total
                            if pct >= last_pct + 5:
                                self.log(f"下载进度: {pct}% ({downloaded // 1024}KB / {total // 1024}KB)")
                                last_pct = pct
                        elif downloaded % (5 * 1024 * 1024) < 262144:
                            self.log(f"已下载: {downloaded // 1024}KB")
            for old in (save_path, save_path + ".tmp"):
                try:
                    if os.path.exists(old):
                        os.remove(old)
                except Exception:
                    pass
            os.replace(tmp_path, save_path)
            tmp_path = None
            return True
        except Exception as e:
            self.log(f"抖音文件下载失败: {e}")
            return False
        finally:
            if tmp_path:
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass

    def douyin_download(self, url):
        self.log("检测到抖音链接，使用无头浏览器抓取...")

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.log("未安装 Playwright，无法使用抖音专用下载")
            return False

        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        short_hosts = ("v.douyin.com", "v.iesdouyin.com", "iesdouyin.com")
        if any(host == h or host.endswith("." + h) for h in short_hosts) or re.search(r'v\.douyin\.com/\w+', url):
            self.log("正在解析抖音短链...")
            url = self._douyin_resolve_short_url(url)
            self.log(f"解析后地址: {url}")

        video_urls = []
        audio_urls = []
        page_title = ""

        cdn_hosts = (
            "douyinvod.com", "bytevcloudtp.com", "bytecdn.cn",
            "douyincdn.com", "byteimg.com", "volcvod.com",
            "bdurl.net", "pstatp.com", "snssdk.com",
            "amemv.com", "ixigua.com", "tiktokcdn.com",
            "365yg.com", "zjcdn.com", "zijieapi.com",
            "bytegoofy.com", "ibytedtos.com", "bytetcc.com",
            "bytednsdoc.com", "bytedance.com", "toutiao.com",
        )

        try:
            self.log("启动无头浏览器...")
            with sync_playwright() as p:
                browser = None
                for ch in ("chrome", "msedge", "chromium"):
                    try:
                        browser = p.chromium.launch(headless=True, channel=ch)
                        self.log(f"已启动浏览器: {ch}")
                        break
                    except Exception:
                        continue
                if not browser:
                    try:
                        browser = p.chromium.launch(headless=True)
                        self.log("已启动内置 Chromium")
                    except Exception as e:
                        self.log(f"无法启动浏览器: {e}")
                        return False

                context = browser.new_context(
                    user_agent=self._DOUYIN_UA,
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()

                def on_response(response):
                    try:
                        resp_url = response.url
                        if not any(h in resp_url for h in cdn_hosts):
                            return
                        ct = response.headers.get("content-type", "")
                        cl = int(response.headers.get("content-length", "0") or "0")
                        status = response.status

                        is_video = (
                            "video" in ct
                            or "mime_type=video" in resp_url
                            or "mime_type=video_mp4" in resp_url
                            or re.search(r'media_type=\d*[02468]', resp_url)
                        )
                        is_audio = (
                            "audio" in ct
                            or "mime_type=audio" in resp_url
                            or "mime_type=audio_mp4" in resp_url
                            or re.search(r'media_type=\d*[13579]', resp_url)
                        )

                        if not is_video and not is_audio:
                            if "/video/" in resp_url or "mp4" in resp_url:
                                is_video = True

                        clean_url = re.sub(r'[&?]Range=[^&]*', '', resp_url)

                        if is_video:
                            video_urls.append((clean_url, cl, status))
                        if is_audio:
                            audio_urls.append((clean_url, cl, status))
                    except Exception:
                        pass

                page.on("response", on_response)

                self.log("正在加载抖音页面...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                try:
                    page_title = page.title() or ""
                except Exception:
                    pass

                self.log("等待视频加载...")
                for _ in range(10):
                    if self.stop_event.is_set():
                        browser.close()
                        return False
                    if video_urls:
                        break
                    time.sleep(1)

                if not video_urls:
                    try:
                        page.evaluate("""() => {
                            const v = document.querySelector('video');
                            if (v) { v.muted = true; v.play(); }
                            const btn = document.querySelector('[class*="play"]') || document.querySelector('.xgplayer-play');
                            if (btn) btn.click();
                        }""")
                    except Exception:
                        pass
                    for _ in range(8):
                        if self.stop_event.is_set():
                            browser.close()
                            return False
                        if video_urls:
                            break
                        time.sleep(1)

                browser.close()

        except Exception as e:
            self.log(f"无头浏览器出错: {e}")
            return False

        if not video_urls:
            self.log("未抓取到视频地址")
            return False

        def _dedup_and_best(urls):
            seen = {}
            for u, cl, status in urls:
                base = u.split("?")[0]
                if base not in seen or cl > seen[base][1]:
                    seen[base] = (u, cl, status)
            items = list(seen.values())
            full = [x for x in items if x[2] == 200 and x[1] > 0]
            if full:
                full.sort(key=lambda t: t[1], reverse=True)
                return full[0][0]
            items.sort(key=lambda t: (-t[1], t[2]))
            return items[0][0]

        best_video = _dedup_and_best(video_urls)
        best_audio = _dedup_and_best(audio_urls) if audio_urls else None

        self.log(f"抓取到 {len(video_urls)} 个视频流" + (f", {len(audio_urls)} 个音频流" if audio_urls else ""))
        self._set_resolved_url(best_video, is_direct=True)

        aweme_id = ""
        m = re.search(r"/video/(\d+)", url)
        if m:
            aweme_id = m.group(1)
        raw_title = page_title.replace("- 抖音", "").strip() if page_title else ""
        safe_title = self._douyin_sanitize_filename(raw_title) if raw_title else ""
        if safe_title and aweme_id:
            base_name = f"{safe_title}_{aweme_id}"
        elif safe_title:
            base_name = safe_title
        elif aweme_id:
            base_name = f"douyin_{aweme_id}"
        else:
            base_name = f"douyin_{int(time.time())}"
        save_path = os.path.join(self.download_path, f"{base_name}.mp4")

        if best_audio:
            video_tmp = os.path.join(self.download_path, f"{base_name}_video.mp4")
            audio_tmp = os.path.join(self.download_path, f"{base_name}_audio.m4a")

            self.log("下载视频流...")
            if not self._douyin_download_file(best_video, video_tmp):
                self.log("视频流下载失败")
                return False

            self.log("下载音频流...")
            if not self._douyin_download_file(best_audio, audio_tmp):
                self.log("音频流下载失败，使用纯视频文件")
                try:
                    if os.path.exists(audio_tmp):
                        os.remove(audio_tmp)
                except Exception:
                    pass
                if os.path.exists(video_tmp):
                    try:
                        os.replace(video_tmp, save_path)
                    except Exception:
                        save_path = video_tmp
            else:
                self.log("合并音视频...")
                ffmpeg_exe = self.get_ffmpeg_executable()
                if ffmpeg_exe:
                    merge_cmd = [
                        ffmpeg_exe, "-hide_banner", "-nostdin", "-y",
                        "-i", video_tmp, "-i", audio_tmp,
                        "-c:v", "copy", "-c:a", "copy",
                        "-movflags", "+faststart",
                        save_path,
                    ]
                    try:
                        r = subprocess.run(
                            merge_cmd,
                            capture_output=True,
                            text=True,
                            encoding=self.get_subprocess_encoding(),
                            errors="replace",
                            timeout=120,
                            stdin=subprocess.DEVNULL,
                            creationflags=self.get_creationflags(),
                        )
                        if r.returncode == 0 and os.path.exists(save_path):
                            self.log("音视频合并成功")
                            try:
                                os.remove(video_tmp)
                                os.remove(audio_tmp)
                            except Exception:
                                pass
                        else:
                            self.log(f"合并失败(exit={r.returncode})，使用纯视频文件")
                            if os.path.exists(video_tmp):
                                try:
                                    os.replace(video_tmp, save_path)
                                except Exception:
                                    save_path = video_tmp
                            try:
                                if os.path.exists(audio_tmp):
                                    os.remove(audio_tmp)
                            except Exception:
                                pass
                    except Exception as e:
                        self.log(f"合并异常: {e}，使用纯视频文件")
                        if os.path.exists(video_tmp):
                            try:
                                os.replace(video_tmp, save_path)
                            except Exception:
                                save_path = video_tmp
                        try:
                            if os.path.exists(audio_tmp):
                                os.remove(audio_tmp)
                        except Exception:
                            pass
                else:
                    self.log("未找到 ffmpeg，无法合并音视频，使用纯视频文件")
                    if os.path.exists(video_tmp):
                        try:
                            os.replace(video_tmp, save_path)
                        except Exception:
                            save_path = video_tmp
                    try:
                        if os.path.exists(audio_tmp):
                            os.remove(audio_tmp)
                    except Exception:
                        pass
        else:
            self.log("开始下载视频（单流）...")
            if not self._douyin_download_file(best_video, save_path):
                self.log("下载失败")
                return False

        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            self.log(f"下载完成: {save_path}")
            self.log(f"文件大小: {file_size / 1024 / 1024:.2f} MB")
            return True
        else:
            self.log("下载失败：输出文件不存在")
            return False

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

    def ensure_deno(self):
        if os.name != "nt":
            return

        if self.deno_path and os.path.exists(self.deno_path):
            deno_dir = os.path.dirname(self.deno_path)
            current_path = os.environ.get("PATH", "")
            if deno_dir.lower() not in current_path.lower():
                os.environ["PATH"] = deno_dir + os.pathsep + current_path
            self.log(f"已加载内置 Deno: {self.deno_path}")
            return

        found = shutil.which("deno")
        if found:
            self.log(f"已检测到系统 Deno: {found}")
            self.deno_path = found
            return

        self.log("未找到 Deno，部分加密网站可能无法解析。")

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
        cached = os.path.join(self.tools_dir or tempfile.gettempdir(), "ytd-cache", "yt-dlp.exe")
        if os.path.exists(cached):
            return self.ensure_tool_in_temp(cached, "yt-dlp.exe")
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

    def resolve_deno_path(self):
        bundled = self.get_resource_path("deno.exe")
        if os.path.exists(bundled):
            return self.ensure_tool_in_temp(bundled, "deno.exe")
        found = shutil.which("deno")
        if found:
            return found
        return bundled

    def _init_tools_background(self):
        self.ensure_deno()
        self.check_and_update_ytdlp()
        self._ytdlp_ready.set()

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

    def get_latest_ytdlp_version(self):
        """获取最新yt-dlp版本号"""
        try:
            url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data["tag_name"]
        except Exception as e:
            self.log(f"获取最新版本失败: {str(e)}")
            return None

    def get_current_ytdlp_version(self):
        """获取当前yt-dlp版本号"""
        try:
            cmd = [self.yt_dlp_path, "--version"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                creationflags=self.get_creationflags(),
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.log(f"获取当前版本失败: {str(e)}")
        return None

    def download_latest_ytdlp(self, version):
        """下载最新版yt-dlp"""
        try:
            url = f"https://github.com/yt-dlp/yt-dlp/releases/download/{version}/yt-dlp.exe"
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"yt-dlp-{version}.exe")
            
            self.log(f"正在下载yt-dlp {version}...")
            
            urllib.request.urlretrieve(url, temp_file)
            
            if os.path.exists(temp_file):
                self.log(f"下载完成，文件大小: {os.path.getsize(temp_file)} 字节")
                return temp_file
            else:
                self.log("下载失败: 文件不存在")
                return None
        except Exception as e:
            self.log(f"下载失败: {str(e)}")
            return None

    def verify_ytdlp_integrity(self, file_path):
        """验证yt-dlp文件完整性"""
        try:
            cmd = [file_path, "--version"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                encoding=self.get_subprocess_encoding(),
                errors="replace",
                creationflags=self.get_creationflags(),
            )
            return result.returncode == 0
        except Exception:
            return False

    def update_ytdlp_to_temp(self, new_ytdlp_path):
        try:
            if not self.tools_dir:
                return self.yt_dlp_path
            
            target_path = self.ensure_tool_in_temp(new_ytdlp_path, "yt-dlp.exe")
            
            if target_path != self.yt_dlp_path:
                self.log(f"yt-dlp已更新到: {target_path}")
                self.yt_dlp_path = target_path

            cache_dir = os.path.join(self.tools_dir, "ytd-cache")
            os.makedirs(cache_dir, exist_ok=True)
            cached_path = os.path.join(cache_dir, "yt-dlp.exe")
            try:
                shutil.copy2(new_ytdlp_path, cached_path + ".tmp")
                os.replace(cached_path + ".tmp", cached_path)
            except Exception:
                pass
            
            return target_path
        except Exception as e:
            self.log(f"更新失败: {str(e)}")
            return self.yt_dlp_path

    def check_and_update_ytdlp(self):
        """检查并更新yt-dlp"""
        try:
            self.log("正在检查yt-dlp更新...")
            
            current_version = self.get_current_ytdlp_version()
            latest_version = self.get_latest_ytdlp_version()
            
            if not current_version or not latest_version:
                self.log("无法获取版本信息，跳过更新")
                return
            
            self.log(f"当前版本: {current_version}, 最新版本: {latest_version}")
            
            if current_version == latest_version:
                self.log("yt-dlp已是最新版本")
                return
            
            self.log("发现新版本，开始更新...")
            
            new_ytdlp_path = self.download_latest_ytdlp(latest_version)
            if not new_ytdlp_path:
                self.log("下载失败，继续使用当前版本")
                return
            
            if not self.verify_ytdlp_integrity(new_ytdlp_path):
                self.log("文件验证失败，继续使用当前版本")
                try:
                    os.remove(new_ytdlp_path)
                except Exception:
                    pass
                return
            
            self.update_ytdlp_to_temp(new_ytdlp_path)
            
            try:
                os.remove(new_ytdlp_path)
            except Exception:
                pass
            
            self.log("yt-dlp更新完成")
            
        except Exception as e:
            self.log(f"更新检查失败: {str(e)}")
            self.log("将继续使用当前版本")

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

        self.download_path = self.path_var.get().strip() or self.get_default_download_path()
        self.stop_event.clear()
        self._set_resolved_url("", is_direct=False)
        
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        def download_thread():
            dl_url = url
            try:
                if not self._ytdlp_ready.is_set():
                    self.log("yt-dlp 正在初始化/更新中，请稍候...")
                    self._ytdlp_ready.wait()
                    if self.stop_event.is_set():
                        self.log("任务已终止")
                        return
                    self.log("yt-dlp 初始化完成，开始下载...")

                if self.is_douyin_url(dl_url):
                    actual_url = self._extract_url_from_text(dl_url)
                    self.log(f"提取到链接: {actual_url}")
                    douyin_success = self.douyin_download(actual_url)
                    if douyin_success:
                        if self.stop_event.is_set():
                            self.log("任务已终止")
                            return
                        message = f"已处理完成\n点击'是'打开下载文件夹，'否'关闭提示"
                        if messagebox.askyesno("下载完成", message):
                            folder = self.download_path
                            if os.name == 'nt':
                                os.startfile(folder)
                            else:
                                subprocess.run(["open", folder])
                        return
                    self.log("抖音专用下载失败，回退到yt-dlp下载...")
                    dl_url = actual_url

                if not self.resolve_url(dl_url):
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

                if self.is_douyin_url(dl_url):
                    cookie_file = self._douyin_generate_cookie_file()
                    if cookie_file:
                        cmd.extend(["--cookies", cookie_file])
                
                if self.is_debug:
                    cmd.append("-v")
                
                cmd.append(dl_url)
                
                self.log(f"开始下载: {dl_url}")
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
