# Near-Duplicate Code Analysis Report

## **Tổng quan**
- **Ngày phân tích**: 2025-01-10
- **Files scanned**: 690 meaningful Python files
- **Files normalized**: 686 files
- **Near-duplicate clusters**: 8007 clusters
- **Similarity threshold**: 0.90 (90%)

## **Phương pháp phát hiện**
1. **AST Normalization**: Chuẩn hóa code bằng cách loại bỏ tên biến và literals
2. **Token Sequence**: Tạo chuỗi token từ AST node types
3. **Cosine Similarity**: Tính độ tương đồng giữa các file trong cùng thư mục
4. **Clustering**: Gom nhóm các file có similarity ≥ 90%

## **Top Near-Duplicate Clusters**

### **Cluster 1: AgentDev Related Files**
- **Canonical**: `agent_dev.py`
- **Non-canonical**: `agentdev_validation_system.py`
- **Similarity**: High (likely similar structure)

### **Cluster 2: Analysis Tools**
- **Canonical**: `agentdev_validation_system.py`
- **Non-canonical**: 
  - `analyze_agentdev_interface.py`
  - `analyze_f821.py`
  - `analyze_f821_evidence.py`
- **Similarity**: High (analysis pattern)

### **Cluster 3: API Servers**
- **Canonical**: `api_server.py`
- **Non-canonical**: Multiple API-related files
- **Similarity**: High (server setup pattern)

## **Khuyến nghị**

### **Phase 1: Safe Cleanup**
- Ưu tiên attic các non-canonical files có:
  - `inbound_imports == 0`
  - `executed_lines == 0`
  - `git_touches <= 1`

### **Phase 2: Code Consolidation**
- Thay thế imports từ non-canonical sang canonical
- Merge unique functionality vào canonical file
- Attic remaining non-canonical files

### **Phase 3: Verification**
- Chạy tests sau mỗi consolidation
- Đảm bảo không break functionality
- Update documentation

## **Safety Measures**
- ✅ Chỉ attic files không được sử dụng
- ✅ Giữ lại canonical files
- ✅ Rollback capability maintained
- ✅ Test sau mỗi thay đổi

## **Next Steps**
1. Integrate near-dupe detection vào redundant scoring
2. Prioritize attic non-canonical files với score cao
3. Plan code consolidation cho Wave-1e
