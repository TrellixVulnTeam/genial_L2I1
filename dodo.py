import datetime
import glob
import importlib
import math
import multiprocessing
import os
import platform
import re
import shutil
import subprocess
import time
import zipfile

from urllib.parse import urlparse

from doit.action import CmdAction
from doit.exceptions import TaskFailed, TaskError
from doit import get_var



default = {
    'pandoc': 'pandoc',
    'pylupdate5': 'pylupdate5',
    'lrelease': 'lrelease',
    'pyrcc5': 'pyrcc5',
    'pyuic5': 'pyuic5',
    'pip': 'pip',
    'pyenv': 'pyenv',
    'pyqtdeploycli': 'pyqtdeploycli',
    'make': 'make',
    'gist': 'gist',
    'sysroot-dir': 'pyqtdeploy',
    'sysroot-cache-dir': os.path.join('pyqtdeploy', 'cache'),
    'qt-source-url': 'https://download.qt.io/official_releases/qt/5.7/5.7.0/single/qt-everywhere-opensource-src-5.7.0.zip',
    'qt-install-dir': os.path.join('pyqtdeploy', 'qt-5.7.0')
}

config = {
    'pandoc': get_var('pandoc', default['pandoc']),
    'pylupdate5': get_var('pylupdate5', default['pylupdate5']),
    'lrelease': get_var('lrelease', default['lrelease']),
    'pyrcc5': get_var('pyrcc5', default['pyrcc5']),
    'pyuic5': get_var('pyuic5', default['pyuic5']),
    'pip': get_var('pip', default['pip']),
    'pyenv': get_var('pyenv', default['pyenv']),
    'pyqtdeploycli': get_var('pyqtdeploycli', default['pyqtdeploycli']),
    'gist': get_var('gist', default['gist']),
    'sysroot-dir': get_var('sysroot-dir', default['sysroot-dir']),
    'sysroot-cache-dir': get_var('sysroot-cache-dir', default['sysroot-cache-dir']),
    'qt-source-url': get_var('qt-source-url', default['qt-source-url']),
    'qt-install-dir': get_var('qt-install-dir', default['qt-install-dir'])
}

DOIT_CONFIG = {
    'default_tasks': [
        'install_dependencies',
        'convert_md',
        'download_icons',
        'download_qtbase_ts',
        'update_ts',
        'generate_qm',
        'generate_locale',
        'generate_icons',
        'generate_plugins',
        'compile_qrc',
        'compile_ui',
        'create_sysroot',
        'create_pdy'
    ]
}


''' ============== '''
''' === CHECKS === '''
''' ============== '''


def is_continuous_integration():
    return os.environ.get('CONTINUOUS_INTEGRATION') is not None


def check_cmd(command):
    if not shutil.which(command):
        return TaskFailed("'{}' not found.".format(command))


def check_module(module):
    try:
        importlib.import_module(module)
    except ImportError:
        return TaskFailed("'{}' module not found.")


''' ================= '''
''' === UTILITIES === '''
''' ================= '''


def update_gist(step, file):
    if is_continuous_integration() and check_cmd('gist') is not TaskFailed:
        gist_id = 'a9ada04ad9ee0b1920994b7a55f22774'
        platform_system = platform.system()
        if platform_system == 'Darwin': platform_system = 'osx'
        if platform_system == 'Linux': platform_system = 'linux'
        if platform_system == 'Windows': platform_system = 'windows'

        command = ['gist', '-f', '{}-{}.log'.format(step, platform_system), '-u', 'a9ada04ad9ee0b1920994b7a55f22774']

        p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate(file)
        p.wait()
        if p.poll() > 0:
            return TaskError("Command '{}' failed.\n{}".format(" ".join(command), p.stderr))


def do_nothing():
    pass


''' ============= '''
''' === TASKS === '''
''' ============= '''


def task_install_dependencies():
    return {
        'file_dep': ['doit_requirements.txt'],
        'actions': [
            CmdAction('{} install -r doit_requirements.txt'.format(config['pip']))
        ],
        'verbosity': 2,
        'setup': ['rehash_pyenv']
    }


