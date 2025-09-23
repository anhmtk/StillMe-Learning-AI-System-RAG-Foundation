# AgentDev Repair Plan

## 🎯 Mục tiêu tổng thể
Sửa chữa và hoàn thiện AgentDev system để đạt được:
- **Success Rate**: >80% (hiện tại 0%)
- **Performance**: <10s per step (hiện tại 71s)
- **Reliability**: Stable test harness
- **Safety**: Ethics validation và guardrails

## 📋 Kế hoạch theo bước nhỏ (≤30 phút/bước)

### **PHASE 1: CRITICAL FIXES (Day 1)**

#### **Step 1: Install Missing Dependencies** ⏱️ 5 phút
- **Mục tiêu**: Cài đặt các dependencies còn thiếu
- **Files chạm**: `requirements.txt`
- **Lệnh chạy**: 
  ```bash
  pip install jsonschema httpx gitpython rich typer pydantic
  ```
- **Tiêu chí chấp nhận**: `pip list` shows all packages installed
- **Rollback**: `pip uninstall <package>`

#### **Step 2: Fix Import Errors** ⏱️ 10 phút
- **Mục tiêu**: Sửa các import errors trong test suite
- **Files chạm**: `tests/conftest.py`, `stillme_core/__init__.py`
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/test_agentdev_loop.py -v
  ```
- **Tiêu chí chấp nhận**: `pytest: 2 passed, 1 xfailed, 0 failed`
- **Rollback**: Revert import changes

#### **Step 3: Fix Terminal Observation Loop** ⏱️ 20 phút
- **Mục tiêu**: Cải thiện việc đọc terminal output
- **Files chạm**: `stillme_core/executor.py`, `stillme_core/verifier.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test terminal parsing" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: Terminal output được parse correctly, không có "no tests ran"
- **Rollback**: Revert executor changes

#### **Step 4: Add Basic Error Handling** ⏱️ 15 phút
- **Mục tiêu**: Thêm try-catch blocks cho critical operations
- **Files chạm**: `stillme_core/controller.py`, `stillme_core/planner.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test error handling" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: System không crash khi có lỗi, có error messages rõ ràng
- **Rollback**: Revert error handling changes

#### **Step 5: Improve Logging** ⏱️ 10 phút
- **Mục tiêu**: Thêm structured logging cho debugging
- **Files chạm**: `stillme_core/logging_utils.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test logging" --max-steps 1 --verbose
  ```
- **Tiêu chí chấp nhận**: Logs được ghi vào file với format consistent
- **Rollback**: Revert logging changes

### **PHASE 2: STABILIZATION (Day 2)**

#### **Step 6: Stabilize Test Harness** ⏱️ 25 phút
- **Mục tiêu**: Đảm bảo test framework hoạt động ổn định
- **Files chạm**: `tests/conftest.py`, `stillme_core/sandbox.py`
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/ -v --tb=short
  ```
- **Tiêu chí chấp nhận**: `pytest: X passed, Y failed, Z warnings` (no import errors)
- **Rollback**: Revert test changes

#### **Step 7: Fix Sandbox Path Issues** ⏱️ 20 phút
- **Mục tiêu**: Sửa path conflicts giữa sandbox và main repo
- **Files chạm**: `stillme_core/executor.py`, `stillme_core/sandbox.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test sandbox" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: Không có "file or directory not found" errors
- **Rollback**: Revert sandbox changes

#### **Step 8: Optimize Performance** ⏱️ 30 phút
- **Mục tiêu**: Giảm thời gian execution từ 71s xuống <10s
- **Files chạm**: `stillme_core/planner.py`, `stillme_core/executor.py`
- **Lệnh chạy**: 
  ```bash
  time python -m stillme_core.agent_dev --goal "Test performance" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: Execution time <10s per step
- **Rollback**: Revert performance changes

### **PHASE 3: ENHANCEMENT (Day 3)**

#### **Step 9: Add Model Router Fallback** ⏱️ 25 phút
- **Mục tiêu**: Thêm fallback mechanism cho AI model calls
- **Files chạm**: `stillme_core/ai_manager.py`, `stillme_core/planner.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test fallback" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: System hoạt động khi primary model fail
- **Rollback**: Revert fallback changes

#### **Step 10: Add Safety Mechanisms** ⏱️ 30 phút
- **Mục tiêu**: Tích hợp ethics validation
- **Files chạm**: `stillme_core/controller.py`, `framework.py`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --goal "Test safety" --max-steps 1
  ```
- **Tiêu chí chấp nhận**: Code changes được validate bởi EthicalCoreSystem
- **Rollback**: Revert safety changes

