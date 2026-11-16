import os
import subprocess
import sys
import tkinter as tk
from tkinter import Button, Tk, messagebox
import webbrowser
import winsound
import comtypes
from comtypes import COMMETHOD, GUID, HRESULT, IUnknown
from ctypes import POINTER, c_int, c_uint
from ctypes.wintypes import LPCWSTR, RECT
from PIL import Image, ImageTk

try:
  import ctypes

  ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
  pass


def resource_path(relative_path):
  """Get absolute path to resource, works for dev and for PyInstaller"""
  try:
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)


class IShellItemArray(IUnknown):
  _iid_ = GUID("{B63EA76D-1F85-456F-A19C-48159EFA858B}")
  _methods_ = []


class IDesktopWallpaper(IUnknown):
  _iid_ = GUID("{B92B56A9-8B55-4E14-9A89-0199BBB6F93B}")
  _methods_ = [
      COMMETHOD([], HRESULT, "SetWallpaper", (["in"], LPCWSTR), (["in"], LPCWSTR)),
      COMMETHOD([], HRESULT, "GetWallpaper", (["in"], LPCWSTR), (["out"], POINTER(LPCWSTR))),
      COMMETHOD([], HRESULT, "GetMonitorDevicePathAt", (["in"], c_uint), (["out"], POINTER(LPCWSTR))),
      COMMETHOD([], HRESULT, "GetMonitorDevicePathCount", (["out"], POINTER(c_uint))),
      COMMETHOD([], HRESULT, "GetMonitorRECT", (["in"], LPCWSTR), (["out"], POINTER(RECT))),
      COMMETHOD([], HRESULT, "SetBackgroundColor", (["in"], c_uint)),
      COMMETHOD([], HRESULT, "GetBackgroundColor", (["out"], POINTER(c_uint))),
      COMMETHOD([], HRESULT, "SetPosition", (["in"], c_int)),
      COMMETHOD([], HRESULT, "GetPosition", (["out"], POINTER(c_int))),
      COMMETHOD([], HRESULT, "SetSlideshow", (["in"], POINTER(IShellItemArray))),
      COMMETHOD([], HRESULT, "GetSlideshow", (["out"], POINTER(POINTER(IShellItemArray)))),
      COMMETHOD([], HRESULT, "SetSlideshowOptions", (["in"], c_int), (["in"], c_uint)),
      COMMETHOD([], HRESULT, "GetSlideshowOptions", (["out"], POINTER(c_int)), (["out"], POINTER(c_uint))),
      COMMETHOD([], HRESULT, "AdvanceSlideshow", (["in"], LPCWSTR), (["in"], c_int)),
      COMMETHOD([], HRESULT, "GetStatus", (["out"], POINTER(c_int))),
      COMMETHOD([], HRESULT, "Enable", (["in"], c_int)),
  ]