def task_rehash_pyenv():
    if not shutil.which(config['pyenv']):
        return {
            'actions': [do_nothing]
        }
    else:
        return {
            'actions': [do_nothing],
            'teardown': [CmdAction('{} rehash'.format(config['pyenv']))]
        }


def task_convert_md():
    files = glob.glob("**.md", recursive=True)

    yield {
        'basename': 'convert_md',
        'name': None,
        'watch': ['.'],
        'doc': 'Converts project .md files to .rst'
    }

    for file in files:
        file_name = os.path.splitext(os.path.basename(file))
        dir_name = os.path.dirname(file)
        rst_file_path = os.path.join(dir_name, file_name[0] + ".rst")
        pandoc = config['pandoc']
        yield {
            'name': file,
            'file_dep': [file],
            'actions': [(check_cmd, [pandoc]), '{} -s -S {} -o {}'.format(pandoc, file, rst_file_path)],
            'targets': [rst_file_path]
        }


def task_download_icons():
    icons = [
        'document-new',
        'document-open',
        'document-save',
        'document-save-as',
        'edit-undo',
        'edit-redo',
        'edit-cut',
        'edit-copy',
        'edit-paste',
        'document-properties',
        'document-print',
        'document-print-preview',
        'application-exit',
        'window-close',
        'list-add',
        'list-remove',
        'go-up',
        'go-down'
    ]
    icons_dir = "genial/resources/icons"

    def download_icon(icon):
        import requests
        from lxml import html

        if not os.path.isfile(get_icon_path(icon)):
            download_page_url = "https://commons.wikimedia.org/wiki/File:Gnome-{}.svg".format(icon)
            download_page_response = requests.get(download_page_url)
            download_page_tree = html.fromstring(download_page_response.text)
            icon_urls = download_page_tree.xpath('//div[@class="fullImageLink"]/a/@href')
            if len(icon_urls) > 0:
                icon_response = requests.get(icon_urls[0])
                os.makedirs(icons_dir, exist_ok=True)
                with open(os.path.join(icons_dir, icon + '.svg'), '+wb') as f:
                    f.write(icon_response.content)

    def get_icon_path(icon):
        return os.path.join(icons_dir, '{}.svg'.format(icon))

    def check_outdated(icon):
        if not os.path.isfile(get_icon_path(icon)):
            return False
        return True

    yield {
        'basename': 'download_icons',
        'name': None,
        'watch': [icons_dir],
        'doc': 'Download icons from GNOME Desktop icons project.'
    }

    for icon in icons:
        icon_path = get_icon_path(icon)
        yield {
            'name': icon,
            'actions': [(check_module, ['requests']), (check_module, ['lxml']), (download_icon, [icon])],
            'targets': [icon_path],
            'uptodate': [(check_outdated, [icon], {})]
        }


def task_download_qtbase_ts():
    locale_dir = "genial/resources/locale"
    languages = []
    for file in os.listdir(locale_dir):
        if file.endswith(".ts"):
            match = re.match(r'genial_(.*)\.ts', file)
            if match is not None:
                languages.append(match.group(1))

    def download_qtbase_ts(language):
        import requests

        language_qtbase_ts_path = get_language_qtbase_ts_path(language)
        if not os.path.isfile(language_qtbase_ts_path):
            url = "http://l10n-files.qt.io/l10n-files/qt5-old/qtbase_{}.ts".format(language)
            response = requests.get(url)
            with open(language_qtbase_ts_path, "wb+") as f:
                f.write(response.content)

    def get_language_qtbase_ts_path(language):
        return os.path.join(locale_dir, 'qtbase_{}.ts'.format(language))

    def check_outdated(language):
        if not os.path.isfile(get_language_qtbase_ts_path(language)):
            return False
        return True

    yield {
        'basename': 'download_qtbase_ts',
        'name': None,
        'watch': [locale_dir],
        'doc': 'Download qtbase file for each supported language other than English.'
    }

    for language in languages:
        language_qtbase_ts_path = get_language_qtbase_ts_path(language)
        yield {
            'name': language,
            'actions': [(check_module, ['requests']), (download_qtbase_ts, [language])],
            'targets': [language_qtbase_ts_path],
            'uptodate': [(check_outdated, [language])]
        }


