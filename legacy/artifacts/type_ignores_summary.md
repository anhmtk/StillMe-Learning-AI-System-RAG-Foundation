# Type Ignore Audit Summary

**Total # type: ignore found: 152**

## By Directory

- `stillme_core\core/`: 67 ignores
- `stillme_core\core\observability/`: 28 ignores
- `stillme_core\core\router/`: 17 ignores
- `stillme_core\core\cli\commands/`: 13 ignores
- `stillme_core\modules/`: 8 ignores
- `stillme_core\core\quality/`: 7 ignores
- `stillme_core\middleware/`: 6 ignores
- `agent_dev\core/`: 2 ignores
- `stillme_core\core\security/`: 2 ignores
- `tests/`: 1 ignores
- `stillme_core\core\self_learning/`: 1 ignores

## By File (Top 20)

- `stillme_core\core\observability\dashboard.py`: 27 ignores
- `stillme_core\core\cli\commands\router.py`: 13 ignores
- `stillme_core\core\memory_security_integration.py`: 11 ignores
- `stillme_core\core\usage_analytics_engine.py`: 10 ignores
- `stillme_core\core\security_compliance_system.py`: 9 ignores
- `stillme_core\core\intelligent_pricing_engine.py`: 8 ignores
- `stillme_core\core\learning_optimization_engine.py`: 8 ignores
- `stillme_core\core\module_governance_system.py`: 6 ignores
- `stillme_core\core\phase2_integration_testing.py`: 6 ignores
- `stillme_core\middleware\reflex_engine.py`: 6 ignores
- `stillme_core\core\router\agent_coordinator.py`: 6 ignores
- `stillme_core\core\quality\code_quality_enforcer.py`: 5 ignores
- `stillme_core\core\router\learning_engine.py`: 5 ignores
- `stillme_core\modules\layered_memory_v1_old.py`: 4 ignores
- `stillme_core\modules\market_intel.py`: 3 ignores
- `stillme_core\core\router\intelligent_router.py`: 3 ignores
- `agent_dev\core\automated_monitor.py`: 2 ignores
- `stillme_core\core\provider_router.py`: 2 ignores
- `stillme_core\core\sandbox_manager.py`: 2 ignores
- `stillme_core\core\quality\auto_fixer.py`: 2 ignores

## All Ignores (First 50)

1. **tests\test_stillme_behavior_matrix.py:32**
   ```
   spec.loader.exec_module(mod)  # type: ignore
   ```

2. **agent_dev\core\automated_monitor.py:28**
   ```
   import psutil  # type: ignore
   ```

3. **agent_dev\core\automated_monitor.py:29**
   ```
   import schedule  # type: ignore
   ```

4. **stillme_core\core\ai_manager.py:387**
   ```
   return execute_agentdev_super_task(task)  # type: ignore
   ```

5. **stillme_core\core\config_defaults.py:24**
   ```
   from dotenv import load_dotenv  # type: ignore
   ```

6. **stillme_core\core\intelligent_pricing_engine.py:27**
   ```
   AutonomousManagementSystem as AMS,  # type: ignore
   ```

7. **stillme_core\core\intelligent_pricing_engine.py:30**
   ```
   LearningOptimizationEngine as LOE,  # type: ignore
   ```

8. **stillme_core\core\intelligent_pricing_engine.py:33**
   ```
   SecurityComplianceSystem as SCS,  # type: ignore
   ```

9. **stillme_core\core\intelligent_pricing_engine.py:35**
   ```
   from .usage_analytics_engine import UsageAnalyticsEngine as UAE  # type: ignore
   ```

10. **stillme_core\core\intelligent_pricing_engine.py:39**
   ```
   AutonomousManagementSystem as AMS,  # type: ignore
   ```

11. **stillme_core\core\intelligent_pricing_engine.py:42**
   ```
   LearningOptimizationEngine as LOE,  # type: ignore
   ```

12. **stillme_core\core\intelligent_pricing_engine.py:45**
   ```
   SecurityComplianceSystem as SCS,  # type: ignore
   ```

13. **stillme_core\core\intelligent_pricing_engine.py:48**
   ```
   UsageAnalyticsEngine as UAE,  # type: ignore
   ```

14. **stillme_core\core\learning_optimization_engine.py:76**
   ```
   def register_endpoint(self, method: str, path: str, handler: Any, auth_required: bool = False) -> None:  # type: ignore
   ```

15. **stillme_core\core\learning_optimization_engine.py:104**
   ```
   def get_system_health(self) -> dict[str, Any]:  # type: ignore
   ```

16. **stillme_core\core\learning_optimization_engine.py:111**
   ```
   def get_autonomous_status(self) -> dict[str, Any]:  # type: ignore
   ```

17. **stillme_core\core\learning_optimization_engine.py:624**
   ```
   performance_values.append(  # type: ignore
   ```

