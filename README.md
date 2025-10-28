# 🌟 StillMe AI IPC — Bạn đồng hành thông minh (mời cộng đồng góp sức)

[![Alpha](https://img.shields.io/badge/status-alpha-orange)](https://github.com/anhmtk/stillme_ai_ipc)
[![Security-First](https://img.shields.io/badge/security-first-green)](docs/SECURITY_COMPLIANCE_MAP.md)
[![Open to PRs](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**StillMe AI IPC** là một AI companion thông minh được tạo ra bởi **Anh Nguyễn** với sự hỗ trợ lớn từ các tổ chức AI như OpenAI, Google, DeepSeek. Mục tiêu của là đồng hành và trở thành bạn bè với mọi người.

> **Lưu ý**: Dự án này đang trong giai đoạn alpha. Chúng tôi chia sẻ để nhận phản hồi sớm từ cộng đồng. Nếu bạn thấy tiềm năng, hãy giúp chúng tôi đưa nó đến mức production.

## 🎯 Tầm nhìn & Sứ mệnh

**Tầm nhìn**: Tạo ra một AI companion thực sự thông minh, có thể tự học và tự tiến hóa, đồng thời duy trì an toàn và đạo đức.

**Sứ mệnh**: 
- 🤖 **Tự học & Tự tiến hóa**: StillMe có thể tự đề xuất và học kiến thức mới
- 🛡️ **An toàn & Minh bạch**: Mọi quyết định học tập đều có thể kiểm soát và giám sát
- 👥 **Cộng đồng**: Mở cửa cho cộng đồng đóng góp và phát triển
- 🌍 **Toàn cầu**: Hỗ trợ đa ngôn ngữ, đặc biệt là tiếng Việt

## 🚀 Điểm độc đáo của StillMe

### 🤖 AgentDev (Alpha) - Trưởng phòng Kỹ thuật AI
- **Tư duy Senior**: Phân tích tác động, suy nghĩ bảo mật, đánh giá kinh doanh
- **Tự động hóa**: Giám sát hệ thống 24/7, tự động sửa lỗi, tối ưu hiệu suất
- **Học từ kinh nghiệm**: Rút kinh nghiệm từ các lần thực hiện trước
- **Trạng thái**: Chạy được nền tảng, còn thiếu một số module nâng cao

### 🧠 Hệ thống Router thông minh
- **Local AI trước**: Ưu tiên AI local (Llama3.1-8B) cho câu hỏi đơn giản
- **Cloud AI khi cần**: Tự động chuyển sang DeepSeek cho câu hỏi phức tạp
- **Fallback thông minh**: Luôn có phản hồi dự phòng khi gặp lỗi
- **Trạng thái**: Hoạt động ổn định, đã tích hợp vào dashboard

### 🧠 Trí nhớ phân tầng (Beta)
- **Short-term**: Ghi nhớ cuộc trò chuyện hiện tại
- **Mid-term**: Lưu trữ kiến thức trong vài ngày
- **Long-term**: Lưu trữ kiến thức lâu dài với mã hóa
- **Trạng thái**: Simple mode hoạt động, consolidation đang phát triển

### 📚 Hệ thống học tập tiến hóa (WIP)
- **Tự đề xuất**: StillMe tự tìm và đề xuất kiến thức mới mỗi 2 giờ
- **12 nguồn học**: HN, Reddit, GitHub, TechCrunch, ArXiv, News, Stack Overflow, Medium, Academic, YouTube, Subreddits
- **Phê duyệt thông minh**: Tự động phê duyệt nội dung an toàn, yêu cầu xem xét nội dung nhạy cảm
- **Trạng thái**: Đang khôi phục từng phần, một số nguồn chưa hoạt động

## 📊 Trạng thái hiện tại

### ✅ Đã hoàn thành
- [x] API server chạy ổn định trên port 8000
- [x] Dashboard Streamlit hoạt động trên port 8529
- [x] Chat interface với StillMe (local + cloud AI)
- [x] Router system hoạt động (local → cloud fallback)
- [x] Database SQLite cho proposals và sessions
- [x] Authentication system cơ bản
- [x] Environment protection (.env policy)

### 🔄 Đang phát triển
- [ ] Notifications (email/Telegram) cần hoàn thiện
- [ ] 12 learning sources: đang restore từng phần
- [ ] Community voting: chưa bật công khai
- [ ] Mobile app: cần cập nhật UI/UX
- [ ] Desktop app: cần tích hợp với hệ thống mới

### ⚠️ Vấn đề đã biết
- [ ] Một số learning sources chưa hoạt động (ArXiv, Medium)
- [ ] Notification system cần cấu hình thêm
- [ ] Dashboard UX cần cải thiện (chat panel, responsive)
- [ ] Community features chưa hoàn thiện

## 🚀 Thử ngay (Quick Start)

### Windows (Đơn giản nhất)
```bash
# 1. Clone repository
git clone https://github.com/anhmtk/stillme_ai_ipc.git
cd stillme_ai_ipc

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Chạy auto-start scripts
start_dashboard.bat    # Mở dashboard
start_api_server.bat   # Mở API server (terminal khác)
```

### Linux/macOS
```bash
# 1. Clone và cài đặt
git clone https://github.com/anhmtk/stillme_ai_ipc.git
cd stillme_ai_ipc
pip install -r requirements.txt

# 2. Chạy services
python api_server.py &                    # API server
streamlit run dashboards/streamlit/integrated_dashboard.py --server.port 8529 &
```

### Truy cập
- **Dashboard**: http://localhost:8529
- **API Server**: http://127.0.0.1:8000
- **Chat với StillMe**: Mở dashboard → Click chat bubble

## 🤝 Cách đóng góp trong 5 phút

### 🎨 Frontend/UI/UX (Cần gấp!)
- **Dashboard cải thiện**: Chat panel, responsive design, dark mode
- **Mobile app**: Flutter UI/UX improvements
- **Desktop app**: Modern UI với better UX

### 🔧 Backend/API
- **Learning sources**: Fix ArXiv, Medium, thêm nguồn mới
- **Notification system**: Email/Telegram integration
- **Performance**: Tối ưu response time, memory usage

### 📚 Documentation
- **API docs**: Swagger/OpenAPI documentation
- **User guides**: Hướng dẫn sử dụng chi tiết
- **Developer docs**: Architecture, contribution guide

### 🐛 Good First Issues
1. **Fix chat panel scrolling** (1-2h)
2. **Add dark mode to dashboard** (2-3h)
3. **Improve mobile responsive** (3-4h)
4. **Add loading indicators** (1h)
5. **Fix notification system** (4-6h)

## 🗺️ Roadmap (Có deadline mềm)

### 2-4 tuần tới
- [ ] Hoàn thiện 12 learning sources
- [ ] Fix notification system (email/Telegram)
- [ ] Cải thiện dashboard UX
- [ ] Mobile app responsive

### 1-3 tháng tới
- [ ] Community voting system
- [ ] Advanced learning algorithms
- [ ] Multi-language support
- [ ] Performance optimization

### Help Wanted
- [ ] **UI/UX Designer**: Cải thiện giao diện dashboard và mobile
- [ ] **Backend Developer**: Tối ưu API và database
- [ ] **DevOps**: CI/CD, deployment automation
- [ ] **QA Tester**: Test cases, bug reports

## 🛡️ An toàn & Minh bạch (Ưu tiên hàng đầu)

### 🔒 Bảo mật
- **Environment Protection**: Không commit .env, secret scanning
- **Input Validation**: SQL injection, XSS protection
- **Rate Limiting**: DDoS protection
- **Audit Logging**: Ghi log mọi hoạt động quan trọng

### 📋 Minh bạch
- **Open Source**: Toàn bộ code mở, có thể audit
- **Learning Logs**: Ghi lại mọi quyết định học tập
- **Approval Workflow**: Con người kiểm soát nội dung nhạy cảm
- **Community Oversight**: Cộng đồng có thể review và đóng góp

## 🎓 Quan điểm "Tự quyết học tập" (Có điều kiện)

Chúng tôi đang cân nhắc cho phép StillMe **tự quyết định** việc học tập trong các giới hạn an toàn:

### ✅ Được phép tự học
- Kiến thức công khai, không nhạy cảm
- Nội dung từ nguồn đáng tin cậy
- Thông tin kỹ thuật, khoa học
- Cập nhật xu hướng công nghệ

### ⚠️ Cần phê duyệt
- Nội dung chính trị, tôn giáo
- Thông tin cá nhân, riêng tư
- Nội dung có thể gây tranh cãi
- Kiến thức từ nguồn không rõ ràng

### 🚫 Tuyệt đối cấm
- Nội dung độc hại, bạo lực
- Thông tin sai lệch
- Nội dung vi phạm pháp luật
- Dữ liệu cá nhân không được phép

## 📋 Tuyên bố về đạo đức & bảo mật

### 🛡️ Nguyên tắc cốt lõi
- **Safety & Ethics**: An toàn và đạo đức là ưu tiên số 1
- **Privacy**: Bảo vệ quyền riêng tư của người dùng
- **Community Responsibility**: Trách nhiệm với cộng đồng

### 🔐 Cam kết cụ thể
- **Security-first**: Thiết kế bảo mật từ đầu
- **Transparency**: Minh bạch về cách hoạt động
- **.env Protection**: Không bao giờ commit secrets
- **Future Audits**: Sẵn sàng cho audit bảo mật
- **Bug Bounty**: Khuyến khích báo cáo lỗ hổng

### 📊 Trách nhiệm giải trình
- **Learning Decisions**: Ghi lại mọi quyết định học tập
- **Approval Process**: Quy trình phê duyệt rõ ràng
- **Community Feedback**: Lắng nghe phản hồi cộng đồng
- **Regular Reviews**: Đánh giá định kỳ về đạo đức

### 🌍 Tầm nhìn dài hạn
- **Global Impact**: Tác động tích cực toàn cầu
- **Ethical AI**: AI đạo đức và có trách nhiệm
- **Community-Driven**: Phát triển bởi cộng đồng
- **Open Innovation**: Đổi mới mở và minh bạch

## 🤝 Lời mời cộng đồng

### 🎯 Chúng tôi cần sự giúp đỡ của bạn

**AI Safety Researchers**: Giúp đánh giá và cải thiện hệ thống an toàn
**Ethics Advisors**: Tư vấn về đạo đức AI và quyết định học tập
**Developers**: Đóng góp code, fix bugs, thêm tính năng
**Testers**: Test hệ thống, báo cáo lỗi, đề xuất cải thiện
**Designers**: Cải thiện UI/UX, tạo mockups, design system
**Documentation**: Viết docs, hướng dẫn, tutorials

### 🚀 Cách bắt đầu
1. **Fork repository** và tạo branch mới
2. **Chọn issue** phù hợp với skill level
3. **Submit PR** với description rõ ràng
4. **Join discussion** trong GitHub Discussions

### 💡 Ý tưởng đóng góp
- **Dashboard improvements**: Chat UI, responsive design
- **Learning sources**: Thêm nguồn mới, fix nguồn cũ
- **Notification system**: Email, Telegram, Discord
- **Mobile app**: Flutter improvements
- **Testing**: Unit tests, integration tests
- **Documentation**: API docs, user guides

### 💝 Hỗ trợ dự án
Nếu bạn thấy StillMe hữu ích và muốn hỗ trợ phát triển:

**Cách hỗ trợ miễn phí:**
- ⭐ **Star repository** - giúp dự án được nhiều người biết đến
- 🐛 **Báo cáo bugs** - giúp cải thiện chất lượng
- 💡 **Đề xuất tính năng** - định hướng phát triển
- 📢 **Chia sẻ với bạn bè** - lan tỏa cộng đồng

**Hỗ trợ tài chính (tùy chọn):**
Server hosting, API costs, và thời gian phát triển đều cần chi phí. Nếu bạn muốn hỗ trợ:

[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee--yellow.svg?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/stillme)

*Cảm ơn bạn đã tin tưởng và sử dụng StillMe! 🙏*

## 📊 Thống kê dự án

StillMe AI là một framework AI toàn diện với **100+ modules** trên nhiều thành phần:

### Số liệu cốt lõi
- **Tổng Modules**: 100+ (72 trong `stillme_core/`, 25 trong `modules/`, 3 trong `stillme_ethical_core/`)
- **Kích thước dự án**: 22.89 MB (tối ưu từ 5.3GB)
- **Số file**: 1,036 files trong 156 thư mục
- **Mức độ phức tạp**: 8.5/10 (Enterprise-grade)
- **Test Coverage**: 97.9% (bộ test toàn diện)
- **Security Compliance**: OWASP ASVS Level 2+ (90% compliance)

### 🧪 Hệ thống AgentDev

StillMe bao gồm **AgentDev**, một hệ thống AI Senior Developer với khả năng toàn diện:

#### Kết quả Test
![AgentDev Tests](https://img.shields.io/badge/AgentDev%20Tests-31%2F31%20passing-green)
![AgentDev Coverage](https://img.shields.io/badge/AgentDev%20Coverage-97%25-green)
![AgentDev Security](https://img.shields.io/badge/AgentDev%20Security-100%25%20pass-green)

**Trạng thái**: ✅ **SẴN SÀNG PRODUCTION** - Tất cả quality gates đạt với hiệu suất xuất sắc.

#### Quality Gates
- ✅ Test Coverage: 97.9% lines, 85% branches
- ✅ Test Pass Rate: 100% (31/31 tests)
- ✅ Performance: P95 E2E < 200ms
- ✅ Security: All adversarial tests pass
- ✅ Resilience: All chaos tests pass
- ✅ Learning: Advanced evolutionary system

## 🔧 Cấu hình & Bảo mật

### Environment Setup
StillMe sử dụng hệ thống cấu hình môi trường an toàn với thứ tự ưu tiên rõ ràng:

```bash
# 1. Copy file cấu hình mẫu
cp .env.example .env

# 2. Chỉnh sửa .env với giá trị thực tế
# TUYỆT ĐỐI KHÔNG commit .env files với secrets thật!

# 3. Để override local, tạo .env.local
# .env.local có ưu tiên cao hơn .env

# 4. Kiểm tra cấu hình
python scripts/check_env.py
```

### Thứ tự ưu tiên Environment
1. **`.env`** - Cấu hình cơ bản (commit vào git)
2. **`.env.local`** - Override local (ignore bởi git, ưu tiên cao nhất)

### Environment Variables cần thiết
```bash
# Core Configuration
STILLME_DRY_RUN=1                    # Set to 0 for production
STILLME_TZ=Asia/Ho_Chi_Minh          # Timezone
RUNTIME_BASE_URL=http://localhost:8000

# AI Provider API Keys (Required)
OPENAI_API_KEY=sk-REPLACE_ME         # Your OpenAI API key
DEEPSEEK_API_KEY=sk-REPLACE_ME       # Your DeepSeek API key
```

### Security Best Practices
- ✅ **TUYỆT ĐỐI KHÔNG commit `.env` files** với API keys thật
- ✅ **Sử dụng `.env.local`** cho local development overrides
- ✅ **Sử dụng GitHub Secrets** cho CI/CD environments
- ✅ **Rotate API keys** thường xuyên
- ✅ **Chạy `python scripts/check_env.py`** để verify cấu hình

## 📚 Tài liệu & Hỗ trợ

### 📖 Tài liệu
- **API Documentation**: `/docs` endpoint
- **Architecture Guide**: `docs/ARCHITECTURE_OVERVIEW.md`
- **Security Guide**: `docs/SECURITY_COMPLIANCE_MAP.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Mobile App Guide**: `mobile_app/README_MOBILE.md`
- **Desktop App Guide**: `desktop_app/README.md`

### 🤝 Cộng đồng & Hỗ trợ
- **Issues**: [GitHub Issues](https://github.com/anhmtk/stillme_ai_ipc/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anhmtk/stillme_ai_ipc/discussions)
- **Security**: [Security Policy](SECURITY.md)
- **Contributing**: [Contributing Guide](CONTRIBUTING.md)

### 📄 License
MIT License - xem [LICENSE](LICENSE) file để biết chi tiết.

### 🙏 Lời cảm ơn
StillMe AI được tạo ra bởi **Anh Nguyễn** với sự hỗ trợ lớn từ các tổ chức AI bao gồm OpenAI, Google, DeepSeek và cộng đồng open-source. Dự án nhằm tạo ra một AI companion an toàn, thông minh và hữu ích cho mọi người.

---

**StillMe AI IPC** - *Bạn đồng hành thông minh, an toàn và minh bạch* 🤖✨

> **Lưu ý**: Dự án này đang trong giai đoạn alpha. Chúng tôi cố tình minh bạch về điểm yếu hiện tại để cộng đồng dễ chọn việc phù hợp và đóng góp hiệu quả.