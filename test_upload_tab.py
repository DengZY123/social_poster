#!/usr/bin/env python3
"""
测试上传图文标签点击功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.publisher import XhsPublisher


async def test_upload_tab():
    """测试上传图文标签点击"""
    publisher = XhsPublisher(headless=False, user_data_dir='firefox_profile')
    
    try:
        await publisher.start()
        print('✅ 发布器启动成功')
        
        # 检查登录状态
        if not await publisher.check_login_status():
            print('❌ 用户未登录，请先登录')
            return False
        
        print('✅ 用户已登录')
        
        # 直接访问发布页面
        publish_url = "https://creator.xiaohongshu.com/publish/publish?from=tab_switch"
        await publisher.page.goto(publish_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        print('✅ 访问发布页面成功')
        
        # 测试点击上传图文标签
        result = await publisher._switch_to_image_text_mode()
        
        if result:
            print('✅ 成功点击上传图文标签！')
            
            # 保持页面打开一段时间供观察
            print('页面将保持打开10秒供观察...')
            await asyncio.sleep(10)
            
            return True
        else:
            print('❌ 点击上传图文标签失败')
            return False
            
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        await publisher.close()


def main():
    """主函数"""
    print("测试上传图文标签点击功能")
    print("=" * 40)
    
    try:
        result = asyncio.run(test_upload_tab())
        
        if result:
            print("\n✅ 测试成功")
            return 0
        else:
            print("\n❌ 测试失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 0
    except Exception as e:
        print(f"\n❌ 测试脚本执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())