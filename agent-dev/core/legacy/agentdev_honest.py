#!/usr/bin/env python3
"""
AgentDev Honest - Phiên bản AgentDev có trách nhiệm và trung thực
Tích hợp hệ thống validation tự động để đảm bảo chất lượng

Tính năng:
1. Bằng chứng trước/sau khi sửa code
2. Phân loại lỗi rõ ràng theo mức độ nghiêm trọng
3. Kiểm tra tự động sau mỗi lần sửa
4. Ưu tiên chất lượng hơn số lượng
5. Báo cáo trung thực với bằng chứng cụ thể
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Any
from agentdev_validation_system import AgentDevValidator, ValidationResult, ErrorSeverity

class HonestAgentDev:
    """AgentDev có trách nhiệm và trung thực"""
    
    def __init__(self, project_root: str = "."):
        self.validator = AgentDevValidator(project_root)
        self.session_id = int(time.time())
        self.fixes_applied = []
        self.validation_history = []
        
    def start_fix_session(self, description: str) -> Dict:
        """Bắt đầu phiên sửa lỗi với validation"""
        print("=" * 80)
        print(f"🚀 BẮT ĐẦU PHIÊN SỬA LỖI: {description}")
        print(f"🆔 Session ID: {self.session_id}")
        print("=" * 80)
        
        # Validation trước khi sửa
        before_data = self.validator.validate_before_fix()
        
        session_data = {
            'session_id': self.session_id,
            'description': description,
            'start_time': time.time(),
            'before_data': before_data,
            'fixes': []
        }
        
        print(f"📊 TRẠNG THÁI TRƯỚC KHI SỬA:")
        print(f"   🔢 Tổng lỗi: {before_data['total_errors']}")
        print(f"   🧪 Test passed: {'✅' if before_data['test_passed'] else '❌'}")
        print(f"   📁 Bằng chứng: {before_data['evidence_file']}")
        
        return session_data
    
    def apply_fix(self, fix_description: str, fix_function, *args, **kwargs) -> Dict:
        """Áp dụng một sửa chữa với validation"""
        print(f"\n🔧 ÁP DỤNG SỬA CHỮA: {fix_description}")
        
        fix_start_time = time.time()
        
        try:
            # Thực hiện sửa chữa
            result = fix_function(*args, **kwargs)
            
            fix_data = {
                'description': fix_description,
                'start_time': fix_start_time,
                'end_time': time.time(),
                'duration': time.time() - fix_start_time,
                'success': True,
                'result': result
            }
            
            print(f"   ✅ Thành công trong {fix_data['duration']:.2f}s")
            
        except Exception as e:
            fix_data = {
                'description': fix_description,
                'start_time': fix_start_time,
                'end_time': time.time(),
                'duration': time.time() - fix_start_time,
                'success': False,
                'error': str(e)
            }
            
            print(f"   ❌ Thất bại: {e}")
        
        self.fixes_applied.append(fix_data)
        return fix_data
    
    def end_fix_session(self, session_data: Dict) -> ValidationResult:
        """Kết thúc phiên sửa lỗi với validation"""
        print(f"\n🏁 KẾT THÚC PHIÊN SỬA LỖI")
        
        # Validation sau khi sửa
        result = self.validator.validate_after_fix(session_data['before_data'])
        
        # Cập nhật session data
        session_data['end_time'] = time.time()
        session_data['duration'] = session_data['end_time'] - session_data['start_time']
        session_data['fixes'] = self.fixes_applied
        session_data['validation_result'] = result.__dict__
        
        # Lưu session data
        session_file = f"session_{self.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        # Tạo báo cáo
        report = self.validator.generate_report(result)
        
        # Lưu báo cáo
        report_file = f"session_report_{self.session_id}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📁 Session data: {session_file}")
        print(f"📄 Báo cáo: {report_file}")
        
        # Hiển thị kết quả
        self._display_session_summary(session_data, result)
        
        return result
    
    def _display_session_summary(self, session_data: Dict, result: ValidationResult):
        """Hiển thị tóm tắt phiên sửa lỗi"""
        print("\n" + "=" * 80)
        print("📊 TÓM TẮT PHIÊN SỬA LỖI")
        print("=" * 80)
        
        print(f"🆔 Session ID: {self.session_id}")
        print(f"📝 Mô tả: {session_data['description']}")
        print(f"⏱️  Thời gian: {session_data['duration']:.2f}s")
        print(f"🔧 Số sửa chữa: {len(self.fixes_applied)}")
        
        print(f"\n📈 KẾT QUẢ VALIDATION:")
        print(f"   🔢 Lỗi trước: {result.before_errors}")
        print(f"   🔢 Lỗi sau: {result.after_errors}")
        print(f"   ✅ Đã sửa: {result.errors_fixed}")
        print(f"   🚨 Lỗi nghiêm trọng: {result.critical_errors}")
        print(f"   ⚠️  Cảnh báo: {result.warnings}")
        print(f"   💡 Gợi ý style: {result.style_suggestions}")
        
        quality_score = self.validator.get_quality_score(result)
        print(f"   🎯 Điểm chất lượng: {quality_score:.1f}/100")
        
        print(f"\n🎯 TRẠNG THÁI: {'✅ THÀNH CÔNG' if result.success else '❌ THẤT BẠI'}")
        
        if result.success:
            print("🌟 AgentDev đã hoàn thành nhiệm vụ một cách trung thực và có trách nhiệm!")
        else:
            print("⚠️  Cần kiểm tra lại quá trình sửa lỗi.")
        
        print("=" * 80)
    
    def get_priority_fixes(self, error_details: List[Dict]) -> List[Dict]:
        """Lấy danh sách lỗi cần ưu tiên sửa theo quy tắc chất lượng"""
        # Sắp xếp theo mức độ ưu tiên
        priority_order = {
            ErrorSeverity.CRITICAL_ERROR.value: 1,
            ErrorSeverity.WARNING.value: 2,
            ErrorSeverity.STYLE_SUGGESTION.value: 3
        }
        
        sorted_errors = sorted(
            error_details,
            key=lambda x: priority_order.get(x['severity'], 4)
        )
        
        return sorted_errors
    
    def should_continue_fixing(self, result: ValidationResult) -> bool:
        """Quyết định có nên tiếp tục sửa lỗi hay không"""
        # Dừng nếu đã sửa được lỗi nghiêm trọng
        if result.critical_errors == 0 and result.before_errors > 0:
            return False
        
        # Dừng nếu điểm chất lượng đã đạt mức tốt
        quality_score = self.validator.get_quality_score(result)
        if quality_score >= 80:
            return False
        
        # Dừng nếu đã sửa quá nhiều lỗi vặt mà chưa sửa lỗi nghiêm trọng
        if result.critical_errors > 0 and result.style_suggestions > 50:
            return False
        
        return True
    
    def generate_honest_report(self, result: ValidationResult) -> str:
        """Tạo báo cáo trung thực với bằng chứng"""
        quality_score = self.validator.get_quality_score(result)
        
        report = f"""
