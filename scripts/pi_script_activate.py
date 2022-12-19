import os, shutil, stat

PATH = "$HOME/wrx_scripts"

if __name__ == "__main__":
    os.rmdir(PATH)
    os.mkdir(PATH)
    for file_name in os.listdir("scripts"):
        if ".sh" in file_name:
            dst = shutil.copyfile(file_name, PATH)
            st = os.stat(dst)
            os.chmod(dst, st.st_mode | stat.S_IEXEC)