class PatakynoGameApp:
  WINDOW_WIDTH = 680
  WINDOW_HEIGHT = 380
  QUESTION_IMAGE_SIZE = 145
  SYSTEM_REGISTRY_KEYS = (
      (r"Control Panel\Desktop", None),
      (
          r"Software\Microsoft\Windows\DWM",
          (
              "ColorizationColor",
              "ColorizationAfterglow",
              "AccentColor",
              "ColorPrevalence",
          ),
      ),
      (
          r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent",
          ("AccentPalette", "AccentColorMenu", "StartColorMenu"),
      ),
      (
          r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
          ("ColorPrevalence",),
      ),
      (r"Control Panel\Colors", ("Background",)),
      (r"Control Panel\Personalization\Desktop Slideshow", None),
      (r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers", None),
  )

  def __init__(self, root):
    self.root = root
    self.lang = "en"  # Default language is English
    self.wrong_count = 0
    self.current_question_index = 0
    self.is_dark_red_theme = False  # Track dark-red theme state
    self.original_wallpaper_state = None
    self.wallpaper_snapshot_taken = False
    self.original_registry_settings = None
    self.original_registry_keys = None
    self.com_initialized = False
    self.completed_successfully = False

    self.root.title("The Patakyno Game")
    self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
    self.root.resizable(False, False)
    self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    # Set application icon from files folder
    try:
      icon_path = resource_path(os.path.join("files", "pataka.ico"))
      if os.path.exists(icon_path):
        self.root.iconbitmap(icon_path)
    except Exception as e:
      print(f"Error loading icon: {e}")

    # Paths to resources
    self.wallpaper_path = resource_path(os.path.join("files", "wallpaper.png"))
    self.background_path = resource_path(os.path.join("files", "background.png"))
    try:
      with Image.open(self.background_path) as image:
        self.background_source = image.convert("RGBA")
    except OSError as e:
      self.background_source = None
      print(f"Error loading background image: {e}")

    # Questions database with exact image filenames matching your files folder
    self.questions = [
        {
            "image": "pataka.png",
            "en": {
                "q": "Who is Pataka?",
                "opts": [("President", "correct"), ("Model", "wrong")],
            },
            "ru": {
                "q": "Кто такая патака?",
                "opts": [("Президент", "correct"), ("Модель", "wrong")],
            },
        },
        {
            "image": "patakyno_flag.png",
            "en": {
                "q": "What is the Republic of Patakyno?",
                "opts": [
                    ("Independent state", "correct"),
                    ("Integral part of Russia", "wrong"),
                ],
            },
            "ru": {
                "q": "Что такое Республика Патакино?",
                "opts": [
                    ("Независимое государство", "correct"),
                    ("Неотъемлемая часть России", "wrong"),
                ],
            },
        },
        {
            "image": "pedro.png",
            "en": {
                "q": "What does Pedro love?",
                "opts": [
                    ("Robbing the people of Mexico", "wrong"),
                    ("Cheese", "correct"),
                ],
                "sound": "iwantcheese.wav",
            },
            "ru": {
                "q": "Что любит Педро?",
                "opts": [
                    ("Грабить народ Мексики", "wrong"),
                    ("Сыр", "correct"),
                ],
                "sound": "iwantcheese.wav",
            },
        },
        {
            "image": "kesha.png",
            "en": {
                "q": "Who is the head of Israel?",
                "opts": [("Kesha", "correct"), ("Petus", "wrong")],
            },
            "ru": {
                "q": "Кто глава Израиля?",
                "opts": [("Кеша", "correct"), ("Петус", "wrong")],
            },
        },
        {
            "image": "pataka2.png",
            "en": {
                "q": "What citizenship do you want?",
                "opts": [("Russia", "wrong"), ("Patakyno", "correct")],
            },
            "ru": {
                "q": "Какое гражданство вы хотите?",
                "opts": [("России", "wrong"), ("Патакино", "correct")],
            },
        },
    ]

    # Keep a reference to images to prevent garbage collection
    self.current_image = None

    # Show welcome / language selection screen first
    self.apply_theme_colors()
    self.show_welcome_screen()
    self.root.after_idle(self.center_window)

  def center_window(self):
    """Centers the window precisely on the user's screen"""
    self.root.update_idletasks()
    width = self.WINDOW_WIDTH
    height = self.WINDOW_HEIGHT
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    self.root.geometry(f"{width}x{height}+{x}+{y}")

  def play_sound(self, filename, wait=False):
    """Play sound reliably using winsound for .wav files"""
    try:
      sound_path = resource_path(os.path.join("files", filename))
      if os.path.exists(sound_path):
        flags = winsound.SND_FILENAME
        if not wait:
          flags |= winsound.SND_ASYNC
        winsound.PlaySound(
            sound_path, flags
        )
    except Exception as e:
      print(f"Error playing sound {filename}: {e}")

  def set_wallpaper(self):
    """Set wallpaper using Windows API"""
    if not os.path.exists(self.wallpaper_path):
      raise FileNotFoundError(self.wallpaper_path)

    if not self.wallpaper_snapshot_taken:
      self.capture_system_settings()

    if not ctypes.windll.user32.SystemParametersInfoW(
        20, 0, self.wallpaper_path, 3
    ):
      raise ctypes.WinError(ctypes.get_last_error())

  def capture_system_settings(self):
    """Capture wallpaper and accent settings before the first system change."""
    import winreg

    comtypes.CoInitialize()
    self.com_initialized = True
    captured = False
    try:
      desktop = comtypes.CoCreateInstance(
          GUID("{C2CF3110-460E-4FC1-B9D0-8A1C0C9CC4BD}"),
          interface=IDesktopWallpaper,
          clsctx=comtypes.CLSCTX_ALL,
      )
      status = desktop.GetStatus()
      monitor_count = desktop.GetMonitorDevicePathCount()
      wallpapers = []
      for index in range(monitor_count):
        monitor = desktop.GetMonitorDevicePathAt(index)
        wallpapers.append((monitor, desktop.GetWallpaper(monitor) or ""))

      registry_settings, registry_keys = self.capture_registry_settings(
          winreg
      )
      background_type_value = registry_settings.get(
          (
              r"Software\Microsoft\Windows\CurrentVersion\Explorer\Wallpapers",
              "BackgroundType",
          )
      )
      self.original_wallpaper_state = {
          "desktop": desktop,
          "wallpapers": wallpapers,
          "position": desktop.GetPosition(),
          "background_color": desktop.GetBackgroundColor(),
          "slideshow": (
              desktop.GetSlideshow()
              if background_type_value == (2, winreg.REG_DWORD)
              else None
          ),
          "slideshow_options": desktop.GetSlideshowOptions(),
          "status": status,
          "background_type": (
              background_type_value[0]
              if background_type_value is not None
              else None
          ),
      }
      self.original_registry_settings = registry_settings
      self.original_registry_keys = registry_keys
      self.wallpaper_snapshot_taken = True
      captured = True
    finally:
      if not captured:
        self.release_system_snapshot()

  def capture_registry_settings(self, winreg):
    """Capture selected wallpaper values and all slideshow metadata."""
    snapshot = {}
    existing_keys = {}
    for key_path, value_names in self.SYSTEM_REGISTRY_KEYS:
      try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_QUERY_VALUE,
        ) as key:
          existing_keys[key_path] = True
          if value_names is None:
            _, value_count, _ = winreg.QueryInfoKey(key)
            names = [
                winreg.EnumValue(key, index)[0]
                for index in range(value_count)
            ]
          else:
            names = value_names
          for value_name in names:
            try:
              snapshot[(key_path, value_name)] = winreg.QueryValueEx(
                  key, value_name
              )
            except FileNotFoundError:
              snapshot[(key_path, value_name)] = None
      except FileNotFoundError:
        existing_keys[key_path] = False
        if value_names is not None:
          for value_name in value_names:
            snapshot[(key_path, value_name)] = None
    return snapshot, existing_keys

  def broadcast_windows_settings_change(self):
    hwnd_broadcast = 0xFFFF
    wm_settingchange = 0x001A
    for section in ("Control Panel\\Desktop", "ImmersiveColorSet"):
      result = ctypes.windll.user32.SendMessageTimeoutW(
          hwnd_broadcast,
          wm_settingchange,
          0,
          section,
          2,
          5000,
          None,
      )
      if not result:
        raise ctypes.WinError(ctypes.get_last_error())

  def restore_system_settings(self):
    """Restore the wallpaper and accent values captured before they changed."""
    errors = []
    if self.wallpaper_snapshot_taken:
      try:
        self.restore_wallpaper()
      except (OSError, comtypes.COMError) as e:
        errors.append(f"Could not restore the previous wallpaper: {e}")

      errors.extend(self.restore_registry_settings())
      if not errors:
        try:
          self.broadcast_windows_settings_change()
        except OSError as e:
          errors.append(f"Could not refresh Windows settings: {e}")

      if not errors:
        self.wallpaper_snapshot_taken = False
        self.original_wallpaper_state = None
        self.original_registry_settings = None
        self.original_registry_keys = None

    return errors

  def restore_wallpaper(self):
    state = self.original_wallpaper_state
    desktop = state["desktop"]
    is_slideshow = state["background_type"] == 2
    is_solid_color = (
        state["background_type"] == 1
        or not any(path for _, path in state["wallpapers"])
    )

    if is_slideshow:
      if state["slideshow"] is None:
        raise OSError("The original slideshow could not be captured.")
      desktop.SetSlideshow(state["slideshow"])
      desktop.SetSlideshowOptions(*state["slideshow_options"])
    elif is_solid_color:
      if not ctypes.windll.user32.SystemParametersInfoW(20, 0, "", 3):
        raise ctypes.WinError(ctypes.get_last_error())
    else:
      first_wallpaper = next(
          (path for _, path in state["wallpapers"] if path), None
      )
      if first_wallpaper and not ctypes.windll.user32.SystemParametersInfoW(
          20, 0, first_wallpaper, 3
      ):
        raise ctypes.WinError(ctypes.get_last_error())
      for monitor, path in state["wallpapers"]:
        if path:
          desktop.SetWallpaper(monitor, path)

    desktop.SetPosition(state["position"])
    desktop.SetBackgroundColor(state["background_color"])
    desktop.Enable(bool(state["status"] & 0x01))
    if is_slideshow:
      first_wallpaper = next(
          (path for _, path in state["wallpapers"] if path), None
      )
      if first_wallpaper and not ctypes.windll.user32.SystemParametersInfoW(
          20, 0, first_wallpaper, 3
      ):
        raise ctypes.WinError(ctypes.get_last_error())
      desktop.SetSlideshow(state["slideshow"])
      desktop.SetSlideshowOptions(*state["slideshow_options"])
      desktop.Enable(bool(state["status"] & 0x01))

  def restore_registry_settings(self):
    import winreg

    errors = []
    for key_path, value_names in self.SYSTEM_REGISTRY_KEYS:
      original_values = {
          name: value
          for (path, name), value in self.original_registry_settings.items()
          if path == key_path
      }
      try:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE,
        ) as key:
          if value_names is None:
            _, value_count, _ = winreg.QueryInfoKey(key)
            current_names = {
                winreg.EnumValue(key, index)[0]
                for index in range(value_count)
            }
            names_to_restore = current_names | set(original_values)
          else:
            names_to_restore = set(value_names)

          for value_name in names_to_restore:
            try:
              original_value = original_values.get(value_name)
              if original_value is None:
                winreg.DeleteValue(key, value_name)
              else:
                value, value_type = original_value
                winreg.SetValueEx(key, value_name, 0, value_type, value)
            except FileNotFoundError:
              if original_values.get(value_name) is not None:
                errors.append(
                    f"Could not restore registry value "
                    f"{key_path}\\{value_name}: the key disappeared."
                )
            except OSError as e:
              errors.append(
                  f"Could not restore registry value "
                  f"{key_path}\\{value_name}: {e}"
              )
      except OSError as e:
        errors.append(f"Could not restore registry key {key_path}: {e}")

    if not errors:
      for key_path, existed_before in self.original_registry_keys.items():
        if existed_before:
          continue
        try:
          with winreg.OpenKey(
              winreg.HKEY_CURRENT_USER,
              key_path,
              0,
              winreg.KEY_QUERY_VALUE,
          ) as key:
            subkey_count, value_count, _ = winreg.QueryInfoKey(key)
          if subkey_count == 0 and value_count == 0:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
          pass
        except OSError as e:
          errors.append(f"Could not remove empty registry key {key_path}: {e}")
    return errors

  def release_system_snapshot(self):
    self.original_wallpaper_state = None
    self.original_registry_settings = None
    self.original_registry_keys = None
    self.wallpaper_snapshot_taken = False
    if self.com_initialized:
      comtypes.CoUninitialize()
      self.com_initialized = False

  def close_app(self):
    if self.completed_successfully:
      errors = self.restore_system_settings()
      if errors:
        messagebox.showerror(
            "System settings restore failed",
            "\n".join(errors),
            parent=self.root,
        )
    self.release_system_snapshot()
    self.root.destroy()

  def force_windows_manual_dark_red_accent(self):
    """Force Windows 11 26H2 into Manual accent mode with deep dark red color"""
    try:
      import winreg

      if self.original_registry_settings is None:
        self.capture_system_settings()

      # Stop Windows from selecting an accent automatically from the wallpaper.
      with winreg.CreateKeyEx(
          winreg.HKEY_CURRENT_USER,
          r"Control Panel\Desktop",
          0,
          winreg.KEY_SET_VALUE,
      ) as key_desktop:
        winreg.SetValueEx(
            key_desktop, "AutoColorization", 0, winreg.REG_DWORD, 0
        )

      # Explorer accent values use AABBGGRR, while DWM uses AARRGGBB.
      red, green, blue = 0x85, 0x00, 0x1B
      accent_color = 0xFF000000 | (blue << 16) | (green << 8) | red
      dwm_color = 0xC4000000 | (red << 16) | (green << 8) | blue
      shades = [
          tuple(
              int(channel + (255 - channel) * amount)
              for channel in (red, green, blue)
          )
          for amount in (0.6, 0.4, 0.2, 0.0)
      ]
      shades.extend(
          tuple(int(channel * (1 + amount)) for channel in (red, green, blue))
          for amount in (-0.25, -0.45, -0.65)
      )
      shades.append((0x88, 0x88, 0x88))
      accent_palette = b"".join(bytes(shade + (0,)) for shade in shades)
      start_color = (
          0xFF000000
          | (shades[4][2] << 16)
          | (shades[4][1] << 8)
          | shades[4][0]
      )

      with winreg.CreateKeyEx(
          winreg.HKEY_CURRENT_USER,
          r"Software\Microsoft\Windows\DWM",
          0,
          winreg.KEY_SET_VALUE,
      ) as key_dwm:
        winreg.SetValueEx(
            key_dwm, "ColorizationColor", 0, winreg.REG_DWORD, dwm_color
        )
        winreg.SetValueEx(
            key_dwm, "ColorizationAfterglow", 0, winreg.REG_DWORD, dwm_color
        )
        winreg.SetValueEx(
            key_dwm, "AccentColor", 0, winreg.REG_DWORD, accent_color
        )
        winreg.SetValueEx(
            key_dwm, "ColorPrevalence", 0, winreg.REG_DWORD, 1
        )

      with winreg.CreateKeyEx(
          winreg.HKEY_CURRENT_USER,
          r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent",
          0,
          winreg.KEY_SET_VALUE,
      ) as key_accent:
        winreg.SetValueEx(
            key_accent,
            "AccentPalette",
            0,
            winreg.REG_BINARY,
            accent_palette,
        )
        winreg.SetValueEx(
            key_accent, "AccentColorMenu", 0, winreg.REG_DWORD, accent_color
        )
        winreg.SetValueEx(
            key_accent, "StartColorMenu", 0, winreg.REG_DWORD, start_color
        )

      with winreg.CreateKeyEx(
          winreg.HKEY_CURRENT_USER,
          r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
          0,
          winreg.KEY_SET_VALUE,
      ) as key_personalize:
        winreg.SetValueEx(
            key_personalize, "ColorPrevalence", 0, winreg.REG_DWORD, 1
        )

      self.broadcast_windows_settings_change()
    except OSError as e:
      messagebox.showerror(
          "System accent update failed", str(e), parent=self.root
      )
      return False
    return True

  def apply_theme_colors(self):
    """Configure dynamic colors (Default Dark with modern blue buttons -> Deep Dark Red on wrong answer)"""
    if self.is_dark_red_theme:
      self.bg_color = "#1F0406"  # Deep rich dark red background for app window
      self.fg_color = "#FFFFFF"
      self.btn_bg = "#6E0B14"  # Rich dark red buttons
      self.btn_fg = "#FFFFFF"
    else:
      self.bg_color = "#1E1E1E"  # Modern dark theme background
      self.fg_color = "#FFFFFF"
      self.btn_bg = "#0067C0"  # Modern blue buttons by default
      self.btn_fg = "#FFFFFF"

    self.root.configure(bg=self.bg_color)

  def clear_window(self):
    """Remove all widgets from the root window and apply current theme"""
    for widget in self.root.winfo_children():
      widget.destroy()
    self.canvas = None
    self.background_image = None
    self.current_image = None
    self.apply_theme_colors()

  def create_screen_canvas(self):
    canvas = tk.Canvas(
        self.root,
        width=self.WINDOW_WIDTH,
        height=self.WINDOW_HEIGHT,
        bg=self.bg_color,
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)

    if self.background_source is not None:
      background = self.background_source.resize(
          (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
          Image.Resampling.LANCZOS,
      )
      alpha = background.getchannel("A").point(lambda value: value * 51 // 255)
      background.putalpha(alpha)
      composite = Image.new(
          "RGBA",
          (self.WINDOW_WIDTH, self.WINDOW_HEIGHT),
          self.bg_color,
      )
      composite.alpha_composite(background)
      self.background_image = ImageTk.PhotoImage(
          composite, master=self.root
      )
      canvas.create_image(0, 0, image=self.background_image, anchor="nw")

    self.canvas = canvas
    return canvas

  def add_canvas_button(self, canvas, x, y, width, text, command):
    button = Button(
        canvas,
        text=text,
        command=command,
        font=("Segoe UI", 10),
        bg=self.btn_bg,
        fg=self.btn_fg,
        relief="flat",
        cursor="hand2",
    )
    canvas.create_window(
        x,
        y,
        window=button,
        width=width,
        height=38,
    )

  def load_question_image(self, img_filename):
    """Load, resize, and return image for the current question safely"""
    try:
      img_path = resource_path(os.path.join("files", img_filename))
      image = tk.PhotoImage(file=img_path)
      scale = max(
          (image.width() + self.QUESTION_IMAGE_SIZE - 1)
          // self.QUESTION_IMAGE_SIZE,
          (image.height() + self.QUESTION_IMAGE_SIZE - 1)
          // self.QUESTION_IMAGE_SIZE,
      )
      if scale > 1:
        image = image.subsample(scale, scale)
      self.current_image = image
      return self.current_image
    except tk.TclError as e:
      print(f"Error loading image {img_filename}: {e}")
    return None

  def show_welcome_screen(self):
    """Initial screen for language selection and starting the game"""
    self.clear_window()
    canvas = self.create_screen_canvas()
    canvas.create_text(
        self.WINDOW_WIDTH // 2,
        112,
        text="Welcome to The Patakyno Game\nДобро пожаловать в Патакино",
        font=("Segoe UI", 12, "bold"),
        fill=self.fg_color,
        justify="center",
    )

    canvas.create_text(
        self.WINDOW_WIDTH // 2,
        184,
        text="Choose language / Выберите язык:",
        font=("Segoe UI", 10),
        fill=self.fg_color,
    )

    self.add_canvas_button(
        canvas, self.WINDOW_WIDTH // 2 - 95, 244, 170, "English",
        lambda: self.start_game("en"),
    )
    self.add_canvas_button(
        canvas, self.WINDOW_WIDTH // 2 + 95, 244, 170, "Русский",
        lambda: self.start_game("ru"),
    )
    canvas.create_text(
        12,
        self.WINDOW_HEIGHT - 12,
        text="Jersey Drush",
        font=("Segoe UI", 8),
        fill="#AAAAAA",
        anchor="sw",
        tags=("author_link",),
    )
    canvas.tag_bind(
        "author_link",
        "<Button-1>",
        lambda event: webbrowser.open("https://github.com/jerseydrush/"),
    )
    canvas.tag_bind(
        "author_link",
        "<Enter>",
        lambda event: canvas.config(cursor="hand2"),
    )
    canvas.tag_bind(
        "author_link",
        "<Leave>",
        lambda event: canvas.config(cursor=""),
    )

    canvas.create_text(
        self.WINDOW_WIDTH - 12,
        self.WINDOW_HEIGHT - 12,
        text="v5.1",
        font=("Segoe UI", 8),
        fill="#AAAAAA",
        anchor="se",
        tags=("version_link",),
    )
    canvas.tag_bind(
        "version_link",
        "<Button-1>",
        lambda event: webbrowser.open(
            "https://github.com/jerseydrush/the_patakyno_game/releases/"
        ),
    )
    canvas.tag_bind(
        "version_link",
        "<Enter>",
        lambda event: canvas.config(cursor="hand2"),
    )
    canvas.tag_bind(
        "version_link",
        "<Leave>",
        lambda event: canvas.config(cursor=""),
    )

  def start_game(self, lang):
    """Start the quiz with the selected language"""
    self.lang = lang
    self.current_question_index = 0
    self.wrong_count = 0
    self.is_dark_red_theme = False
    self.show_question()

  def show_question(self):
    """Display the current question, image, and options"""
    self.clear_window()

    if self.current_question_index >= len(self.questions):
      self.show_victory_screen()
      return

    q_data = self.questions[self.current_question_index]
    text_data = q_data[self.lang]

    # Special trigger for Question 3 (Pedro loves cheese -> play iwantcheese.wav)
    if "sound" in text_data:
      self.play_sound(text_data["sound"])

    canvas = self.create_screen_canvas()

    # Keep the image beside the question and answers in the landscape layout.
    img_obj = self.load_question_image(q_data["image"])
    if img_obj:
      canvas.create_image(108, self.WINDOW_HEIGHT // 2, image=img_obj)

    panel_x = 220
    panel_width = self.WINDOW_WIDTH - panel_x - 24
    canvas.create_text(
        panel_x,
        105,
        text=f"Question {self.current_question_index + 1} / {len(self.questions)}",
        font=("Segoe UI", 9, "italic"),
        fill="#AAAAAA",
        anchor="w",
    )

    canvas.create_text(
        panel_x,
        150,
        text=text_data["q"],
        font=("Segoe UI", 11, "bold"),
        fill=self.fg_color,
        width=panel_width,
        justify="left",
        anchor="nw",
    )

    for option_index, (text, answer_type) in enumerate(text_data["opts"]):
      self.add_canvas_button(
          canvas,
          panel_x + panel_width // 2,
          230 + option_index * 52,
          panel_width,
          text,
          lambda answer=answer_type: self.handle_answer(answer),
      )

  def handle_answer(self, answer_type):
    """Handle correct or incorrect answers"""
    if answer_type == "correct":
      next_question_index = self.current_question_index + 1
      next_question_has_sound = (
          next_question_index < len(self.questions)
          and "sound" in self.questions[next_question_index][self.lang]
      )
      self.play_sound("correct.wav", wait=next_question_has_sound)
      self.current_question_index += 1
      self.show_question()
    else:
      # Wrong answer logic
      self.wrong_count += 1
      self.play_sound("wrong.wav")

      if self.wrong_count == 1:
        # 1st wrong: change wallpaper
        try:
          self.set_wallpaper()
          wallpaper_changed = True
        except OSError as e:
          wallpaper_changed = False
          messagebox.showerror(
              (
                  "Wallpaper change failed"
                  if self.lang == "en"
                  else "Не удалось изменить обои"
              ),
              str(e),
              parent=self.root,
          )
        warning_title = (
            "Patakyno Warning"
            if self.lang == "en"
            else "Предупреждение Патакино"
        )
        warning_text = (
            (
                "-1000 PATAKYNO CREDITS\n"
                + (
                    "Your PataCoins are now frozen."
                    if wallpaper_changed
                    else "Wallpaper could not be changed."
                )
            )
            if self.lang == "en"
            else (
                "-1000 КРЕДИТОВ ПАТАКИНО\n"
                + (
                    "Ваши ПатаКоины теперь заморожены."
                    if wallpaper_changed
                    else "Не удалось изменить обои."
                )
            )
        )
        messagebox.showwarning(
            warning_title, warning_text, parent=self.root
        )
      elif self.wrong_count == 2:
        # 2nd wrong: switch app theme to deep dark red mode AND force system manual dark red accent
        self.is_dark_red_theme = True
        self.force_windows_manual_dark_red_accent()
        warning = (
            "-150000 PATAKYNO CREDITS\n"
            "You have been declared wanted in the United Patakia."
            if self.lang == "en"
            else (
                "-150000 КРЕДИТОВ ПАТАКИНО\n"
                "Вы объявлены в розыск в Объединении Патакия."
            )
        )
        warning_title = (
            "Patakyno Warning"
            if self.lang == "en"
            else "Предупреждение Патакино"
        )
        messagebox.showwarning(
            warning_title, warning, parent=self.root
        )
      elif self.wrong_count >= 3:
        # 3rd wrong: spy detection message and restart the computer
        msg = (
            "-9999999 КРЕДИТОВ ПАТАКИНО\n"
            "Los Pedrilos уже выехали за тобой!"
            if self.lang == "ru"
            else (
                "-9999999 PATAKYNO CREDITS\n"
                "Los Pedrilos are already on their way for you!"
            )
        )
        alert_title = (
            "SECURITY ALERT"
            if self.lang == "en"
            else "ТРЕВОГА БЕЗОПАСНОСТИ"
        )
        messagebox.showerror(alert_title, msg)
        self.close_app()

        # Trigger computer restart in 10 seconds
        try:
          subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
        except Exception as e:
          print(f"Error triggering system action: {e}")
        return

      # Move to next question even after a wrong answer
      self.current_question_index += 1
      self.show_question()

  def show_victory_screen(self):
    """Screen shown when all questions are completed correctly (resets app theme back to blue)"""
    self.completed_successfully = True
    self.is_dark_red_theme = False  # Reset app theme back to modern dark/blue on success
    restore_errors = self.restore_system_settings()
    self.clear_window()
    canvas = self.create_screen_canvas()

    if restore_errors:
      messagebox.showerror(
          "System settings restore failed",
          "\n".join(restore_errors),
          parent=self.root,
      )

    victory_text = (
        "Поздравляем! Вы истинный гражданин Патакино!"
        if self.lang == "ru"
        else "Congratulations! You are a true citizen of Patakyno!"
    )
    canvas.create_text(
        self.WINDOW_WIDTH // 2,
        145,
        text=victory_text,
        font=("Segoe UI", 12, "bold"),
        fill=self.fg_color,
        width=self.WINDOW_WIDTH - 80,
        justify="center",
    )

    self.add_canvas_button(
        canvas,
        self.WINDOW_WIDTH // 2,
        235,
        190,
        "Exit / Выход",
        self.close_app,
    )


if __name__ == "__main__":
  root = Tk()
  app = PatakynoGameApp(root)
  root.mainloop()