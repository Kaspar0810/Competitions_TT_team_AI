from cx_Freeze import setup, Executable
from pathlib import Path
import sys
# base_dir = Path(__file__).parent.resolve()
# src_dir = base_dir/"src"
# src_dir = base_dir
build_options = {"packages": ["os", "sys", "PyQt5", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui","pymysql"],
                "excludes": ["tkinter", "test"],
                "include_files": ["UI", "font", "icons", "output", "help", "sign", "regions.xlsx", "backup_db", "log"], 
                "include_msvcr": [True],          
                "bin_includes":["libmysql.dll"], 
                "bin_path_includes":[r"C:\Program Files\MySQL\MySQL Connector C 8.0\lib"]
                }
executables = [Executable("main.py", base="Win32GUI", icon="C_TT.ico", target_name="CTT.exe")]
# executables = [Executable(script=str(src_dir / "main.py"),base="Win32GUI")]

setup(
name="CTT",
version="1.0.0",
description="Qt5 + MySQL Application",
options={"build_exe": build_options, 
         },
executables=executables)