18. **stillme_core\core\learning_optimization_engine.py:628**
   ```
   if len(performance_values) >= 10:  # type: ignore
   ```

19. **stillme_core\core\learning_optimization_engine.py:629**
   ```
   avg_performance = sum(performance_values) / len(performance_values)  # type: ignore
   ```

20. **stillme_core\core\learning_optimization_engine.py:631**
   ```
   patterns.append(  # type: ignore
   ```

21. **stillme_core\core\learning_optimization_engine.py:673**
   ```
   category=KnowledgeCategory.SYSTEM_PATTERNS,  # type: ignore
   ```

22. **stillme_core\core\memory_security_integration.py:254**
   ```
   self.secure_storage = _SecureMemoryManager(secure_config)  # type: ignore
   ```

23. **stillme_core\core\memory_security_integration.py:275**
   ```
   self.performance_monitor.start_monitoring()  # type: ignore
   ```

24. **stillme_core\core\memory_security_integration.py:279**
   ```
   self.integration_bridge.register_endpoint(  # type: ignore
   ```

25. **stillme_core\core\memory_security_integration.py:282**
   ```
   self.integration_bridge.register_endpoint(  # type: ignore
   ```

26. **stillme_core\core\memory_security_integration.py:288**
   ```
   self.integration_bridge.register_endpoint(  # type: ignore
   ```

27. **stillme_core\core\memory_security_integration.py:332**
   ```
   self.memory_system.add_memory(  # type: ignore
   ```

28. **stillme_core\core\memory_security_integration.py:383**
   ```
   results = self.memory_system.search(query=query)  # type: ignore
   ```

29. **stillme_core\core\memory_security_integration.py:433**
   ```
   results = self.memory_system.search(query=query)  # type: ignore
   ```

30. **stillme_core\core\memory_security_integration.py:625**
   ```
   result_security_level = getattr(result.metadata, "get", lambda x, y: y)(  # type: ignore
   ```

31. **stillme_core\core\memory_security_integration.py:720**
   ```
   health_result = self.memory_system.get_health_status()  # type: ignore
   ```

32. **stillme_core\core\memory_security_integration.py:832**
   ```
   )  # type: ignore
   ```

33. **stillme_core\core\module_governance_system.py:28**
   ```
   from .integration_bridge import IntegrationBridge  # type: ignore
   ```

34. **stillme_core\core\module_governance_system.py:29**
   ```
   from .memory_security_integration import MemorySecurityIntegration  # type: ignore
   ```

35. **stillme_core\core\module_governance_system.py:31**
   ```
   from .security_middleware import SecurityMiddleware  # type: ignore
   ```

36. **stillme_core\core\module_governance_system.py:34**
   ```
   from stillme_core.integration_bridge import IntegrationBridge  # type: ignore
   ```

37. **stillme_core\core\module_governance_system.py:36**
   ```
   MemorySecurityIntegration,  # type: ignore
   ```

38. **stillme_core\core\module_governance_system.py:39**
   ```
   from stillme_core.security_middleware import SecurityMiddleware  # type: ignore
   ```

39. **stillme_core\core\phase2_integration_testing.py:23**
   ```
   from .autonomous_management_system import AutonomousManagementSystem  # type: ignore
   ```

40. **stillme_core\core\phase2_integration_testing.py:24**
   ```
   from .learning_optimization_engine import LearningOptimizationEngine  # type: ignore
   ```

41. **stillme_core\core\phase2_integration_testing.py:25**
   ```
   from .security_compliance_system import SecurityComplianceSystem  # type: ignore
   ```

42. **stillme_core\core\phase2_integration_testing.py:29**
   ```
   AutonomousManagementSystem,  # type: ignore
   ```

43. **stillme_core\core\phase2_integration_testing.py:32**
   ```
   LearningOptimizationEngine,  # type: ignore
   ```

44. **stillme_core\core\phase2_integration_testing.py:35**
   ```
   SecurityComplianceSystem,  # type: ignore
   ```

45. **stillme_core\core\policy_templates.py:30**
   ```
   def get_template(template_name: str, locale: str = "vi", context: dict = None) -> str:  # type: ignore
   ```

46. **stillme_core\core\provider_router.py:21**
   ```
   return "safe"  # type: ignore[return-value]
   ```

47. **stillme_core\core\provider_router.py:22**
   ```
   return m  # type: ignore[return-value]
   ```

48. **stillme_core\core\safety_guard.py:27**
   ```
   from .policy_templates import get_template  # type: ignore
   ```

49. **stillme_core\core\sandbox_manager.py:29**
   ```
   def start_container(self) -> bool:  # type: ignore
   ```

50. **stillme_core\core\sandbox_manager.py:107**
   ```
   return result  # type: ignore
   ```

... and 102 more (see CSV for complete list)