def task_update_ts():
    genial_pro_path = "genial.pro"

    def generate_pylupdate5_cmd():
        with open(genial_pro_path, 'w+') as pro_file:
            pro_file.write(pro_file_content)
            pro_file.close()
        return "{} -verbose -translate-function '_translate' {}".format(
            config['pylupdate5'], genial_pro_path
        )

    src_dir = "genial"
    sources = []
    forms = []
    translations = []

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                if not (re.match(r'ui_(.*)\.py', file) or re.match(r'__init__\.py', file)):
                    sources.append(os.path.join(root, file))
            elif file.endswith(".ui"):
                forms.append(os.path.join(root, file))
            elif file.endswith(".ts"):
                if not re.match(r'qtbase_(.*)\.ts', file):
                    translations.append(os.path.join(root, file))

    pro_file_content = "SOURCES = " + " \\\n".join(sources) + "\n\n"
    pro_file_content += "FORMS = " + " \\\n".join(forms) + "\n\n"
    pro_file_content += "TRANSLATIONS = " + " \\\n".join(translations)

    return {
        'task_dep': ['download_qtbase_ts'],
        'actions': [(check_cmd, ['pylupdate5']), CmdAction(generate_pylupdate5_cmd, [pro_file_content])],
        'targets': [genial_pro_path] + translations,
        'verbosity': 2
    }


def task_generate_qm():
    locale_dir = "genial/resources/locale"
    languages = []

    for file in os.listdir(locale_dir):
        if file.endswith(".ts"):
            match = re.match(r'genial_(.*)\.ts', file)
            if match is not None:
                languages.append(match.group(1))

    yield {
        'basename': 'generate_qm',
        'name': None,
        'watch': [locale_dir],
        'doc': 'Generate .qm files from .ts files',
        'task_dep': ['update_ts']
    }

    for language in languages:
        genial_ts_file = os.path.join(locale_dir, "genial_{}.ts".format(language))
        genial_qm_file = os.path.join(locale_dir, "genial_{}.qm".format(language))
        qtbase_ts_file = os.path.join(locale_dir, "qtbase_{}.ts".format(language))
        qtbase_qm_file = os.path.join(locale_dir, "qtbase_{}.qm".format(language))

        lrelease = config['lrelease']

        yield {
            'name': 'genial_' + language,
            'actions': [
                (check_cmd, [lrelease]),
                CmdAction('{} {} -qm {}'.format(lrelease, genial_ts_file, genial_qm_file))
            ],
            'file_dep': [genial_ts_file],
            'targets': [genial_qm_file],
            'task_dep': ['update_ts']
        }

        yield {
            'name': 'qtbase_' + language,
            'actions': [
                (check_cmd, [lrelease]),
                CmdAction('{} {} -qm {}'.format(config['lrelease'], qtbase_ts_file, qtbase_qm_file))
            ],
            'file_dep': [qtbase_ts_file],
            'targets': [qtbase_qm_file],
            'task_dep': ['update_ts']
        }


def task_generate_locale():
    def create_rcc():
        if files_found:
            with open(target, 'w+') as f:
                f.write(qrc_content)

    resources_dir = "genial/resources"
    locale_dir = os.path.join(resources_dir, "locale")
    target = os.path.join(resources_dir, 'locale.qrc')
    qrc_content = "<RCC>"
    qrc_content += '\n  <qresource prefix="/locale">'
    files_found = []
    os.makedirs(locale_dir, exist_ok=True)
    for file in os.listdir(locale_dir):
        if file.endswith(".qm"):
            files_found.append(os.path.join(locale_dir, file))
            qrc_content += "\n    <file alias='{}'>locale/{}</file>".format(file, file)
    qrc_content += "\n  </qresource>"
    qrc_content += "\n</RCC>\n"

    return {
        'task_dep': ['generate_qm'],
        'file_dep': files_found,
        'actions': [create_rcc],
        'targets': [target],
        'verbosity': 2
    }


