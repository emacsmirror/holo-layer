from PyQt6 import QtCore
from PyQt6.QtCore import QObject, Qt, QRectF, QMimeDatabase
from PyQt6.QtGui import QColor, QFontMetrics, QFontDatabase, QFont, QIcon, QPainterPath

from utils import *

import os

# File extension to MIME lookup table
FILE_SUFFIX_MIME_DICT = {
    "json": "application-json",
    "vue": "application-javascript"
}

# Mode to icon lookup table
MODE_ICON_DICT = {
    "eaf-file-manager": "directory",
    "eaf-browser": "browser",
    "eaf-git": "git",
    "eaf-map": "map",
    "eaf-rss-reader": "rss-reader",
    "eaf-music-player": "music-player",
    "eaf-pyqterminal": "terminal",
    "eaf-terminal": "terminal",
    "eaf-camera": "camera"
}

class SortTab(QObject):

    def __init__(self) -> None:
        super().__init__()

        # Set font.
        [self.font_size] = get_emacs_vars([
            "holo-layer-sort-tab-font-size"
        ])
        self.font_family = QFontDatabase.systemFont(
            QFontDatabase.SystemFont.FixedFont # get the system's monospaced font
        ).family()
        self.font = QFont()
        self.font.setFamily(self.font_family)
        self.font.setPointSize(self.font_size)

        # Set some variables.
        self.tab_scroll_pos = 0 # scroll position, records the horizontal scroll position of the tab bar
        self.tab_icon_size = 22 # tab icon size
        self.tab_padding_x = 15 # padding around tab text
        self.tab_icon_padding_right = 10 # padding between tab icon and tab text
        self.tab_translate_offset = 60 # translate offset, ensure that users can see whether there are other tabs around current tab

        # Create icon cache directory.
        self.icon_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon_cache")
        if not os.path.exists(self.icon_cache_dir):
            os.makedirs(self.icon_cache_dir)

        # Create mime database.
        self.mime_db = QMimeDatabase()

    def draw(self, painter, emacs_frame_info, sort_tab_info):
        # Save current painting state
        painter.save()
        
        # Draw tab bar background
        if "emacs_theme_mode" in sort_tab_info and emacs_frame_info and len(sort_tab_info["tab_names"]) > 0:
            [emacs_x, emacs_y, emacs_width, emacs_height] = emacs_frame_info
            
            # Get emacs theme colors.
            theme_mode = sort_tab_info["emacs_theme_mode"]
            theme_background_color = sort_tab_info["emacs_theme_background_color"]
            
            # Create tab background color base on emacs background color.
            if theme_mode == "dark":
                if theme_background_color == "#000000":
                    tab_background_color = "#333333"
                else:
                    tab_background_color = QColor(theme_background_color).darker(120).name()
            else:
                if theme_background_color == "#FFFFFF":
                    tab_background_color = "#EEEEEE"
                else:
                    tab_background_color = QColor(theme_background_color).darker(110).name()
            
            tab_line_bg = QColor(tab_background_color)
            
            # Draw tab bar background
            tab_height = sort_tab_info["tab_height"]
            
            painter.setBrush(tab_line_bg)
            painter.setPen(QColor(tab_background_color))
            painter.drawRect(QRectF(emacs_x, emacs_y, emacs_width, tab_height))
        
        # Use original condition: only draw tabs when tab info and frame info are available
        if "tab_names" in sort_tab_info and emacs_frame_info:
            self.emacs_frame_info = emacs_frame_info
            self.sort_tab_info = sort_tab_info
            
            [emacs_x, emacs_y, emacs_width, emacs_height] = emacs_frame_info
            tab_names = sort_tab_info["tab_names"]
            tab_modes = sort_tab_info["tab_modes"]
            current_tab_index = sort_tab_info["current_tab_index"]
            tab_height = sort_tab_info["tab_height"]
            emacs_theme_mode = sort_tab_info["emacs_theme_mode"]
            emacs_theme_background_color = sort_tab_info["emacs_theme_background_color"]

            # Set font
            font = QFont()
            font.setPointSize(self.font_size)
            painter.setFont(font)
            font_metrics = QFontMetrics(font)

            # Calculate width for each tab based on text length
            tab_widths = []
            total_width = 0
            
            for i, tab_name in enumerate(tab_names):
                # Get tab icon information
                mode_name = tab_modes[i]
                icon_info = self.get_tab_icon_info(tab_name, mode_name)
                icon_path, icon_offset = icon_info
                
                # Calculate text width
                tab_text = self.get_tab_render_name(tab_name)
                text_width = font_metrics.horizontalAdvance(tab_text)
                
                # Calculate total tab width = slope offset + left padding + icon width(if any) + text width + right padding + slope offset
                tab_slope = 10  # Trapezoid slope horizontal offset
                width = 2 * tab_slope + 2 * self.tab_padding_x + text_width
                if icon_path and os.path.exists(icon_path):
                    width += icon_offset
                
                # Ensure minimum width
                min_width = 100
                width = max(width, min_width)
                
                tab_widths.append(width)
                total_width += width

            # Create tab colors based on Emacs theme colors
            theme_foreground_color = sort_tab_info["emacs_theme_foreground_color"]
            
            # Active tab colors
            active_tab_fg = QColor(theme_foreground_color)
            active_tab_bg = QColor(emacs_theme_background_color)
            
            # Inactive tab colors
            if emacs_theme_mode == "dark":
                # For dark theme
                inactive_tab_fg = QColor(tab_background_color).lighter(500)
                inactive_tab_bg = QColor(tab_background_color).lighter(150)
            else:
                # For light theme
                inactive_tab_fg = QColor(tab_background_color).darker(300)
                inactive_tab_bg = QColor(tab_background_color).darker(105)
            
            # Set tab overlap amount
            tab_overlap = 10  # Tabs overlap by 10 pixels
            
            # Calculate tab positions, considering overlap
            tab_positions = [emacs_x]
            for i in range(1, len(tab_widths)):
                tab_positions.append(tab_positions[i-1] + tab_widths[i-1] - tab_overlap)

            # Draw tabs - Chrome-style rounded trapezoid
            # Ensure the current selected tab is visible
            if current_tab_index >= 0:
                current_tab_start = tab_positions[current_tab_index]
                current_tab_end = current_tab_start + tab_widths[current_tab_index]
                
                # If current tab is not in visible area, adjust scroll position
                if current_tab_start < emacs_x + self.tab_scroll_pos:
                    self.tab_scroll_pos = current_tab_start - emacs_x
                elif current_tab_end > emacs_x + emacs_width + self.tab_scroll_pos:
                    self.tab_scroll_pos = current_tab_end - emacs_x - emacs_width
            
            # First draw inactive tabs, then draw the active tab to ensure it appears on top
            # First pass: draw all inactive tabs
            for i, tab_name in enumerate(tab_names):
                if i == current_tab_index:
                    continue  # Skip current tab, will draw it later
                
                # Consider scroll position
                x = tab_positions[i] - self.tab_scroll_pos
                y = emacs_y
                mode_name = tab_modes[i]
                tab_width = tab_widths[i]
                
                # If tab is completely outside visible area, skip drawing
                if x + tab_width < emacs_x or x > emacs_x + emacs_width:
                    continue
                
                # Set inactive tab colors
                painter.setBrush(inactive_tab_bg)
                painter.setPen(inactive_tab_fg)
                
                # Get tab icon information
                icon_info = self.get_tab_icon_info(tab_name, mode_name)
                icon_path, icon_offset = icon_info
                
                # Create trapezoid path
                path = QPainterPath()
                
                # Trapezoid parameters
                tab_slope = 10  # Trapezoid slope horizontal offset
                corner_radius = 8  # Corner radius
                
                # Draw trapezoid path (with rounded corners)
                # Top-left rounded corner
                path.moveTo(x + tab_slope + corner_radius, y)
                # Top-right rounded corner
                path.lineTo(x + tab_width - tab_slope - corner_radius, y)
                path.arcTo(x + tab_width - tab_slope - corner_radius * 2, y, corner_radius * 2, corner_radius * 2, 90, -90)
                # Bottom-right - straight to bottom, no border
                path.lineTo(x + tab_width, y + tab_height)
                # Bottom-left - straight to bottom, no border
                path.lineTo(x, y + tab_height)
                # Top-left rounded corner
                path.lineTo(x + tab_slope, y + corner_radius)
                path.arcTo(x + tab_slope, y, corner_radius * 2, corner_radius * 2, 180, -90)
                
                # Fill trapezoid, no border
                # Set no border
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(path)
                
                # Restore text color
                painter.setPen(inactive_tab_fg)
                
                # Draw icon
                if icon_path and os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    icon_rect = QRectF(x + tab_slope + self.tab_padding_x, 
                                      y + (tab_height - self.tab_icon_size) / 2,
                                      self.tab_icon_size, 
                                      self.tab_icon_size)
                    icon.paint(painter, icon_rect.toRect())
                
                # Draw tab text
                text_left = x + tab_slope + self.tab_padding_x
                if icon_path and os.path.exists(icon_path):
                    text_left += icon_offset
                
                text_width = (x + tab_width - tab_slope) - text_left - self.tab_padding_x
                text_rect = QRectF(text_left, y, text_width, tab_height)
                
                tab_text = self.get_tab_render_name(tab_name)
                painter.drawText(text_rect, 
                                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter, 
                                tab_text)
            
            # Second pass: draw only the active tab to ensure it's on top
            if current_tab_index >= 0:
                tab_name = tab_names[current_tab_index]
                x = tab_positions[current_tab_index] - self.tab_scroll_pos
                y = emacs_y
                mode_name = tab_modes[current_tab_index]
                tab_width = tab_widths[current_tab_index]
                
                # If tab is completely outside visible area, skip drawing
                if x + tab_width < emacs_x or x > emacs_x + emacs_width:
                    # Restore painting state
                    painter.restore()
                    return
                
                # Set active tab colors
                painter.setBrush(active_tab_bg)
                painter.setPen(active_tab_fg)
                
                # Get tab icon information
                icon_info = self.get_tab_icon_info(tab_name, mode_name)
                icon_path, icon_offset = icon_info
                
                # Create trapezoid path
                path = QPainterPath()
                
                # Trapezoid parameters
                tab_slope = 10  # Trapezoid slope horizontal offset
                corner_radius = 8  # Corner radius
                
                # Draw trapezoid path (with rounded corners)
                # Top-left rounded corner
                path.moveTo(x + tab_slope + corner_radius, y)
                # Top-right rounded corner
                path.lineTo(x + tab_width - tab_slope - corner_radius, y)
                path.arcTo(x + tab_width - tab_slope - corner_radius * 2, y, corner_radius * 2, corner_radius * 2, 90, -90)
                # Bottom-right - straight to bottom, no border
                path.lineTo(x + tab_width, y + tab_height)
                # Bottom-left - straight to bottom, no border
                path.lineTo(x, y + tab_height)
                # Top-left rounded corner
                path.lineTo(x + tab_slope, y + corner_radius)
                path.arcTo(x + tab_slope, y, corner_radius * 2, corner_radius * 2, 180, -90)
                
                # Fill trapezoid, no border
                # Set no border
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(path)
                
                # Restore text color
                painter.setPen(active_tab_fg)
                
                # Draw icon
                if icon_path and os.path.exists(icon_path):
                    icon = QIcon(icon_path)
                    icon_rect = QRectF(x + tab_slope + self.tab_padding_x, 
                                      y + (tab_height - self.tab_icon_size) / 2,
                                      self.tab_icon_size, 
                                      self.tab_icon_size)
                    icon.paint(painter, icon_rect.toRect())
                
                # Draw tab text
                text_left = x + tab_slope + self.tab_padding_x
                if icon_path and os.path.exists(icon_path):
                    text_left += icon_offset
                
                text_width = (x + tab_width - tab_slope) - text_left - self.tab_padding_x
                text_rect = QRectF(text_left, y, text_width, tab_height)
                
                tab_text = self.get_tab_render_name(tab_name)
                painter.drawText(text_rect, 
                                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter, 
                                tab_text)
        
        # Restore painting state
        painter.restore()

    def get_tab_render_name(self, tab_name):
        max_len = 50
        if len(tab_name) <= max_len:
            return tab_name
        else:
            half_len = max_len // 2
            return tab_name[:half_len-2] + '...' + tab_name[-half_len+1:]

    def get_tab_icon_info(self, tab_name, mode_name):
        # Get file info.
        file_info = QtCore.QFileInfo(tab_name)
        file_suffix = file_info.suffix()

        # Calculable mime type base on buffer mode or file suffix.
        if mode_name in MODE_ICON_DICT:
            mime = MODE_ICON_DICT[mode_name]
        elif file_suffix in FILE_SUFFIX_MIME_DICT:
            mime = FILE_SUFFIX_MIME_DICT[file_suffix]
        else:
            mime = self.mime_db.mimeTypeForFile(file_info).name().replace("/", "-")

        # Build icon variables.
        icon_name = "{}.{}".format(mime, "png")
        icon_path = os.path.join(self.icon_cache_dir, icon_name)

        # Return icon info.
        if os.path.exists(icon_path):
            icon_offset = self.tab_icon_size + self.tab_icon_padding_right
            return (icon_path, icon_offset)
        else:
            # Print mime information if not found icon in cache directory.
            print("***** ", tab_name, mode_name, mime)
            return (None, 0)
