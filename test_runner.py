import os
import shutil
import mklink_engine

def run_tests():
    print("==================================================")
    print("[TEST] 开始运行 MKlink GUI 引擎核心功能测试脚本 (增补版)...")
    print("==================================================")
    
    # 定义测试路径
    base_dir = os.path.abspath(".")
    test_src = os.path.join(base_dir, "test_source_folder")
    test_dst = os.path.join(base_dir, "test_destination_parent")
    
    # 确保测试环境干净
    cleanup_test_paths(test_src, test_dst)
    
    try:
        # 1. 准备测试数据
        os.makedirs(test_src, exist_ok=True)
        os.makedirs(test_dst, exist_ok=True)
        
        file1 = os.path.join(test_src, "text1.txt")
        file2 = os.path.join(test_src, "sub", "text2.txt")
        os.makedirs(os.path.dirname(file2), exist_ok=True)
        
        with open(file1, "w", encoding="utf-8") as f:
            f.write("这是搬家测试文件1的内容")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("这是搬家测试文件2的内容，位于子目录")
            
        print("[SUCCESS] 1. 测试数据准备就绪。")
        
        # 2. 测试“极速数据搬迁+建立 Junction 链接”
        print("\n[RUNNING] 2. 正在测试【一键极速搬家】逻辑...")
        
        def progress_log(status, percent):
            print(f"   [搬家进度 {percent}%] {status}")
            
        success, msg = mklink_engine.safe_migrate_and_link(test_src, test_dst, progress_log)
        
        if not success:
            print(f"[FAIL] 一键极速搬家失败: {msg}")
            return False
            
        print(f"[SUCCESS] 极速搬家成功！")
        
        # 3. 验证链接状态与目标探测
        print("\n[RUNNING] 3. 正在测试【重解析点检测与目标解析】...")
        if not mklink_engine.is_reparse_point(test_src):
            print("[FAIL] 错误: 原路径搬迁后未被识别为重解析点(Reparse Point)！")
            return False
        
        resolved_target = mklink_engine.get_link_target(test_src)
        expected_target = os.path.join(test_dst, "test_source_folder")
        if os.path.abspath(resolved_target) != os.path.abspath(expected_target):
            print(f"[FAIL] 错误: 链接指向解析错误！解析值: {resolved_target}, 预期值: {expected_target}")
            return False
            
        print(f"[SUCCESS] 链接探测与目标解析测试通过！指向: {resolved_target}")
        
        # 4. 测试“一键反向搬迁数据还原”
        print("\n[RUNNING] 4. 正在测试【一键数据反向还原与解绑】...")
        
        def progress_log_restore(status, percent):
            print(f"   [还原进度 {percent}%] {status}")
            
        success_rest, msg_rest = mklink_engine.safe_restore_and_remove_link(test_src, progress_log_restore)
        if not success_rest:
            print(f"[FAIL] 一键数据还原失败: {msg_rest}")
            return False
            
        print(f"[SUCCESS] 反向数据还原引擎调用成功！")
        
        # 检验原路径是否变回普通文件夹，且目标已删除，数据完好
        if mklink_engine.is_reparse_point(test_src):
            print("[FAIL] 错误: 还原后原路径依然是链接状态！")
            return False
            
        if os.path.exists(expected_target):
            print("[FAIL] 错误: 还原后目标盘数据文件夹未被清理！")
            return False
            
        with open(os.path.join(test_src, "text1.txt"), "r", encoding="utf-8") as f:
            restored_content = f.read()
        if restored_content != "这是搬家测试文件1的内容":
            print("[FAIL] 错误: 还原后的数据文件损坏或内容不一致！")
            return False
            
        print("[SUCCESS] 数据反向还原连通性、物理目录变动及完整性测试通过！还原大获成功！")

        # 5. 测试高级建链
        print("\n[RUNNING] 5. 正在测试【手动建链模式】(创建普通 Junction)...")
        test_link_only = os.path.join(base_dir, "test_link_only")
        
        # 使用 os.path.lexists 完美防范“死链接”占用冲突
        if os.path.exists(test_link_only) or os.path.lexists(test_link_only):
            try:
                os.rmdir(test_link_only)
            except:
                try:
                    os.remove(test_link_only)
                except:
                    pass
            
        success_adv, msg_adv = mklink_engine.create_link('junction', test_link_only, test_src)
        if not success_adv:
            print(f"[FAIL] 创建高级链接失败: {msg_adv}")
            return False
            
        print(f"[SUCCESS] 手动建链执行成功！")
        
        # 6. 测试单纯安全解绑链接
        print("\n[RUNNING] 6. 正在测试【安全解除链接(仅解绑)】...")
        success_unl, msg_unl = mklink_engine.safe_remove_link_only(test_link_only)
        if not success_unl:
            print(f"[FAIL] 链接安全解绑失败: {msg_unl}")
            return False
            
        if os.path.exists(test_link_only) or os.path.lexists(test_link_only):
            print("[FAIL] 错误: 解绑后链接仍然存在！")
            return False
            
        if not os.path.exists(test_src):
            print("[FAIL] 错误: 安全解绑居然误删了真实的源数据！")
            return False
            
        print("[SUCCESS] 安全解绑验证成功：仅删链接壳，数据100%安全！")

        print("\n==================================================")
        print("[FINISHED] 引擎所有痛点（搬迁、解绑、反向还原）自动化测试 100% 通过！")
        print("==================================================")
        return True

    except Exception as e:
        print(f"[FAIL] 测试执行过程中发生非预期异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理测试现场
        print("\n[CLEAN] 正在清理测试产生的临时文件和链接...")
        cleanup_test_paths(test_src, test_dst)
        test_link_only = os.path.join(base_dir, "test_link_only")
        if os.path.exists(test_link_only) or os.path.lexists(test_link_only):
            try:
                os.rmdir(test_link_only)
            except:
                try:
                    os.remove(test_link_only)
                except:
                    pass
        print("[SUCCESS] 清理完成。")

def cleanup_test_paths(src, dst):
    for path in [src, dst]:
        if os.path.exists(path) or os.path.lexists(path):
            try:
                os.rmdir(path)
            except:
                try:
                    shutil.rmtree(path)
                except:
                    pass

if __name__ == "__main__":
    run_tests()