def task_generate_icons():
    def create_rcc():
        if files_found:
            with open(target, 'w+') as f:
                f.write(qrc_content)

    resources_dir = "genial/resources"
    icons_dir = os.path.join(resources_dir, "icons")
    target = os.path.join(resources_dir, 'icons.qrc')
    qrc_content = "<RCC>"
    qrc_content += '\n  <qresource prefix="/icons">'
    files_found = []
    os.makedirs(icons_dir, exist_ok=True)
    for file in os.listdir(icons_dir):
        if file.endswith(".svg"):
            files_found.append(os.path.join(icons_dir, file))
            qrc_content += "\n    <file alias='{}'>icons/{}</file>".format(file, file)
    qrc_content += "\n  </qresource>"
    qrc_content += "\n</RCC>\n"

    return {
        'task_dep': ['download_icons'],
        'file_dep': files_found,
        'actions': [create_rcc],
        'targets': [target],
        'verbosity': 2
    }


def task_generate_plugins():
    def create_rcc():
        if files_found:
            with open(target, 'w+') as f:
                f.write(qrc_content)

    resources_dir = "genial/resources"
    plugins_dir = os.path.join(resources_dir, "plugins")
    target = os.path.join(resources_dir, 'plugins.qrc')
    qrc_content = "<RCC>"
    qrc_content += '\n  <qresource prefix="/icons">'
    files_found = []
    os.makedirs(plugins_dir, exist_ok=True)

    current_dir = os.getcwd()
    os.chdir(resources_dir)
    for root, dirs, files in os.walk("plugins"):
        for file in files:
            if file.endswith(".genial-plugin") or file.endswith(".py"):
                if platform.system() != "Windows":
                    plugin_dir = root.replace("plugins/", "")
                else:
                    plugin_dir = root.replace("plugins\\", "")
                files_found.append(os.path.join(plugins_dir, plugin_dir, file))
                qrc_content += "\n    <file alias='{}'>{}</file>".format(
                    os.path.join(plugin_dir, file),
                    os.path.join(root, file)
                )
    os.chdir(current_dir)

    qrc_content += "\n  </qresource>"
    qrc_content += "\n</RCC>\n"

    return {
        'file_dep': files_found,
        'actions': [create_rcc],
        'targets': [target],
        'verbosity': 2
    }


def task_compile_qrc():
    resources_dir = "genial/resources"

    yield {
        'basename': 'compile_qrc',
        'name': None,
        'watch': [resources_dir],
        'doc': 'Compiles *.qrc files to *_rc.py',
        'task_dep': ['generate_locale', 'generate_icons', 'generate_plugins']
    }

    for file in os.listdir(resources_dir):
        if file.endswith(".qrc"):
            output_file = re.sub(r'(.*)\.qrc', r'\1_rc.py', file)
            file_full_path = os.path.join(resources_dir, file)
            output_file_full_path = os.path.join(resources_dir, output_file)

            pyrcc5 = config['pyrcc5']

            yield {
                'name': file,
                'actions': [(check_cmd, [pyrcc5]),
                            CmdAction('{} {} -o {}'.format(pyrcc5, file_full_path, output_file_full_path))],
                'file_dep': [file_full_path],
                'targets': [output_file_full_path]
            }


def task_compile_ui():
    ui_dir = "genial/ui"
    gen_dir = "genial/views/gen"

    yield {
        'basename': 'compile_ui',
        'name': None,
        'watch': [ui_dir],
        'doc': 'Compiles *.ui files to ui_*.py'
    }

    for file in os.listdir(ui_dir):
        if file.endswith(".ui"):
            output_file = re.sub(r'(.*)\.ui', r'ui_\1.py', file)
            file_full_path = os.path.join(ui_dir, file)
            output_file_full_path = os.path.join(gen_dir, output_file)

            pyuic5 = config['pyuic5']

            yield {
                'name': file,
                'actions': [
                    (check_cmd, [pyuic5]),
                    CmdAction(
                        '{} --import-from=genial.resources {} -o {}'.format(
                            pyuic5, file_full_path, output_file_full_path
                        )
                    )
                ],
                'file_dep': [file_full_path],
                'targets': [output_file_full_path]
            }


def task_create_sysroot():
    target_dir = config['sysroot-dir']

    def create_dir():
        os.makedirs(target_dir, exist_ok=True)

    return {
        'actions': [create_dir],
        'targets': [target_dir]
    }


