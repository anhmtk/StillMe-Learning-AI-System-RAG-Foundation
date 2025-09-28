"""
StillMe Learning Approval CLI
Command-line interface để quản lý phê duyệt học tập
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from stillme_core.learning.approval_system import (
    ApprovalSystem, ApprovalConfig, ApprovalStatus, 
    ContentType, ApprovalPriority, get_approval_system
)
from stillme_core.learning.approval_queue import ApprovalQueueManager, get_approval_queue_manager

class ApprovalCLI:
    """CLI cho quản lý phê duyệt"""
    
    def __init__(self):
        self.approval_system = None
        self.queue_manager = None
    
    async def initialize(self, config_path: str = None):
        """Khởi tạo hệ thống"""
        config = ApprovalConfig()
        
        # Load config from file if provided
        if config_path and Path(config_path).exists():
            import toml
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = toml.load(f)
                # Update config with loaded data
                for key, value in config_data.get('approval', {}).items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        
        self.approval_system = get_approval_system(config)
        self.queue_manager = get_approval_queue_manager(self.approval_system)
    
    async def list_pending(self, limit: int = 20, priority: str = None):
        """Liệt kê yêu cầu chờ phê duyệt"""
        requests = await self.approval_system.get_pending_requests(limit)
        
        if priority:
            priority_enum = ApprovalPriority(priority.lower())
            requests = [req for req in requests if req.priority == priority_enum]
        
        if not requests:
            print("📭 Không có yêu cầu chờ phê duyệt")
            return
        
        print(f"📋 Danh sách yêu cầu chờ phê duyệt ({len(requests)} items):")
        print("=" * 80)
        
        for i, req in enumerate(requests, 1):
            status_icon = "⏳" if req.status == ApprovalStatus.PENDING else "✅"
            priority_icon = {
                ApprovalPriority.LOW: "🟢",
                ApprovalPriority.MEDIUM: "🟡", 
                ApprovalPriority.HIGH: "🟠",
                ApprovalPriority.CRITICAL: "🔴"
            }.get(req.priority, "⚪")
            
            print(f"{i:2d}. {status_icon} {priority_icon} {req.title[:50]}...")
            print(f"    📝 Type: {req.content_type.value}")
            print(f"    📊 Quality: {req.quality_score:.2f} | Risk: {req.risk_score:.2f}")
            print(f"    ⏰ Created: {req.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"    ⏳ Expires: {req.expires_at.strftime('%Y-%m-%d %H:%M')}")
            if req.source_url:
                print(f"    🔗 Source: {req.source_url}")
            print()
    
    async def show_request(self, request_id: str):
        """Hiển thị chi tiết yêu cầu"""
        request = await self.approval_system.get_request(request_id)
        
        if not request:
            print(f"❌ Không tìm thấy yêu cầu: {request_id}")
            return
        
        print(f"📄 Chi tiết yêu cầu: {request_id}")
        print("=" * 60)
        print(f"📝 Tiêu đề: {request.title}")
        print(f"📋 Mô tả: {request.description}")
        print(f"🏷️  Loại: {request.content_type.value}")
        print(f"📊 Chất lượng: {request.quality_score:.2f}")
        print(f"⚠️  Rủi ro: {request.risk_score:.2f}")
        print(f"🎯 Ưu tiên: {request.priority.value}")
        print(f"📊 Trạng thái: {request.status.value}")
        print(f"⏰ Tạo lúc: {request.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏳ Hết hạn: {request.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if request.source_url:
            print(f"🔗 Nguồn: {request.source_url}")
        
        print(f"\n📄 Nội dung preview:")
        print("-" * 40)
        print(request.content_preview)
        print("-" * 40)
        
        if request.approver_notes:
            print(f"\n💬 Ghi chú phê duyệt: {request.approver_notes}")
        
        if request.approved_by:
            print(f"✅ Phê duyệt bởi: {request.approved_by}")
            print(f"⏰ Lúc: {request.approved_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def approve(self, request_id: str, approver: str, notes: str = None):
        """Phê duyệt yêu cầu"""
        success = await self.approval_system.approve_request(request_id, approver, notes)
        
        if success:
            print(f"✅ Đã phê duyệt yêu cầu: {request_id}")
            print(f"👤 Người phê duyệt: {approver}")
            if notes:
                print(f"💬 Ghi chú: {notes}")
        else:
            print(f"❌ Không thể phê duyệt yêu cầu: {request_id}")
    
    async def reject(self, request_id: str, approver: str, notes: str = None):
        """Từ chối yêu cầu"""
        success = await self.approval_system.reject_request(request_id, approver, notes)
        
        if success:
            print(f"❌ Đã từ chối yêu cầu: {request_id}")
            print(f"👤 Người từ chối: {approver}")
            if notes:
                print(f"💬 Lý do: {notes}")
        else:
            print(f"❌ Không thể từ chối yêu cầu: {request_id}")
    
    async def batch_approve(self, file_path: str):
        """Phê duyệt hàng loạt từ file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                approvals = json.load(f)
            
            results = await self.queue_manager.process_approval_batch(approvals)
            
            print(f"📊 Kết quả phê duyệt hàng loạt:")
            print(f"✅ Đã phê duyệt: {results['approved']}")
            print(f"❌ Đã từ chối: {results['rejected']}")
            print(f"⚠️  Lỗi: {results['failed']}")
            
        except Exception as e:
            print(f"❌ Lỗi khi xử lý file: {e}")
    
    async def stats(self):
        """Hiển thị thống kê"""
        stats = await self.queue_manager.get_approval_summary()
        
        print("📊 Thống kê hệ thống phê duyệt")
        print("=" * 50)
        
        # Queue stats
        queue_stats = stats["queue_stats"]
        print(f"📋 Hàng đợi:")
        print(f"  ⏳ Chờ phê duyệt: {queue_stats['total_pending']}")
        print(f"  🔴 Ưu tiên cao: {queue_stats['high_priority']}")
        print(f"  ⏰ Sắp hết hạn: {queue_stats['expired_soon']}")
        print(f"  📉 Tỷ lệ từ chối: {queue_stats['rejection_rate']:.1%}")
        
        # Approval stats
        approval_stats = stats["approval_stats"]
        print(f"\n📈 Thống kê phê duyệt:")
        for status, count in approval_stats["status_counts"].items():
            print(f"  {status}: {count}")
        
        print(f"  📊 Tổng yêu cầu: {approval_stats['total_requests']}")
        print(f"  ✅ Tỷ lệ phê duyệt: {approval_stats['approval_rate']:.1%}")
        
        # System status
        system_status = stats["system_status"]
        print(f"\n⚙️  Cấu hình hệ thống:")
        print(f"  🔧 Enabled: {system_status['enabled']}")
        print(f"  🎯 Auto-approve threshold: {system_status['auto_approve_threshold']}")
        print(f"  📊 Max pending: {system_status['max_pending']}")
    
    async def cleanup(self):
        """Dọn dẹp yêu cầu hết hạn"""
        expired_count = await self.queue_manager.cleanup_expired_requests()
        print(f"🧹 Đã dọn dẹp {expired_count} yêu cầu hết hạn")
    
    async def test_submit(self, content_type: str, title: str, description: str):
        """Test gửi yêu cầu phê duyệt"""
        try:
            content_type_enum = ContentType(content_type.lower())
            
            request_id = await self.queue_manager.submit_learning_content(
                content_type=content_type_enum,
                title=title,
                description=description,
                content_preview=description[:500],
                quality_score=0.8,
                risk_score=0.2,
                priority=ApprovalPriority.MEDIUM
            )
            
            if request_id:
                print(f"✅ Đã gửi yêu cầu phê duyệt: {request_id}")
                print(f"📝 Tiêu đề: {title}")
                print(f"🏷️  Loại: {content_type}")
            else:
                print("❌ Không thể gửi yêu cầu phê duyệt")
                
        except ValueError as e:
            print(f"❌ Lỗi loại nội dung: {e}")
            print(f"📋 Loại hợp lệ: {[ct.value for ct in ContentType]}")

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="StillMe Learning Approval Manager")
    parser.add_argument("--config", help="Path to config file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List pending requests
    list_parser = subparsers.add_parser("list", help="List pending requests")
    list_parser.add_argument("--limit", type=int, default=20, help="Limit number of requests")
    list_parser.add_argument("--priority", choices=["low", "medium", "high", "critical"], 
                           help="Filter by priority")
    
    # Show request details
    show_parser = subparsers.add_parser("show", help="Show request details")
    show_parser.add_argument("request_id", help="Request ID")
    
    # Approve request
    approve_parser = subparsers.add_parser("approve", help="Approve request")
    approve_parser.add_argument("request_id", help="Request ID")
    approve_parser.add_argument("--approver", default="human", help="Approver name")
    approve_parser.add_argument("--notes", help="Approval notes")
    
    # Reject request
    reject_parser = subparsers.add_parser("reject", help="Reject request")
    reject_parser.add_argument("request_id", help="Request ID")
    reject_parser.add_argument("--approver", default="human", help="Approver name")
    reject_parser.add_argument("--notes", help="Rejection reason")
    
    # Batch approve
    batch_parser = subparsers.add_parser("batch", help="Batch approve from JSON file")
    batch_parser.add_argument("file_path", help="Path to JSON file with approvals")
    
    # Stats
    subparsers.add_parser("stats", help="Show approval statistics")
    
    # Cleanup
    subparsers.add_parser("cleanup", help="Cleanup expired requests")
    
    # Test submit
    test_parser = subparsers.add_parser("test", help="Test submit approval request")
    test_parser.add_argument("content_type", help="Content type")
    test_parser.add_argument("title", help="Title")
    test_parser.add_argument("description", help="Description")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = ApprovalCLI()
    await cli.initialize(args.config)
    
    # Execute command
    try:
        if args.command == "list":
            await cli.list_pending(args.limit, args.priority)
        elif args.command == "show":
            await cli.show_request(args.request_id)
        elif args.command == "approve":
            await cli.approve(args.request_id, args.approver, args.notes)
        elif args.command == "reject":
            await cli.reject(args.request_id, args.approver, args.notes)
        elif args.command == "batch":
            await cli.batch_approve(args.file_path)
        elif args.command == "stats":
            await cli.stats()
        elif args.command == "cleanup":
            await cli.cleanup()
        elif args.command == "test":
            await cli.test_submit(args.content_type, args.title, args.description)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