#### **Step 11: Add Integration Tests** ⏱️ 20 phút
- **Mục tiêu**: Tạo integration tests cho end-to-end workflow
- **Files chạm**: `tests/test_agentdev_integration.py`
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/test_agentdev_integration.py -v
  ```
- **Tiêu chí chấp nhận**: `pytest: X passed, 0 failed`
- **Rollback**: Delete integration test file

#### **Step 12: Performance Benchmarking** ⏱️ 15 phút
- **Mục tiêu**: Tạo benchmark tests cho performance monitoring
- **Files chạm**: `tests/test_agentdev_performance.py`
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/test_agentdev_performance.py -v
  ```
- **Tiêu chí chấp nhận**: Performance metrics được track và report
- **Rollback**: Delete performance test file

### **PHASE 4: VALIDATION (Day 4)**

#### **Step 13: End-to-End Testing** ⏱️ 30 phút
- **Mục tiêu**: Test toàn bộ workflow với real scenarios
- **Files chạm**: `tests/test_agentdev_e2e.py`
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/test_agentdev_e2e.py -v
  ```
- **Tiêu chí chấp nhận**: Success rate >80%
- **Rollback**: Revert to previous working state

#### **Step 14: Documentation Update** ⏱️ 20 phút
- **Mục tiêu**: Cập nhật documentation với changes mới
- **Files chạm**: `README.md`, `AGENTDEV_OVERVIEW.md`
- **Lệnh chạy**: 
  ```bash
  python -m stillme_core.agent_dev --help
  ```
- **Tiêu chí chấp nhận**: Help output shows all options correctly
- **Rollback**: Revert documentation changes

#### **Step 15: Final Validation** ⏱️ 15 phút
- **Mục tiêu**: Final check toàn bộ system
- **Files chạm**: All modified files
- **Lệnh chạy**: 
  ```bash
  python -m pytest tests/ -v
  python -m stillme_core.agent_dev --goal "Final test" --max-steps 2
  ```
- **Tiêu chí chấp nhận**: 
  - `pytest: X passed, Y failed, Z warnings` (Y < 5)
  - `Success rate: >80%`
  - `Execution time: <10s per step`
- **Rollback**: Revert all changes

## 🎯 Success Criteria

### **Minimum Viable Product (MVP)**
- [ ] Success rate >50%
- [ ] Execution time <30s per step
- [ ] No critical errors
- [ ] Basic test coverage

### **Production Ready**
- [ ] Success rate >80%
- [ ] Execution time <10s per step
- [ ] Comprehensive error handling
- [ ] Safety mechanisms active
- [ ] Full test coverage

### **Enterprise Grade**
- [ ] Success rate >95%
- [ ] Execution time <5s per step
- [ ] Advanced monitoring
- [ ] Security audit passed
- [ ] Performance benchmarks

## 🚨 Risk Mitigation

### **High Risk Items**
1. **Terminal Observation Loop**: Có thể break existing functionality
2. **Performance Optimization**: Có thể introduce bugs
3. **Safety Mechanisms**: Có thể block legitimate operations

### **Mitigation Strategies**
1. **Incremental Changes**: Mỗi step nhỏ, test ngay
2. **Rollback Plan**: Mỗi step có rollback strategy
3. **Monitoring**: Track metrics sau mỗi change
4. **Testing**: Comprehensive test coverage

## 📊 Progress Tracking

| Step | Status | Duration | Success Criteria | Notes |
|------|--------|----------|------------------|-------|
| 1 | ⏳ Pending | 5 min | Dependencies installed | |
| 2 | ⏳ Pending | 10 min | Import errors fixed | |
| 3 | ⏳ Pending | 20 min | Terminal parsing works | |
| 4 | ⏳ Pending | 15 min | Error handling added | |
| 5 | ⏳ Pending | 10 min | Logging improved | |
| 6 | ⏳ Pending | 25 min | Test harness stable | |
| 7 | ⏳ Pending | 20 min | Sandbox paths fixed | |
| 8 | ⏳ Pending | 30 min | Performance optimized | |
| 9 | ⏳ Pending | 25 min | Fallback mechanism | |
| 10 | ⏳ Pending | 30 min | Safety mechanisms | |
| 11 | ⏳ Pending | 20 min | Integration tests | |
| 12 | ⏳ Pending | 15 min | Performance benchmarks | |
| 13 | ⏳ Pending | 30 min | E2E testing | |
| 14 | ⏳ Pending | 20 min | Documentation update | |
| 15 | ⏳ Pending | 15 min | Final validation | |

**Total Estimated Time**: 6.5 hours (spread over 4 days)

## 🔄 Iteration Plan

### **Daily Iterations**
- **Day 1**: Steps 1-5 (Critical fixes)
- **Day 2**: Steps 6-8 (Stabilization)
- **Day 3**: Steps 9-12 (Enhancement)
- **Day 4**: Steps 13-15 (Validation)

### **Weekly Review**
- Review progress against success criteria
- Adjust plan based on findings
- Update risk assessment
- Plan next iteration

## 📝 Notes

- Mỗi step phải có clear success criteria
- Rollback plan cho mỗi step
- Monitor metrics sau mỗi change
- Document lessons learned
- Update plan based on real-world findings