def task_download_qt_source():
    qt_url = config['qt-source-url']
    target_file = os.path.basename(urlparse(qt_url).path)
    target_file_path = os.path.join(config['sysroot-cache-dir'], target_file)
    os.makedirs(config['sysroot-cache-dir'], exist_ok=True)

    def download_file():
        import requests

        r = requests.get(qt_url, stream=True)
        start = datetime.datetime.now()
        moment_ago = start
        downloaded_size = 0
        print("Downloading {}:".format(qt_url))
        with open(target_file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                now = datetime.datetime.now()
                if moment_ago + datetime.timedelta(seconds=1) < now:
                    print(
                        "\rDownloaded {}%".format(
                            math.floor(downloaded_size/int(r.headers['content-length']) * 100)
                        ),
                        end=""
                    )
                    moment_ago = now
        print("Finished downloading '{}'.".format(qt_url))

    return {
        'actions': [(check_module, ['requests']), download_file],
        'targets': [target_file_path],
        'verbosity': 2
    }


def task_extract_qt_source():
    qt_url = config['qt-source-url']
    zip_file = os.path.basename(urlparse(qt_url).path)
    zip_file_path = os.path.join(config['sysroot-cache-dir'], zip_file)
    target_dir = os.path.splitext(zip_file)[0]
    target_path = os.path.join(config['sysroot-cache-dir'], target_dir)
    os.makedirs(target_path, exist_ok=True)

    def unzip_file():
        with zipfile.ZipFile(zip_file_path) as zf:
            zf.extractall(path=target_path)

    return {
        'actions': [unzip_file],
        'file_dep': [zip_file_path],
        'targets': [target_path],
        'verbosity': 2
    }


def task_configure_qt_source():
    qt_url = config['qt-source-url']
    zip_file = os.path.basename(urlparse(qt_url).path)
    source_dir = os.path.splitext(zip_file)[0]
    source_path = os.path.join(config['sysroot-cache-dir'], source_dir)
    log_path = ""

    def configure():
        current_path = os.getcwd()
        os.chdir(source_path)

        command = ['./configure', '-prefix', config['qt-install-dir'], '-static', '-release', '-nomake', 'examples']

        try:
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
        except FileNotFoundError as e:
            raise e

        if p.poll() is None:
            start_time = datetime.datetime.now()
            moment_ago = start_time
            while p.poll() is None:
                now = datetime.datetime.now()
                if moment_ago + datetime.timedelta(seconds=30) > now:
                    print('*', end="")
                time.sleep(1)
            print("")

        os.chdir(current_path)

        nonlocal log_path
        log_path = os.path.join(source_path, 'configure.log')
        print('Configure log written to {}'.format(log_path))
        with open(log_path, 'w') as f:
            f.write(p.communicate()[0])

        if p.poll() > 0:
            return TaskError("Command '{}' failed.\n{}".format(" ".join(command), p.stderr))

    return {
        'actions': [configure, (update_gist, ['configure', log_path])],
        'file_dep': [source_path],
        'verbosity': 2
    }


def task_make_qt_source():
    qt_url = config['qt-source-url']
    zip_file = os.path.basename(urlparse(qt_url).path)
    source_dir = os.path.splitext(zip_file)[0]
    source_path = os.path.join(config['sysroot-cache-dir'], source_dir)
    log_path = ""

    def make():
        current_path = os.getcwd()
        os.chdir(source_path)

        command = ['make', '-j{}'.format((multiprocessing.cpu_count() + 1))]

        try:
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
        except FileNotFoundError as e:
            raise e

        if p.poll() is None:
            start_time = datetime.datetime.now()
            moment_ago = start_time
            while p.poll() is None:
                now = datetime.datetime.now()
                if moment_ago + datetime.timedelta(seconds=30) > now:
                    print('*', end="")
                time.sleep(1)
            print("")

        os.chdir(current_path)

        nonlocal log_path
        log_path = os.path.join(source_path, 'make.log')
        print('Make log written to {}'.format(log_path))
        with open(log_path, 'w') as f:
            f.write(p.communicate()[0])

        if p.poll() > 0:
            return TaskError("Command '{}' failed.\n{}".format(" ".join(command), p.stderr))

    return {
        'actions': [make, (update_gist, ['make', log_path])],
        'file_dep': [source_path],
        'verbosity': 2
    }


def task_make_install_qt_source():
    qt_url = config['qt-source-url']
    zip_file = os.path.basename(urlparse(qt_url).path)
    source_dir = os.path.splitext(zip_file)[0]
    source_path = os.path.join(config['sysroot-cache-dir'], source_dir)
    log_path = ""

    os.makedirs(config['qt-install-dir'], exist_ok=True)

    def make_install():
        current_path = os.getcwd()
        os.chdir(source_path)

        command = ['make', 'install', '-j{}'.format((multiprocessing.cpu_count() + 1))]

        try:
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True)
        except FileNotFoundError as e:
            raise e

        if p.poll() is None:
            start_time = datetime.datetime.now()
            moment_ago = start_time
            while p.poll() is None:
                now = datetime.datetime.now()
                if moment_ago + datetime.timedelta(seconds=30) > now:
                    print('*', end="")
                time.sleep(1)
            print("")

        os.chdir(current_path)

        nonlocal log_path
        log_path = os.path.join(source_path, 'make_install.log')
        print('Make install log written to {}'.format(log_path))
        with open(log_path, 'w') as f:
            f.write(p.communicate()[0])

        if p.poll() > 0:
            return TaskError("Command '{}' failed.\n{}".format(" ".join(command), p.stderr))

    return {
        'actions': [make_install, (update_gist, ['make_install', log_path])],
        'file_dep': [source_path],
        'verbosity': 2
    }


