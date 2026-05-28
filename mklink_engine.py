import os
import sys
import shutil
import ctypes
import subprocess
import traceback

def is_admin():
    """检测当前进程是否拥有 Windows 管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin(args=None):
    """请求管理员权限重新拉起当前进程"""
    if args is None:
        args = sys.argv
    
    # 重新组合参数，确保路径有引号包围
    script = args[0]
    script_args = args[1:]
    
    # 如果是编译后的 exe，sys.executable 就是 exe 路径
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        params = " ".join([f'"{arg}"' for arg in script_args])
    else:
        executable = sys.executable
        params = f'"{script}" ' + " ".join([f'"{arg}"' for arg in script_args])

    try:
        # shell32.ShellExecuteW 参数: hwnd, lpOperation, lpFile, lpParameters, lpDirectory, nShowCmd
        # "runas" 会触发 UAC 提权对话框
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, None, 1)
        # 如果返回值 <= 32，说明用户拒绝了提权或出错
        return ret > 32
    except Exception as e:
        print(f"提权启动失败: {e}")
        return False

def run_as_normal_user(args=None):
    """
    通过 explorer.exe DCOM 代理重新拉起当前进程为普通用户权限。
    这能强行剥离当前管理员特权令牌，使 OLE 拖放重新起效。
    """
    if args is None:
        args = sys.argv
    
    script = args[0]
    script_args = args[1:]
    
    # 如果是编译后的 exe，sys.executable 就是 exe 路径
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        params = " ".join([f'"{arg}"' for arg in script_args])
        cmd = f'"{executable}" {params}'
    else:
        executable = sys.executable
        params = f'"{script}" ' + " ".join([f'"{arg}"' for arg in script_args])
        cmd = f'"{executable}" {params}'
        
    try:
        # 使用 explorer.exe 来降权启动自身
        subprocess.Popen(f'explorer.exe {cmd}', shell=True)
        return True
    except Exception as e:
        print(f"降权启动失败: {e}")
        return False

def create_link(link_type, link_path, target_path):
    """
    创建 Windows mklink 链接。
    link_type: 'junction' (目录联接), 'symlink_dir' (目录符号链接), 'symlink_file' (文件符号链接), 'hardlink' (文件硬链接)
    link_path: 欲创建的链接路径 (虚拟路径，原本应不存在)
    target_path: 真实的源文件/文件夹路径
    
    返回: (success_bool, message_str)
    """
    # 格式化路径，Windows 命令行更喜欢反斜杠
    link_path = os.path.abspath(link_path).replace('/', '\\')
    target_path = os.path.abspath(target_path).replace('/', '\\')
    
    # 基本检查
    if not os.path.exists(target_path):
        return False, f"错误: 目标路径不存在: {target_path}"
    
    if os.path.exists(link_path):
        return False, f"错误: 链接路径已存在: {link_path}\n请先删除或重命名该位置的同名文件/文件夹。"

    # 判断类型并拼装 mklink 参数
    # mklink 是 cmd 的内置命令，需要通过 cmd.exe /c 来调用
    if link_type == 'junction':
        # 目录联接 (Junction /J)，通常不需要管理员权限
        cmd = f'cmd.exe /c mklink /J "{link_path}" "{target_path}"'
    elif link_type == 'symlink_dir':
        # 目录符号链接 (Symlink /D)，通常需要管理员权限
        if not is_admin():
            return False, "创建目录符号链接需要管理员权限，请点击上方“提权运行”后重试。"
        cmd = f'cmd.exe /c mklink /D "{link_path}" "{target_path}"'
    elif link_type == 'symlink_file':
        # 文件符号链接 (Symlink)，通常需要管理员权限
        if not is_admin():
            return False, "创建文件符号链接需要管理员权限，请点击上方“提权运行”后重试。"
        cmd = f'cmd.exe /c mklink "{link_path}" "{target_path}"'
    elif link_type == 'hardlink':
        # 文件硬链接 (Hardlink /H)，不需要管理员权限
        cmd = f'cmd.exe /c mklink /H "{link_path}" "{target_path}"'
    else:
        return False, f"未知链接类型: {link_type}"

    try:
        # 执行命令，隐藏命令行窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='gbk', # Windows cmd 中文默认 gbk 编码
            startupinfo=startupinfo
        )
        
        if result.returncode == 0:
            return True, f"链接创建成功！\n命令: {cmd}\n链接: {link_path} -> {target_path}"
        else:
            err_msg = result.stderr.strip() or result.stdout.strip() or f"未知错误 (Code: {result.returncode})"
            return False, f"创建链接失败！\n原因: {err_msg}\n命令: {cmd}"
            
    except Exception as e:
        return False, f"执行异常: {str(e)}\n{traceback.format_exc()}"

def safe_migrate_and_link(source_dir, dest_parent_dir, progress_callback=None):
    """
    一键极速搬家：
    1. 将 source_dir 文件夹的所有内容安全迁移到 dest_parent_dir 内（保持原文件夹名）。
    2. 原 source_dir 搬空并删除后，在原 source_dir 位置创建目录联接(/J)，指向 dest_parent_dir 中的新文件夹。
    
    source_dir: 要搬离的源文件夹 (如 C:/Users/houda/MyGames)
    dest_parent_dir: 要放入的目标文件夹 (如 D:/BigFiles)
    progress_callback: 接收 (step_name, percent_int) 的回调函数，用于实时更新 UI 进度条
    
    返回: (success_bool, message_str)
    """
    # 格式化路径
    source_dir = os.path.abspath(source_dir)
    dest_parent_dir = os.path.abspath(dest_parent_dir)
    
    # 1. 基础合法性检验
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        return False, "错误: 需要搬家的源文件夹不存在或不是一个目录。"
        
    if not os.path.exists(dest_parent_dir) or not os.path.isdir(dest_parent_dir):
        return False, "错误: 目标父文件夹不存在或不是一个目录。"

    # 检查是否为包含关系，防止无限递归
    dir_name = os.path.basename(source_dir)
    dest_dir = os.path.join(dest_parent_dir, dir_name)
    
    if dest_dir.startswith(source_dir + os.sep) or source_dir.startswith(dest_dir + os.sep):
        return False, "错误: 源路径与目标路径存在嵌套关系，无法搬家！"

    if os.path.exists(dest_dir):
        return False, f"错误: 目标位置已存在同名文件夹: {dest_dir}\n请先在目标盘重命名或移走同名文件夹。"

    # 2. 扫描文件，计算总数/大小，用于进度展示
    if progress_callback:
        progress_callback("正在扫描源文件夹...", 5)
        
    total_files = 0
    total_size = 0
    file_list = []
    
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                total_size += os.path.getsize(full_path)
            except:
                pass
            total_files += 1
            file_list.append(full_path)

    if progress_callback:
        progress_callback(f"扫描完成: 共 {total_files} 个文件, 共 {total_size / 1024 / 1024:.2f} MB", 10)

    # 3. 跨分区迁移文件夹内容
    # 为保证绝对安全，我们采用“复制-验证-删除-链接”的四步保险法，防止直接 move 过程中由于中断导致数据损坏丢失。
    try:
        # 创建目标文件夹
        os.makedirs(dest_dir, exist_ok=True)
        
        copied_size = 0
        copied_files = 0
        
        # 复制文件夹结构和文件
        for root, dirs, files in os.walk(source_dir):
            # 创建子目录结构
            rel_path = os.path.relpath(root, source_dir)
            if rel_path != ".":
                target_subdir = os.path.join(dest_dir, rel_path)
                os.makedirs(target_subdir, exist_ok=True)
                
            for f in files:
                src_file = os.path.join(root, f)
                rel_file = os.path.relpath(src_file, source_dir)
                dst_file = os.path.join(dest_dir, rel_file)
                
                # 复制文件并保留属性
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                
                try:
                    fsize = os.path.getsize(src_file)
                    copied_size += fsize
                except:
                    fsize = 0
                
                if progress_callback and total_size > 0:
                    percent = 10 + int((copied_size / total_size) * 70) # 占用 10% - 80% 的进度
                    progress_callback(f"正在迁移: {copied_files}/{total_files} ({copied_size / 1024 / 1024:.1f}/{total_size / 1024 / 1024:.1f} MB)", percent)

        # 4. 文件完整性校验
        if progress_callback:
            progress_callback("正在校验文件完整性...", 85)
            
        # 简单比对源和目标的总大小与文件数
        dest_files = 0
        dest_size = 0
        for root, dirs, files in os.walk(dest_dir):
            for f in files:
                dest_files += 1
                try:
                    dest_size += os.path.getsize(os.path.join(root, f))
                except:
                    pass
                    
        if dest_files != total_files or abs(dest_size - total_size) > 1024: # 允许微小的文件系统大小差异
            # 校验失败，安全回滚：删除已复制的目标数据
            try:
                shutil.rmtree(dest_dir)
            except:
                pass
            return False, f"安全校验失败！源端和目标端文件数或大小不一致（源: {total_files}个/{total_size}B，目标: {dest_files}个/{dest_size}B）。\n数据已安全退回，未做任何更改。"

        # 5. 清理原文件夹
        if progress_callback:
            progress_callback("校验通过！正在清理源位置旧数据...", 90)
            
        # 安全删除源文件夹
        try:
            shutil.rmtree(source_dir)
        except Exception as e:
            # 如果删除失败（例如文件正被系统占用），由于新数据已经安全写入目标盘，
            # 我们警告用户并告知目标盘的新位置，但不自动创建链接以防止污染
            return False, f"警告: 数据已复制成功到目标盘，但在清理源位置大文件夹时失败: {str(e)}\n" \
                          f"可能是有文件被系统占用（如微信、游戏仍在后台运行）。\n" \
                          f"请手动关闭占用程序，删除源路径 '{source_dir}' 后，再手动创建目录联接。"

        # 6. 原地建立 Mklink Junction 目录联接
        if progress_callback:
            progress_callback("正在原地创建目录联接...", 95)
            
        success, link_msg = create_link('junction', source_dir, dest_dir)
        
        if success:
            if progress_callback:
                progress_callback("一键搬迁并建链完成！", 100)
            return True, f"【极速搬家成功！】\n1. 数据已安全迁移至: {dest_dir}\n2. 原路径已成功建立目录联接: {source_dir} -> {dest_dir}\n您现在的 C 盘空间已成功释放！"
        else:
            # 这种情况极少发生，因为源文件夹已被清空删除。如果真的失败，提示用户手动建立
            return False, f"数据迁移成功，但在原地创建目录联接失败！\n迁移位置: {dest_dir}\n错误原因: {link_msg}\n您可以通过手动建链模式补建 Junction 链接。"

    except Exception as e:
        # 全局异常捕获，尝试安全回滚
        try:
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
        except:
            pass
        return False, f"搬家过程中发生严重异常: {str(e)}\n数据未受损坏，操作已安全回滚。\n{traceback.format_exc()}"


def is_reparse_point(path):
    """
    通过 Windows 底层 GetFileAttributesW 判定路径是否是重解析点(Reparse Point)
    这能 100% 精准判定 Junction 目录联接、目录符号链接与文件符号链接。
    """
    if not os.path.exists(path) and not os.path.islink(path):
        return False
    
    FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    try:
        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
        return (attrs != -1) and (attrs & FILE_ATTRIBUTE_REPARSE_POINT) != 0
    except:
        # 降级方案
        return os.path.islink(path)


def get_link_target(path):
    """
    获取重解析点（符号链接/Junction）所指向的真实物理目标路径
    """
    path = os.path.abspath(path)
    if not is_reparse_point(path):
        return None
    try:
        # Python 3.8+ 对 Windows 的 Junction 和 Symlink 的 os.readlink 天然支持极佳
        target = os.readlink(path)
        
        # 核心清洗逻辑：Windows 的 readlink 返回的绝对路径常带有长路径前缀 \\?\ 或是网络共享路径 \\?\UNC\ 
        if target.startswith("\\\\?\\UNC\\"):
            target = "\\\\" + target[8:]
        elif target.startswith("\\\\?\\"):
            target = target[4:]
            
        return os.path.abspath(target)
    except Exception as e:
        print(f"读取链接目标失败: {e}")
        return None


def safe_remove_link_only(link_path):
    """
    【高安全机制】仅安全解除/删除链接壳子，100% 避开 rmtree，绝不伤及真实的物理数据！
    """
    link_path = os.path.abspath(link_path)
    if not is_reparse_point(link_path):
        return False, "错误: 该路径不是一个符号链接或 Junction 联接，无法对其执行解除操作。"

    try:
        # 在 Windows 下，Junction 和目录 Symlink 是以特殊的目录形式存在，
        # 我们必须用 os.rmdir 删除它，这只会移去这个链接名，绝不会删除指向的实际数据文件！
        # 如果是文件链接，则用 os.remove
        if os.path.isdir(link_path):
            os.rmdir(link_path)
        else:
            os.remove(link_path)
        return True, f"成功安全解除链接: {link_path}\n真实存储的物理数据完好无损。"
    except Exception as e:
        return False, f"解除链接失败: {str(e)}"


def safe_restore_and_remove_link(link_path, progress_callback=None):
    """
    【双保险还原数据搬迁】
    1. 读取链接所指向的目标真实盘路径。
    2. 安全地将目标盘的所有文件重新剪切移回 link_path 原路径。
    3. 清理掉临时链接与目标盘空壳，100% 彻底恢复至搬家前状态！
    """
    link_path = os.path.abspath(link_path)
    
    # 1. 检验重解析点合法性
    if not is_reparse_point(link_path):
        return False, "错误: 当前选中的路径并不是一个有效的 mklink 链接，无法执行数据移回还原操作。"

    # 2. 读取物理真实目标路径
    target_dir = get_link_target(link_path)
    if not target_dir or not os.path.exists(target_dir):
        return False, f"错误: 无法解析或找不到链接所指向的真实数据路径。\n解析目标: {target_dir}"

    if not os.path.isdir(target_dir):
        return False, "一键彻底还原目前仅支持大文件夹（Junction/Symlink_dir）的反向迁移。"

    if progress_callback:
        progress_callback("检测通过，正在计算还原数据容量...", 5)

    # 3. 扫描真实目标数据
    total_files = 0
    total_size = 0
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                total_size += os.path.getsize(full_path)
            except:
                pass
            total_files += 1

    if progress_callback:
        progress_callback(f"数据扫描完成: 共 {total_files} 个文件, 约 {total_size / 1024 / 1024:.2f} MB", 10)

    # 4. 双保险还原流程：
    # 为防转移失败导致原链接丢失且数据又没迁回来，我们先将链接重命名为临时备份名：
    temp_link_backup = link_path + "_restore_temp_link"
    if os.path.exists(temp_link_backup):
        try:
            os.rmdir(temp_link_backup)
        except:
            return False, "错误: 原地存在残留的还原临时项，请尝试手动清理后再试。"

    try:
        # 重命名链接壳子（Windows 下支持直接对 Junction 壳子重命名）
        os.rename(link_path, temp_link_backup)
    except Exception as e:
        return False, f"初始化还原失败: 无法断开当前链接壳子以腾出位置 ({str(e)})。请确认无后台占用。"

    # 原位置已经空出，现在开始创建真实目标目录，并把文件安全复制回来
    try:
        os.makedirs(link_path, exist_ok=True)
        
        copied_size = 0
        copied_files = 0
        
        for root, dirs, files in os.walk(target_dir):
            rel_path = os.path.relpath(root, target_dir)
            if rel_path != ".":
                orig_subdir = os.path.join(link_path, rel_path)
                os.makedirs(orig_subdir, exist_ok=True)
                
            for f in files:
                src_file = os.path.join(root, f)
                rel_file = os.path.relpath(src_file, target_dir)
                dst_file = os.path.join(link_path, rel_file)
                
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                
                try:
                    fsize = os.path.getsize(src_file)
                    copied_size += fsize
                except:
                    fsize = 0
                
                if progress_callback and total_size > 0:
                    percent = 10 + int((copied_size / total_size) * 70)
                    progress_callback(f"正在反向搬迁: {copied_files}/{total_files} ({copied_size / 1024 / 1024:.1f}/{total_size / 1024 / 1024:.1f} MB)", percent)

        # 5. 校验数据一致性
        if progress_callback:
            progress_callback("移回完成，正在比对校验数据完整性...", 85)
            
        orig_files = 0
        orig_size = 0
        for root, dirs, files in os.walk(link_path):
            for f in files:
                orig_files += 1
                try:
                    orig_size += os.path.getsize(os.path.join(root, f))
                except:
                    pass

        if orig_files != total_files or abs(orig_size - total_size) > 1024:
            # 校验失败！触发安全回退：清理拷回的数据，并将链接还原
            if progress_callback:
                progress_callback("完整性校验未通过！正在进行安全回滚...", 88)
            shutil.rmtree(link_path)
            os.rename(temp_link_backup, link_path)
            return False, "数据移回安全校验未通过！回滚还原成功，数据仍完整保留在目标盘链接中。"

        # 6. 校验大获成功，清理目标盘和临时链接备份
        if progress_callback:
            progress_callback("校验通过！正在清理目标盘与临时链接...", 90)

        # 彻底清空删除目标盘里搬空后的真实文件夹
        shutil.rmtree(target_dir)

        # 删除临时重命名的 Junction 链接壳子
        os.rmdir(temp_link_backup)

        if progress_callback:
            progress_callback("彻底还原并解绑成功！", 100)
            
        return True, f"【彻底移回并还原成功！】\n1. 您的数据已安全回迁至原路径: {link_path}\n2. D盘多余备份及C盘的虚拟链接已安全卸载。\n所有设置均已恢复至搬家前状态！"

    except Exception as e:
        # 异常情况，触发终极回滚
        try:
            if os.path.exists(link_path):
                shutil.rmtree(link_path)
            if os.path.exists(temp_link_backup):
                os.rename(temp_link_backup, link_path)
        except:
            pass
        return False, f"还原过程中发生非预期异常: {str(e)}\n操作已安全回退。\n{traceback.format_exc()}"

