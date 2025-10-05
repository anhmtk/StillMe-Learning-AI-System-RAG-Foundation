# Skip Policy Audit - Hiện trạng Skip/Cancel/Abort/Stop

## Tổng quan
Audit này tìm hiểu hiện trạng xử lý Skip/Cancel/Abort/Stop trong toàn bộ repo StillMe để chuẩn hoá hành vi "Skip = Diagnose" thay vì "Skip = Cancel".

## Kết quả Audit

### 1. Files có chứa Skip/Cancel/Abort/Stop
**Tổng cộng: 206 files** chứa các từ khóa này, bao gồm:

#### UI Components:
- `stillme_desktop_app.py` - Desktop app UI
- `desktop_chat_app.py` - Desktop chat interface  
- `mobile_app_simple/lib/ui/screens/settings/settings_screen.dart` - Mobile settings
- `mobile_app_simple/lib/data/chat_repository.dart` - Mobile chat logic

#### Backend Services:
- `app.py` - Main backend server
- `app_with_core.py` - Core framework backend
- `stillme_core/framework.py` - Core framework
- `stillme_platform/gateway/main.py` - Gateway service

#### CLI & Tools:
- `scripts/router_cli.py` - Router CLI
- `scripts/router_dashboard.py` - Router dashboard
- `dev_agent_cli.py` - Dev agent CLI
- `run_automated_scheduler.py` - Scheduler runner

### 2. Các hàm cancel()/abort()/stop() được tìm thấy

#### Async Task Cancellation:
```python
# stillme_platform/gateway/services/notification_manager.py:174
self.processing_task.cancel()

# stillme_core/framework.py:1068  
self._heartbeat_task.cancel()

# stillme_core/core/core_metrics_collector.py:242
self._flush_task.cancel()
```

#### Service Stop Methods:
```python
# stillme_platform/gateway/main.py:127
await notification_manager.stop()

# stillme_core/modules/automated_scheduler.py:78
self.stop()

# stillme_core/core/cli/commands/observability.py:61
dashboard.stop()
```

### 3. Điểm có thể đọc log/stream

#### Log Files:
- `stillme_core/core/observability/logger.py` - Centralized logging
- `stillme_core/core/observability/dashboard.py` - Dashboard logs
- `stillme_platform/gateway/services/notification_manager.py` - Gateway logs

#### Stream Sources:
- WebSocket connections: `stillme_platform/gateway/core/websocket_manager.py`
- HTTP streams: `stillme_core/core/provider_router.py`
- CLI output: `scripts/router_cli.py`

#### PID/Heartbeat Tracking:
- `stillme_core/framework.py` - Framework heartbeat
- `stillme_platform/gateway/core/websocket_manager.py` - WebSocket heartbeat
- `stillme_core/core/core_metrics_collector.py` - System monitoring

### 4. Vấn đề hiện tại

#### Skip = Cancel (Cần sửa):
- **Desktop apps**: Không có xử lý Skip riêng biệt
- **Mobile apps**: Không có xử lý Skip riêng biệt  
- **CLI tools**: Không có xử lý Skip riêng biệt
- **Backend services**: Không có xử lý Skip riêng biệt

#### Thiếu Policy:
- Không có policy trung tâm cho Skip behavior
- Không có runtime loader cho interaction policy
- Không có diagnose function cho Skip

#### Thiếu Log Access:
- Không có standardized log tailing
- Không có heartbeat checking
- Không có PID monitoring

## Khuyến nghị

### 1. Tạo Policy Trung Tâm
- `policies/INTERACTION_POLICY.yaml` - Single source of truth
- `runtime/interaction_policy.ts` - Policy loader
- `runtime/skip_diagnose.ts` - Diagnose function

### 2. Cập nhật UI Components
- Desktop apps: Thêm Skip = Diagnose behavior
- Mobile apps: Thêm Skip = Diagnose behavior
- CLI tools: Thêm Skip = Diagnose behavior

### 3. Standardize Log Access
- Centralized log tailing function
- Heartbeat checking mechanism
- PID monitoring system

### 4. CI/CD Integration
- Pre-commit hooks để check policy loading
- CI checks để verify Skip ≠ Cancel
- Integration tests cho Skip behavior

## Next Steps
1. Tạo `policies/INTERACTION_POLICY.yaml`
2. Implement `runtime/skip_diagnose.ts`
3. Update UI components để sử dụng policy
4. Add CI checks và tests
