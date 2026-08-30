# project-tools/project_cleaner.py
import os
import shutil
from pathlib import Path

class ProjectCleaner:
    def __init__(self, project_root: str, dry_run: bool = True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.deleted = []
        self.skipped = []
        self.found = []
    
    def clean_pycache(self):
        """حذف مجلدات __pycache__"""
        print("🧹 تنظيف مجلدات __pycache__...")
        for root, dirs, files in os.walk(self.project_root):
            if "__pycache__" in dirs:
                pycache_path = Path(root) / "__pycache__"
                self.found.append(str(pycache_path))
                if not self.dry_run:
                    shutil.rmtree(pycache_path)
                    self.deleted.append(str(pycache_path))
                else:
                    print(f"  📂 ستحذف: {pycache_path}")
    
    def clean_pyc_files(self):
        """حذف ملفات .pyc"""
        print("\n🧹 تنظيف ملفات .pyc...")
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".pyc"):
                    pyc_path = Path(root) / file
                    self.found.append(str(pyc_path))
                    if not self.dry_run:
                        os.remove(pyc_path)
                        self.deleted.append(str(pyc_path))
                    else:
                        print(f"  📄 ستحذف: {pyc_path}")
    
    def clean_node_modules(self):
        """تنظيف مجلد node_modules"""
        node_modules_path = self.project_root / "frontend" / "node_modules"
        if node_modules_path.exists():
            self.found.append(str(node_modules_path))
            if not self.dry_run:
                shutil.rmtree(node_modules_path)
                self.deleted.append(str(node_modules_path))
            else:
                print(f"\n📂 ستحذف: node_modules (سيتم إعادة تثبيتها لاحقاً)")
    
    def clean_dist(self):
        """تنظيف مجلد dist"""
        dist_path = self.project_root / "frontend" / "dist"
        if dist_path.exists():
            self.found.append(str(dist_path))
            if not self.dry_run:
                shutil.rmtree(dist_path)
                self.deleted.append(str(dist_path))
            else:
                print(f"\n📂 ستحذف: dist (سيتم إعادة بنائها لاحقاً)")
    
    def clean_empty_folders(self):
        """حذف المجلدات الفارغة"""
        print("\n🧹 تنظيف المجلدات الفارغة...")
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                if not any(dir_path.iterdir()):
                    self.found.append(str(dir_path))
                    if not self.dry_run:
                        os.rmdir(dir_path)
                        self.deleted.append(str(dir_path))
                    else:
                        print(f"  📂 ستحذف مجلد فارغ: {dir_path}")
    
    def find_unused_modules(self):
        """العثور على وحدات غير مستخدمة"""
        print("\n🔍 البحث عن وحدات غير مكتملة...")
        backend_modules = self.project_root / "backend" / "app" / "modules"
        if backend_modules.exists():
            for module in backend_modules.iterdir():
                if module.is_dir() and not module.name.startswith("__"):
                    essential_files = ["router.py", "service.py", "models.py"]
                    has_files = any((module / f).exists() for f in essential_files)
                    if not has_files:
                        print(f"  ⚠️ وحدة غير مكتملة: {module.name}")
    
    def run(self):
        """تشغيل التنظيف"""
        print("="*80)
        print("🧹 أداة تنظيف المشروع")
        print("="*80)
        print(f"📌 وضع التجربة (Dry Run): {'نشط ✅' if self.dry_run else 'غير نشط ❌'}")
        print("   (في وضع التجربة، سيتم عرض الملفات فقط دون حذفها)")
        print("-"*60)
        
        self.clean_pycache()
        self.clean_pyc_files()
        self.clean_node_modules()
        self.clean_dist()
        self.clean_empty_folders()
        self.find_unused_modules()
        
        print("\n" + "-"*60)
        if self.dry_run:
            print(f"\n📋 تم العثور على {len(self.found)} عنصر يمكن حذفه")
            print("\n🔴 للتشغيل الفعلي، قم بتعديل السطر الأخير إلى:")
            print("   cleaner = ProjectCleaner('..', dry_run=False)")
            print("   cleaner.run()")
        else:
            print(f"\n✅ تم حذف {len(self.deleted)} عنصر")
            print(f"⏭️  تم تخطي {len(self.skipped)} عنصر")
        
        print("="*80)

# تشغيل التنظيف
if __name__ == "__main__":
    # ابدأ بوضع التجربة (dry_run=True) للمعاينة
    cleaner = ProjectCleaner("..", dry_run=True)
    cleaner.run()