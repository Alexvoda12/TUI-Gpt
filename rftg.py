import shutil
import subprocess


def check_program_in_path(program_name):
    """
    Проверяет, доступна ли программа в PATH
    """
    return shutil.which(program_name) is not None

def get_program_path(program_name):
    """
    Возвращает полный путь к программе
    """
    return shutil.which(program_name)

def check_python():
    """
    Проверяет установлен ли Python
    """
    if not check_program_in_path('python'):
        return False, None, None
    
    try:
        result = subprocess.run(
            ['python', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            path = get_program_path('python')
            return True, version, path
    except Exception:
        pass
    
    return False, None, None

print(check_python())