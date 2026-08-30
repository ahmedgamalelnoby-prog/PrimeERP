# project-tools/project_analyzer.py
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ProjectAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "backend": {},
            "frontend": {},
            "modules": {},
            "issues": [],
            "recommendations": []
        }
    
    def analyze_backend(self):
        """تحليل الـ Backend بالكامل"""
        backend_path = self.project_root / "backend" / "app"
        
        # 1. تحليل الـ Modules
        modules_dir = backend_path / "modules"
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("__"):
                    module_name = module_dir.name
                    self.results["backend"][module_name] = self._analyze_module(module_dir)
        
        # 2. تحليل الـ API Routes
        api_path = backend_path / "api" / "v1"
        if api_path.exists():
            self.results["backend"]["api_routes"] = self._analyze_routes(api_path)
        
        # 3. تحليل الـ Models
        models_path = backend_path / "database" / "models.py"
        if models_path.exists():
            self.results["backend"]["models_count"] = self._count_models(models_path)
    
    def _analyze_module(self, module_path: Path) -> Dict:
        """تحليل وحدة معينة"""
        module_info = {
            "exists": True,
            "files": [],
            "has_models": False,
            "has_schemas": False,
            "has_service": False,
            "has_router": False,
            "has_api": False,
            "completeness": 0,
            "sub_modules": {}
        }
        
        # فحص الملفات الأساسية
        essential_files = {
            "models.py": "has_models",
            "schemas.py": "has_schemas",
            "service.py": "has_service",
            "router.py": "has_router",
            "api.py": "has_api",
            "__init__.py": "has_init"
        }
        
        for file, attr in essential_files.items():
            if (module_path / file).exists():
                module_info[attr] = True
                module_info["files"].append(file)
        
        # فحص المجلدات الفرعية
        for sub_dir in module_path.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith("__"):
                sub_name = sub_dir.name
                sub_info = self._analyze_module(sub_dir)
                if sub_info["files"] or sub_info.get("has_models"):
                    module_info["sub_modules"][sub_name] = sub_info
        
        # حساب نسبة الاكتمال
        completeness_score = sum([
            module_info["has_models"],
            module_info["has_schemas"],
            module_info["has_service"],
            module_info["has_router"],
            module_info["has_api"]
        ])
        module_info["completeness"] = (completeness_score / 5) * 100
        
        return module_info
    
    def _analyze_routes(self, router_path: Path) -> Dict:
        """تحليل المسارات الموجودة"""
        routes = {}
        if (router_path / "router.py").exists():
            with open(router_path / "router.py", 'r', encoding='utf-8') as f:
                content = f.read()
                # البحث عن المسارات
                route_patterns = re.findall(r'@router\.(get|post|put|delete|patch)\([\'"](.*?)[\'"]', content)
                if route_patterns:
                    routes["endpoints"] = [f"{method.upper()} {path}" for method, path in route_patterns]
                
                # البحث عن prefixes
                prefix_match = re.search(r'prefix=[\'"](.*?)[\'"]', content)
                if prefix_match:
                    routes["prefix"] = prefix_match.group(1)
        
        return routes
    
    def _count_models(self, models_path: Path) -> int:
        """حساب عدد النماذج في ملف models.py"""
        try:
            with open(models_path, 'r', encoding='utf-8') as f:
                content = f.read()
                models = re.findall(r'class\s+(\w+)\(.*Base.*\):', content)
                return len(models)
        except:
            return 0
    
    def analyze_frontend(self):
        """تحليل الـ Frontend بالكامل"""
        frontend_path = self.project_root / "frontend" / "src"
        
        # 1. تحليل الـ Modules
        modules_dir = frontend_path / "modules"
        if modules_dir.exists():
            for module_dir in modules_dir.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("_"):
                    module_name = module_dir.name
                    self.results["frontend"][module_name] = self._analyze_frontend_module(module_dir)
        
        # 2. تحليل الـ Pages
        for root, dirs, files in os.walk(frontend_path):
            for file in files:
                if file.endswith("Page.tsx") or file.endswith("page.tsx"):
                    page_path = Path(root) / file
                    module_name = page_path.parent.parent.name if page_path.parent.parent.name not in ["pages", "modules"] else "root"
                    if module_name not in self.results["frontend"]:
                        self.results["frontend"][module_name] = {}
                    self.results["frontend"][module_name]["pages"] = self.results["frontend"][module_name].get("pages", []) + [file]
        
        # 3. تحليل الـ Routes
        routes_path = frontend_path / "app" / "router" / "routes.ts"
        if routes_path.exists():
            with open(routes_path, 'r', encoding='utf-8') as f:
                content = f.read()
                route_patterns = re.findall(r'path:\s*[\'"](.*?)[\'"]', content)
                self.results["frontend"]["defined_routes"] = route_patterns
        
        # 4. فحص المكونات المشتركة
        components_path = frontend_path / "components"
        if components_path.exists():
            self.results["frontend"]["shared_components"] = self._list_components(components_path)
    
    def _analyze_frontend_module(self, module_path: Path) -> Dict:
        """تحليل وحدة Frontend معينة"""
        module_info = {
            "exists": True,
            "has_pages": False,
            "has_services": False,
            "has_hooks": False,
            "has_types": False,
            "has_api": False,
            "files": []
        }
        
        # فحص المجلدات الفرعية
        sub_dirs = ["pages", "services", "hooks", "types", "api", "components"]
        for sub_dir in sub_dirs:
            if (module_path / sub_dir).exists():
                module_info[f"has_{sub_dir}"] = True
                module_info["files"].append(f"{sub_dir}/...")
        
        # فحص الملفات الرئيسية
        essential_files = ["index.ts", "routes.tsx"]
        for file in essential_files:
            if (module_path / file).exists():
                module_info["files"].append(file)
        
        return module_info
    
    def _list_components(self, components_path: Path) -> List[str]:
        """سرد جميع المكونات الموجودة"""
        components = []
        for root, dirs, files in os.walk(components_path):
            for file in files:
                if file.endswith(".tsx") and not file.startswith("index"):
                    rel_path = Path(root) / file
                    components.append(str(rel_path.relative_to(components_path)))
        return components[:20]
    
    def generate_report(self):
        """إنشاء تقرير شامل"""
        report = []
        report.append("="*80)
        report.append(f"📊 تقرير تحليل المشروع - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("="*80)
        
        # تقرير الـ Backend
        report.append("\n📦 **الوحدات النمطية في Backend:**")
        report.append("-"*60)
        
        backend_modules = {}
        for module, info in self.results["backend"].items():
            if module == "api_routes" or module == "models_count":
                continue
            if isinstance(info, dict) and "completeness" in info:
                backend_modules[module] = info["completeness"]
        
        # ترتيب الوحدات حسب الاكتمال
        sorted_modules = sorted(backend_modules.items(), key=lambda x: x[1], reverse=True)
        for module, completeness in sorted_modules:
            status = "✅" if completeness >= 60 else "⚠️" if completeness >= 30 else "❌"
            report.append(f"{status} {module}: {completeness:.0f}% مكتمل")
        
        # عرض الوحدات الفرعية
        for module, info in self.results["backend"].items():
            if isinstance(info, dict) and info.get("sub_modules"):
                for sub, sub_info in info["sub_modules"].items():
                    if sub_info.get("completeness", 0) > 0:
                        report.append(f"   └── 📂 {sub}: {sub_info['completeness']:.0f}%")
        
        # عدد النماذج
        if "models_count" in self.results["backend"]:
            report.append(f"\n📊 عدد النماذج في قاعدة البيانات: {self.results['backend']['models_count']}")
        
        # تقرير الـ Frontend
        report.append("\n\n📱 **الوحدات النمطية في Frontend:**")
        report.append("-"*60)
        for module, info in self.results["frontend"].items():
            if module == "shared_components" or module == "defined_routes" or module == "root":
                continue
            if isinstance(info, dict):
                page_count = len(info.get("pages", []))
                has_services = info.get("has_services", False)
                status = "✅" if page_count > 0 else "⚠️" if has_services else "❌"
                report.append(f"{status} {module}: {page_count} صفحة")
        
        # المكونات المشتركة
        if "shared_components" in self.results["frontend"]:
            report.append(f"\n🧩 **المكونات المشتركة:** {len(self.results['frontend']['shared_components'])} مكون")
        
        # المسارات المعرفة
        if "defined_routes" in self.results["frontend"]:
            routes = self.results["frontend"]["defined_routes"]
            report.append(f"\n🔗 **المسارات المعرفة:** {len(routes)} مسار")
            report.append("المسارات النشطة:")
            for route in routes[:10]:
                report.append(f"   • {route}")
            if len(routes) > 10:
                report.append(f"   ... و {len(routes) - 10} مسار آخر")
        
        # المشاكل والتوصيات
        report.append("\n\n⚠️ **المشاكل والتوصيات:**")
        report.append("-"*60)
        report.append("1. 🟡 بعض الوحدات في Backend غير مكتملة")
        report.append("2. 🟡 توجد ملفات __pycache__ يجب حذفها")
        report.append("3. 🟡 بعض الوحدات في Frontend ليس لديها صفحات أو خدمات")
        report.append("4. 💡 يوصى بحذف الوحدات غير المستخدمة")
        
        # الوحدات الموصى بحذفها
        report.append("\n🗑️ **الوحدات الموصى بحذفها (غير مكتملة):**")
        report.append("-"*60)
        incomplete_modules = [m for m, c in backend_modules.items() if c < 20]
        if incomplete_modules:
            for module in incomplete_modules:
                report.append(f"   ❌ {module} (اكتمال: {backend_modules[module]:.0f}%)")
        else:
            report.append("   ✅ جميع الوحدات مكتملة نسبياً")
        
        return "\n".join(report)
    
    def save_report(self, filename="project_report.txt"):
        """حفظ التقرير في ملف"""
        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ تم حفظ التقرير في {filename}")
        return report
    
    def run(self):
        """تشغيل التحليل الكامل"""
        print("🔍 بدء تحليل المشروع...")
        self.analyze_backend()
        self.analyze_frontend()
        print("✅ تم الانتهاء من التحليل")
        return self.save_report()

# تشغيل التحليل
if __name__ == "__main__":
    # تأكد من أنك في المجلد الصحيح
    project_root = ".."  # العودة إلى جذر المشروع
    analyzer = ProjectAnalyzer(project_root)
    report = analyzer.run()
    print("\n" + report)