# 🎯 BÁO CÁO TRUNG THỰC AGENTDEV

## 📋 Thông tin phiên làm việc
- **Session ID**: {self.session_id}
- **Thời gian**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Điểm chất lượng**: {quality_score:.1f}/100

## 🔍 Bằng chứng trước/sau
- **Trước khi sửa**: {result.evidence_files[0]}
- **Sau khi sửa**: {result.evidence_files[1]}

## 📊 Thống kê lỗi
| Loại | Trước | Sau | Đã sửa |
|------|-------|-----|--------|
| Tổng lỗi | {result.before_errors} | {result.after_errors} | {result.errors_fixed} |
| Lỗi nghiêm trọng | - | {result.critical_errors} | - |
| Cảnh báo | - | {result.warnings} | - |
| Gợi ý style | - | {result.style_suggestions} | - |

## 🎯 Đánh giá trung thực
"""
        
        if result.success:
            report += "✅ **THÀNH CÔNG**: Đã sửa được lỗi và code vẫn hoạt động.\n"
        else:
            report += "❌ **THẤT BẠI**: Cần kiểm tra lại quá trình sửa lỗi.\n"
        
        if quality_score >= 80:
            report += "🌟 **CHẤT LƯỢNG CAO**: Điểm số xuất sắc!\n"
        elif quality_score >= 60:
            report += "👍 **CHẤT LƯỢNG TỐT**: Điểm số khá tốt.\n"
        else:
            report += "⚠️ **CẦN CẢI THIỆN**: Điểm số thấp, cần tập trung vào lỗi nghiêm trọng.\n"
        
        # Thêm khuyến nghị
        report += "\n## 💡 Khuyến nghị\n"
        
        if result.critical_errors > 0:
            report += f"- 🚨 **Ưu tiên cao**: Còn {result.critical_errors} lỗi nghiêm trọng cần sửa ngay\n"
        
        if result.warnings > 10:
            report += f"- ⚠️ **Ưu tiên trung bình**: Còn {result.warnings} cảnh báo cần xem xét\n"
        
        if result.style_suggestions > 50:
            report += f"- 💡 **Ưu tiên thấp**: Còn {result.style_suggestions} gợi ý style (có thể bỏ qua)\n"
        
        report += "\n## 🔒 Cam kết trung thực\n"
        report += "- Tất cả số liệu đều có bằng chứng cụ thể\n"
        report += "- Không báo cáo sai số liệu\n"
        report += "- Ưu tiên chất lượng hơn số lượng\n"
        report += "- Tuân thủ quy tắc: 1 lỗi quan trọng > 100 lỗi vặt\n"
        
        return report

def main():
    """Hàm main để test AgentDev Honest"""
    print("🧪 Test AgentDev Honest...")
    
    # Tạo AgentDev Honest
    agent = HonestAgentDev()
    
    # Bắt đầu phiên sửa lỗi
    session = agent.start_fix_session("Test validation system")
    
    # Giả lập một số sửa chữa
    def dummy_fix_1():
        print("   🔧 Sửa lỗi import...")
        time.sleep(1)
        return "Fixed import errors"
    
    def dummy_fix_2():
        print("   🔧 Sửa lỗi type annotation...")
        time.sleep(1)
        return "Fixed type annotations"
    
    # Áp dụng sửa chữa
    agent.apply_fix("Sửa lỗi import", dummy_fix_1)
    agent.apply_fix("Sửa lỗi type annotation", dummy_fix_2)
    
    # Kết thúc phiên sửa lỗi
    result = agent.end_fix_session(session)
    
    # Tạo báo cáo trung thực
    honest_report = agent.generate_honest_report(result)
    print(honest_report)
    
    # Lưu báo cáo
    with open(f"honest_report_{agent.session_id}.md", 'w', encoding='utf-8') as f:
        f.write(honest_report)

if __name__ == "__main__":
    main()
