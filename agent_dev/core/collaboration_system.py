#!/usr/bin/env python3
"""
Collaboration System - Hệ thống cộng tác và chia sẻ kiến thức
Hệ thống cộng tác cho AgentDev Unified

Tính năng:
1. Code Review Automation - Tự động review code (lint + static AI review)
2. Knowledge Sharing - Chia sẻ kiến thức (push docs/tests summary vào docs/collab/)
3. Mentoring System - Hệ thống mentoring (recommendations trong logs)
4. Collaboration Tools - Tích hợp công cụ cộng tác (stub Slack/Discord plugin)
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ReviewStatus(Enum):
    """Trạng thái review"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"

class ReviewType(Enum):
    """Loại review"""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    DOCUMENTATION = "documentation"

class CollaborationLevel(Enum):
    """Mức độ cộng tác"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class CodeReview:
    """Code review"""
    review_id: str
    file_path: str
    reviewer: str
    review_type: ReviewType
    status: ReviewStatus
    comments: list[str]
    suggestions: list[str]
    score: float  # 0-100
    created_at: datetime
    updated_at: datetime

@dataclass
class KnowledgeShare:
    """Chia sẻ kiến thức"""
    share_id: str
    title: str
    content: str
    category: str
    author: str
    tags: list[str]
    created_at: datetime
    views: int
    likes: int

@dataclass
class MentoringSession:
    """Phiên mentoring"""
    session_id: str
    mentor: str
    mentee: str
    topic: str
    duration: int  # minutes
    feedback: str
    recommendations: list[str]
    created_at: datetime

@dataclass
class CollaborationReport:
    """Báo cáo cộng tác"""
    total_reviews: int
    approved_reviews: int
    knowledge_shares: int
    mentoring_sessions: int
    team_activity: dict[str, int]
    recommendations: list[str]
    generated_at: datetime

class CollaborationSystem:
    """Collaboration System - Hệ thống cộng tác toàn diện"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.collab_dir = self.project_root / "docs" / "collab"
        self.reviews_dir = self.collab_dir / "reviews"
        self.knowledge_dir = self.collab_dir / "knowledge"
        self.mentoring_dir = self.collab_dir / "mentoring"

        # Tạo thư mục cần thiết
        self._ensure_directories()

        # Khởi tạo logging
        self._setup_logging()

        # Collaboration data
        self.reviews: list[CodeReview] = []
        self.knowledge_shares: list[KnowledgeShare] = []
        self.mentoring_sessions: list[MentoringSession] = []

        # Load existing data
        self._load_existing_data()

    def _ensure_directories(self):
        """Đảm bảo thư mục cần thiết tồn tại"""
        for dir_path in [self.collab_dir, self.reviews_dir, self.knowledge_dir, self.mentoring_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging system"""
        log_file = self.collab_dir / "collaboration.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger("CollaborationSystem")

    def _load_existing_data(self):
        """Load dữ liệu cộng tác hiện có"""
        # Load reviews
        review_files = list(self.reviews_dir.glob("*.json"))
        for file_path in review_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                review = CodeReview(**data)
                self.reviews.append(review)
            except Exception as e:
                self.logger.error(f"Error loading review {file_path}: {e}")

        # Load knowledge shares
        knowledge_files = list(self.knowledge_dir.glob("*.json"))
        for file_path in knowledge_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                share = KnowledgeShare(**data)
                self.knowledge_shares.append(share)
            except Exception as e:
                self.logger.error(f"Error loading knowledge share {file_path}: {e}")

        # Load mentoring sessions
        mentoring_files = list(self.mentoring_dir.glob("*.json"))
        for file_path in mentoring_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                session = MentoringSession(**data)
                self.mentoring_sessions.append(session)
            except Exception as e:
                self.logger.error(f"Error loading mentoring session {file_path}: {e}")

    def review_code(self, file_path: str, reviewer: str = "AgentDev") -> CodeReview:
        """Review code tự động"""
        review_id = f"review_{int(time.time())}"

        # Chạy linting tools
        lint_results = self._run_linting(file_path)

        # Phân tích code quality
        quality_analysis = self._analyze_code_quality(file_path)

        # Phân tích security
        security_analysis = self._analyze_security(file_path)

        # Phân tích performance
        performance_analysis = self._analyze_performance(file_path)

        # Tổng hợp kết quả
        comments = []
        suggestions = []
        score = 100.0

        # Xử lý linting results
        if lint_results['errors']:
            comments.extend([f"Lỗi linting: {error}" for error in lint_results['errors']])
            score -= len(lint_results['errors']) * 5

        if lint_results['warnings']:
            comments.extend([f"Cảnh báo linting: {warning}" for warning in lint_results['warnings']])
            score -= len(lint_results['warnings']) * 2

        # Xử lý quality analysis
        if quality_analysis['complexity'] > 10:
            comments.append(f"Độ phức tạp cao: {quality_analysis['complexity']}")
            suggestions.append("Xem xét chia nhỏ function để giảm độ phức tạp")
            score -= 10

        if quality_analysis['duplicate_code'] > 0:
            comments.append(f"Phát hiện {quality_analysis['duplicate_code']} đoạn code trùng lặp")
            suggestions.append("Refactor để loại bỏ code trùng lặp")
            score -= 5

        # Xử lý security analysis
        if security_analysis['issues']:
            comments.extend([f"Vấn đề bảo mật: {issue}" for issue in security_analysis['issues']])
            suggestions.append("Sửa các vấn đề bảo mật được phát hiện")
            score -= len(security_analysis['issues']) * 15

        # Xử lý performance analysis
        if performance_analysis['slow_operations']:
            comments.extend([f"Thao tác chậm: {op}" for op in performance_analysis['slow_operations']])
            suggestions.append("Tối ưu hóa các thao tác chậm")
            score -= len(performance_analysis['slow_operations']) * 5

        # Xác định status
        if score >= 90:
            status = ReviewStatus.APPROVED
        elif score >= 70:
            status = ReviewStatus.NEEDS_CHANGES
        else:
            status = ReviewStatus.REJECTED

        # Tạo review
        review = CodeReview(
            review_id=review_id,
            file_path=file_path,
            reviewer=reviewer,
            review_type=ReviewType.CODE_QUALITY,
            status=status,
            comments=comments,
            suggestions=suggestions,
            score=score,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Lưu review
        self._save_review(review)
        self.reviews.append(review)

        self.logger.info(f"Code review completed for {file_path}, score: {score}")
        return review

    def _run_linting(self, file_path: str) -> dict[str, list[str]]:
        """Chạy linting tools"""
        errors = []
        warnings = []

        try:
            # Chạy flake8
            result = subprocess.run(['flake8', file_path], capture_output=True, text=True)
            if result.returncode != 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip():
                        if 'E' in line:  # Error
                            errors.append(line.strip())
                        elif 'W' in line:  # Warning
                            warnings.append(line.strip())
        except FileNotFoundError:
            # flake8 không có sẵn, bỏ qua
            pass

        try:
            # Chạy pylint
            result = subprocess.run(['pylint', file_path], capture_output=True, text=True)
            if result.returncode != 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.strip() and ':' in line:
                        if 'error' in line.lower():
                            errors.append(line.strip())
                        elif 'warning' in line.lower():
                            warnings.append(line.strip())
        except FileNotFoundError:
            # pylint không có sẵn, bỏ qua
            pass

        return {'errors': errors, 'warnings': warnings}

    def _analyze_code_quality(self, file_path: str) -> dict[str, Any]:
        """Phân tích chất lượng code"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            # Tính độ phức tạp (đơn giản)
            complexity = 0
            for line in lines:
                if any(keyword in line for keyword in ['if', 'for', 'while', 'try', 'except']):
                    complexity += 1

            # Tìm code trùng lặp (đơn giản)
            duplicate_code = 0
            line_counts = {}
            for line in lines:
                if line.strip() and not line.strip().startswith('#'):
                    line_counts[line] = line_counts.get(line, 0) + 1

            duplicate_code = sum(1 for count in line_counts.values() if count > 3)

            return {
                'complexity': complexity,
                'duplicate_code': duplicate_code,
                'total_lines': len(lines)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing code quality for {file_path}: {e}")
            return {'complexity': 0, 'duplicate_code': 0, 'total_lines': 0}

    def _analyze_security(self, file_path: str) -> dict[str, list[str]]:
        """Phân tích bảo mật"""
        issues = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Kiểm tra các pattern bảo mật
            security_patterns = {
                'password': 'Phát hiện từ khóa "password" - có thể chứa thông tin nhạy cảm',
                'secret': 'Phát hiện từ khóa "secret" - có thể chứa thông tin nhạy cảm',
                'key': 'Phát hiện từ khóa "key" - có thể chứa API key',
                'token': 'Phát hiện từ khóa "token" - có thể chứa token nhạy cảm',
                'eval(': 'Sử dụng eval() có thể gây lỗ hổng bảo mật',
                'exec(': 'Sử dụng exec() có thể gây lỗ hổng bảo mật',
                'subprocess': 'Sử dụng subprocess cần kiểm tra input validation'
            }

            for pattern, message in security_patterns.items():
                if pattern in content.lower():
                    issues.append(message)

        except Exception as e:
            self.logger.error(f"Error analyzing security for {file_path}: {e}")

        return {'issues': issues}

    def _analyze_performance(self, file_path: str) -> dict[str, list[str]]:
        """Phân tích hiệu suất"""
        slow_operations = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Kiểm tra các pattern hiệu suất
            performance_patterns = {
                'for i in range(len(': 'Sử dụng range(len()) có thể chậm',
                'list.append(': 'Sử dụng list.append() trong vòng lặp có thể chậm',
                'string +=': 'Sử dụng string concatenation có thể chậm',
                'time.sleep(': 'Sử dụng time.sleep() có thể ảnh hưởng hiệu suất',
                'requests.get(': 'HTTP requests có thể chậm, cần timeout',
                'open(': 'File operations cần được tối ưu'
            }

            for pattern, message in performance_patterns.items():
                if pattern in content:
                    slow_operations.append(message)

        except Exception as e:
            self.logger.error(f"Error analyzing performance for {file_path}: {e}")

        return {'slow_operations': slow_operations}

    def _save_review(self, review: CodeReview):
        """Lưu review vào file"""
        review_file = self.reviews_dir / f"{review.review_id}.json"

        with open(review_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(review), f, indent=2, default=str)

    def share_knowledge(self, title: str, content: str, author: str,
                       category: str = "general", tags: list[str] = None) -> KnowledgeShare:
        """Chia sẻ kiến thức"""
        if tags is None:
            tags = []

        share_id = f"share_{int(time.time())}"

        share = KnowledgeShare(
            share_id=share_id,
            title=title,
            content=content,
            category=category,
            author=author,
            tags=tags,
            created_at=datetime.now(),
            views=0,
            likes=0
        )

        # Lưu knowledge share
        self._save_knowledge_share(share)
        self.knowledge_shares.append(share)

        self.logger.info(f"Knowledge shared: {title} by {author}")
        return share

    def _save_knowledge_share(self, share: KnowledgeShare):
        """Lưu knowledge share vào file"""
        share_file = self.knowledge_dir / f"{share.share_id}.json"

        with open(share_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(share), f, indent=2, default=str)

    def create_mentoring_session(self, mentor: str, mentee: str, topic: str,
                                duration: int, feedback: str = "") -> MentoringSession:
        """Tạo phiên mentoring"""
        session_id = f"session_{int(time.time())}"

        # Tạo recommendations dựa trên topic
        recommendations = self._generate_mentoring_recommendations(topic)

        session = MentoringSession(
            session_id=session_id,
            mentor=mentor,
            mentee=mentee,
            topic=topic,
            duration=duration,
            feedback=feedback,
            recommendations=recommendations,
            created_at=datetime.now()
        )

        # Lưu mentoring session
        self._save_mentoring_session(session)
        self.mentoring_sessions.append(session)

        self.logger.info(f"Mentoring session created: {topic} between {mentor} and {mentee}")
        return session

    def _generate_mentoring_recommendations(self, topic: str) -> list[str]:
        """Tạo recommendations cho mentoring"""
        recommendations = []

        topic_lower = topic.lower()

        if 'python' in topic_lower:
            recommendations.extend([
                "Học Python basics: variables, functions, classes",
                "Thực hành với Python exercises",
                "Đọc Python documentation",
                "Tham gia Python community"
            ])

        if 'testing' in topic_lower:
            recommendations.extend([
                "Học về unit testing với pytest",
                "Thực hành viết test cases",
                "Tìm hiểu về test coverage",
                "Học về mocking và fixtures"
            ])

        if 'security' in topic_lower:
            recommendations.extend([
                "Học về OWASP Top 10",
                "Thực hành với security tools",
                "Tìm hiểu về encryption",
                "Học về authentication và authorization"
            ])

        if 'performance' in topic_lower:
            recommendations.extend([
                "Học về profiling tools",
                "Tìm hiểu về algorithms complexity",
                "Thực hành optimization techniques",
                "Học về caching strategies"
            ])

        if not recommendations:
            recommendations = [
                "Tìm hiểu thêm về chủ đề này",
                "Thực hành thường xuyên",
                "Tham gia community discussions",
                "Đọc documentation và tutorials"
            ]

        return recommendations

    def _save_mentoring_session(self, session: MentoringSession):
        """Lưu mentoring session vào file"""
        session_file = self.mentoring_dir / f"{session.session_id}.json"

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(session), f, indent=2, default=str)

    def generate_collaboration_report(self) -> CollaborationReport:
        """Tạo báo cáo cộng tác"""
        total_reviews = len(self.reviews)
        approved_reviews = len([r for r in self.reviews if r.status == ReviewStatus.APPROVED])
        knowledge_shares = len(self.knowledge_shares)
        mentoring_sessions = len(self.mentoring_sessions)

        # Tính team activity
        team_activity = {}
        for review in self.reviews:
            team_activity[review.reviewer] = team_activity.get(review.reviewer, 0) + 1

        for share in self.knowledge_shares:
            team_activity[share.author] = team_activity.get(share.author, 0) + 1

        for session in self.mentoring_sessions:
            team_activity[session.mentor] = team_activity.get(session.mentor, 0) + 1
            team_activity[session.mentee] = team_activity.get(session.mentee, 0) + 1

        # Tạo recommendations
        recommendations = []

        if total_reviews > 0:
            approval_rate = approved_reviews / total_reviews
            if approval_rate < 0.8:
                recommendations.append("Cải thiện chất lượng code để tăng tỷ lệ approval")
            else:
                recommendations.append("Duy trì chất lượng code hiện tại")

        if knowledge_shares < 5:
            recommendations.append("Khuyến khích team chia sẻ kiến thức nhiều hơn")

        if mentoring_sessions < 3:
            recommendations.append("Tăng cường hoạt động mentoring trong team")

        if len(team_activity) < 3:
            recommendations.append("Khuyến khích tất cả thành viên tham gia cộng tác")

        return CollaborationReport(
            total_reviews=total_reviews,
            approved_reviews=approved_reviews,
            knowledge_shares=knowledge_shares,
            mentoring_sessions=mentoring_sessions,
            team_activity=team_activity,
            recommendations=recommendations,
            generated_at=datetime.now()
        )

    def create_collaboration_summary(self) -> str:
        """Tạo tóm tắt cộng tác"""
        report = self.generate_collaboration_report()

        summary = f"""# Báo cáo Cộng tác Team

**Ngày tạo**: {report.generated_at.strftime('%d/%m/%Y %H:%M:%S')}

## 📊 Thống kê tổng quan

- **Tổng số reviews**: {report.total_reviews}
- **Reviews được approve**: {report.approved_reviews}
- **Chia sẻ kiến thức**: {report.knowledge_shares}
- **Phiên mentoring**: {report.mentoring_sessions}

## 👥 Hoạt động team

"""

        for member, activity in report.team_activity.items():
            summary += f"- **{member}**: {activity} hoạt động\n"

        summary += "\n## 💡 Khuyến nghị\n\n"

        for recommendation in report.recommendations:
            summary += f"- {recommendation}\n"

        summary += "\n## 📈 Xu hướng\n\n"

        if report.total_reviews > 0:
            approval_rate = report.approved_reviews / report.total_reviews
            summary += f"- Tỷ lệ approval: {approval_rate:.1%}\n"

        if report.knowledge_shares > 0:
            summary += f"- Trung bình {report.knowledge_shares} bài chia sẻ kiến thức\n"

        if report.mentoring_sessions > 0:
            summary += f"- Trung bình {report.mentoring_sessions} phiên mentoring\n"

        return summary

    def save_collaboration_report(self, report: CollaborationReport) -> str:
        """Lưu báo cáo cộng tác"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Lưu JSON report
        json_file = self.project_root / "artifacts" / f"collaboration_report_{timestamp}.json"
        json_file.parent.mkdir(exist_ok=True)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, default=str)

        # Lưu summary
        summary = self.create_collaboration_summary()
        summary_file = self.collab_dir / f"collaboration_summary_{timestamp}.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        return str(json_file)

def main():
    """Main function for testing"""
    collab_system = CollaborationSystem(".")

    # Test code review
    test_file = "agent_dev/core/agentdev.py"
    if os.path.exists(test_file):
        review = collab_system.review_code(test_file)
        print(f"Code review completed: {review.score}/100")

    # Test knowledge sharing
    share = collab_system.share_knowledge(
        "Python Best Practices",
        "Một số best practices cho Python development...",
        "AgentDev",
        "programming",
        ["python", "best-practices"]
    )
    print(f"Knowledge shared: {share.title}")

    # Test mentoring
    session = collab_system.create_mentoring_session(
        "Senior Dev",
        "Junior Dev",
        "Python Testing",
        60,
        "Good progress on testing concepts"
    )
    print(f"Mentoring session created: {session.topic}")

    # Generate report
    report = collab_system.generate_collaboration_report()
    json_file = collab_system.save_collaboration_report(report)
    print(f"Collaboration report saved: {json_file}")

if __name__ == "__main__":
    main()