def task_create_pdy():
    target_pdy = 'genial.pdy'

    default_python_major = 3
    default_python_minor = 5
    default_python_patch = 2
    default_source_dir = os.path.join(
        os.path.expanduser('~'),
        '.pyenv/sources/{}.{}.{}/Python'.format(
            default_python_major, default_python_minor, default_python_patch
        )
    )
    default_include_dir = os.path.join(
        os.path.expanduser('~'),
        '.pyenv/versions/{}.{}.{}/include/python{}.{}m'.format(
            default_python_major, default_python_minor, default_python_patch,
            default_python_major, default_python_minor
        )
    )
    default_python_library = os.path.join(
        os.path.expanduser('~'),
        '.pyenv/versions/{}.{}.{}/lib/libpython{}.{}m.a'.format(
            default_python_major, default_python_minor, default_python_patch,
            default_python_major, default_python_minor
        )
    )
    default_standard_library_dir = os.path.join(
        os.path.expanduser('~'),
        '.pyenv/versions/{}.{}.{}/lib/python{}.{}'.format(
            default_python_major, default_python_minor, default_python_patch,
            default_python_major, default_python_minor
        )
    )

    exclusion_list = [
        re.compile('.*\.pyc$'), re.compile('.*\.pyd$'), re.compile('.*\.pyo$'),
        re.compile('.*\.pyx$'), re.compile('.*\.pxi$'), re.compile('^__pycache__$'),
        re.compile('.*-info$'), re.compile('.*-info$'), re.compile('^EGG_INFO$'),
        re.compile('.*\.so$'), re.compile('^\.DS_Store$')
    ]

    def write_pdy_to_file(python_major, python_minor, python_patch, source_dir,
                          include_dir, python_library, standard_library_dir):
        from lxml import etree

        def package_content(path):
            def is_excluded(x):
                for exclusion_element in exclusion_list:
                    if exclusion_element.search(x):
                        return True

            name = os.path.basename(os.path.normpath(path))
            node = etree.Element('PackageContent')
            node.set('name', name)
            node.set('included', "1")
            if os.path.isfile(path):
                node.set('isdirectory', '0')
            else:
                node.set('isdirectory', '1')
                for file in os.listdir(path):
                    if not is_excluded(file):
                        node.append(package_content(os.path.join(path, file)))
            return node

        project = etree.Element("Project")
        project.set('version', "6")

        python = etree.SubElement(project, "Python")
        python.set('hostinterpreter', '')
        python.set('major', '{}'.format(python_major))
        python.set('minor', '{}'.format(python_minor))
        python.set('patch', '{}'.format(python_patch))
        python.set('platformpython', "linux-* macx win32")
        python.set('sourcedir', source_dir)
        python.set('ssl', "0")
        python.set('targetincludedir', include_dir)
        python.set('targetlibrary', python_library)
        python.set('targetstdlibdir', standard_library_dir)

        application = etree.SubElement(project, "Application")
        application.set('entrypoint', "")
        application.set('isbundle', "1")
        application.set('isconsole', "0")
        application.set('ispyqt5', "1")
        application.set('name', "Genial")
        application.set('script', "genial.py")
        application.set('syspath', "")

        package = etree.SubElement(application, "Package")
        package.set('name', ".")
        package.append(package_content('genial'))
        genial_py_file = etree.SubElement(package, "PackageContent")
        genial_py_file.set('name', 'genial.py')
        genial_py_file.set('included', "1")
        genial_py_file.set('isdirectory', "0")
        license_file = etree.SubElement(package, "PackageContent")
        license_file.set('name', 'LICENSE')
        license_file.set('included', "1")
        license_file.set('isdirectory', "0")

        exclude_pyc = etree.SubElement(package, "Exclude")
        exclude_pyc.set('name', "*.pyc")
        exclude_pyd = etree.SubElement(package, "Exclude")
        exclude_pyd.set('name', "*.pyd")
        exclude_pyo = etree.SubElement(package, "Exclude")
        exclude_pyo.set('name', "*.pyo")
        exclude_pyx = etree.SubElement(package, "Exclude")
        exclude_pyx.set('name', "*.pyx")
        exclude_pxi = etree.SubElement(package, "Exclude")
        exclude_pxi.set('name', "*.pxi")
        exclude_pycache = etree.SubElement(package, "Exclude")
        exclude_pycache.set('name', "__pycache__")
        exclude_info = etree.SubElement(package, "Exclude")
        exclude_info.set('name', "*-info")
        exclude_egginfo = etree.SubElement(package, "Exclude")
        exclude_egginfo.set('name', "EGG_INFO")
        exclude_so = etree.SubElement(package, "Exclude")
        exclude_so.set('name', "*.so")

        pyqtmodule_sip = etree.SubElement(project, "PyQtModule")
        pyqtmodule_sip.set('name', "sip")
        pyqtmodule_qtcore = etree.SubElement(project, "PyQtModule")
        pyqtmodule_qtcore.set('name', "QtCore")
        pyqtmodule_qtwidgets = etree.SubElement(project, "PyQtModule")
        pyqtmodule_qtwidgets.set('name', "QtWidgets")
        pyqtmodule_qtgui = etree.SubElement(project, "PyQtModule")
        pyqtmodule_qtgui.set('name', "QtGui")

        others = etree.SubElement(project, "Others")
        others.set('builddir', "build")
        others.set('qmake', "$SYSROOT/qt-5.5.1/bin/qmake")

        with open(target_pdy, 'wb') as f:
            f.write(etree.tostring(project, pretty_print=True, xml_declaration=True, encoding='utf-8'))

    return {
        'actions': [(check_module, ['lxml']), (check_cmd, ['pyqtdeploycli']), write_pdy_to_file],
        'params': [
            {
                'name': 'python_major',
                'long': 'python-major',
                'type': int,
                'default': default_python_major,
                'help': 'Python major release to use.'
            },
            {
                'name': 'python_minor',
                'long': 'python-minor',
                'type': int,
                'default': default_python_minor,
                'help': 'Python minor release to use.'
            },
            {
                'name': 'python_patch',
                'long': 'python-patch',
                'type': int,
                'default': default_python_patch,
                'help': 'Python patch release to use.'
            },
            {
                'name': 'source_dir',
                'long': 'source-dir',
                'type': str,
                'default': default_source_dir,
                'help': 'Python source directory.'
            },
            {
                'name': 'include_dir',
                'long': 'include-dir',
                'type': str,
                'default': default_include_dir,
                'help': 'Target include directory.'
            },
            {
                'name': 'python_library',
                'long': 'python-library',
                'type': str,
                'default': default_python_library,
                'help': 'Target Python library.'
            },
            {
                'name': 'standard_library_dir',
                'long': 'standard-library-dir',
                'type': str,
                'default': default_standard_library_dir,
                'help': 'Target standard library directory.'
            }
        ],
        'targets': [target_pdy],
        'verbosity': 2
    }
