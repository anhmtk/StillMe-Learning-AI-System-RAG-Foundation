# AI Router Testing & Monitoring Scripts

This directory contains various scripts for testing, monitoring, and managing the AI router system.

## 🚀 Quick Start

### 1. **Test the Router (Recommended)**
```bash
# Run comprehensive tests
python scripts/test_router.py --all

# Or run individual test suites
python scripts/test_router.py --unit
python scripts/test_router.py --integration
python scripts/test_router.py --performance
```

### 2. **Debug a Specific Prompt**
```bash
# Debug why a prompt is routed to a specific model
python scripts/debug_router.py --prompt "viết code Python tính giai thừa"
```

### 3. **Monitor Performance**
```bash
# Run performance benchmark
python scripts/benchmark_router.py --performance

# Or run full benchmark suite
python scripts/benchmark_router.py --full
```

## 📋 Available Scripts

### **Core Testing Scripts**
- **`test_router.py`** - Comprehensive test suite with unit, integration, and performance tests
- **`validate_router.py`** - Quick validation of router configuration and performance
- **`benchmark_router.py`** - Performance benchmarking with detailed metrics

### **Debugging & Analysis Scripts**
- **`debug_router.py`** - Debug routing decisions with detailed analysis
- **`router_tools.py`** - Various utility functions for testing and validation
- **`monitor_router.py`** - Real-time performance monitoring

### **Management Scripts**
- **`router_manager.py`** - Router status, configuration, and maintenance
- **`calibrate_router.py`** - Fine-tune router weights and thresholds
- **`router_cli.py`** - Command-line interface for interactive testing

### **Monitoring Scripts**
- **`router_dashboard.py`** - Real-time dashboard for router monitoring
- **`router_cli.py`** - Interactive command-line interface

## 🎯 Common Use Cases

### **1. Initial Testing**
```bash
# Run all tests to ensure router is working
python scripts/test_router.py --all

# Check router status
python scripts/router_manager.py --status
```

### **2. Debugging Routing Issues**
```bash
# Debug why a prompt isn't routing correctly
python scripts/debug_router.py --prompt "your prompt here"

# Run interactive debugging
python scripts/debug_router.py --interactive
```

### **3. Performance Optimization**
```bash
# Benchmark current performance
python scripts/benchmark_router.py --full

# Calibrate router for better accuracy
python scripts/calibrate_router.py --auto-tune

# Monitor performance in real-time
python scripts/monitor_router.py --live
```

### **4. Configuration Management**
```bash
# View current configuration
python scripts/router_manager.py --config

# Run maintenance checks
python scripts/router_manager.py --maintenance

# Export configuration
python scripts/calibrate_router.py --export config.env
```

### **5. Interactive Testing**
```bash
# Start interactive CLI
python scripts/router_cli.py --interactive

# Test specific prompts
python scripts/router_cli.py --prompt "chào bạn"

# Batch process prompts from file
python scripts/router_cli.py --batch prompts.txt
```

## Understanding Test Results

### **Test Output Interpretation**
- **✅ PASS** - Test passed successfully
- **❌ FAIL** - Test failed, check error message
- **⚠️ WARN** - Test passed but with warnings

### **Performance Grades**
- **A+ (Excellent)** - < 1ms average analysis time
- **A (Very Good)** - < 5ms average analysis time
- **B (Good)** - < 10ms average analysis time
- **C (Acceptable)** - < 50ms average analysis time
- **D (Needs Improvement)** - > 50ms average analysis time

### **Accuracy Targets**
- **Simple Prompts** - Should route to `gemma2:2b` (target: 80%+ accuracy)
- **Coding Prompts** - Should route to `deepseek-coder:6.7b` (target: 80%+ accuracy)
- **Complex Prompts** - Should route to `deepseek-chat` (target: 80%+ accuracy)

## Configuration

### **Environment Variables**
```bash
# Complexity analysis weights
COMPLEXITY_WEIGHT_LENGTH=0.15
COMPLEXITY_WEIGHT_COMPLEX_INDICATORS=0.25
COMPLEXITY_WEIGHT_ACADEMIC_TERMS=0.35
COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS=0.3
COMPLEXITY_WEIGHT_MULTI_PART=0.15
COMPLEXITY_WEIGHT_CONDITIONAL=0.2
COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC=0.4

# Complexity thresholds
COMPLEXITY_THRESHOLD_SIMPLE=0.4
COMPLEXITY_THRESHOLD_MEDIUM=0.7
```

### **Router Configuration Files**
- **`.env`** - Environment variables for configuration
- **`router_config_*.env`** - Exported configuration files
- **`best_router_config_*.env`** - Auto-tuned optimal configurations

## 📊 Output Files

### **Test Results**
- **`test_results_*.json`** - Detailed test results
- **`benchmark_results_*.json`** - Performance benchmark data
- **`validation_results_*.json`** - Validation check results

### **Session Data**
- **`router_session_*.json`** - Session monitoring data
- **`router_cli_session_*.json`** - CLI session data
- **`monitoring_data_*.json`** - Real-time monitoring data

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Import Errors**
```bash
# Ensure stillme_core is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/stillme_core"
```

#### **2. Performance Issues**
```bash
# Check system resources
python scripts/router_manager.py --status

# Run performance tests
python scripts/benchmark_router.py --performance
```

#### **3. Routing Accuracy Issues**
```bash
# Debug specific prompts
python scripts/debug_router.py --prompt "problematic prompt"

# Run accuracy tests
python scripts/validate_router.py --full

# Calibrate router
python scripts/calibrate_router.py --auto-tune
```

#### **4. Configuration Problems**
```bash
# Validate configuration
python scripts/validate_router.py --full

# Check environment variables
python scripts/router_manager.py --config

# Reset to defaults
unset COMPLEXITY_WEIGHT_*
unset COMPLEXITY_THRESHOLD_*
```

### **Getting Help**
```bash
# Show help for any script
python scripts/script_name.py --help

# Run with verbose output
python scripts/script_name.py --verbose

# Export results for analysis
python scripts/script_name.py --export results.json
```

## 📈 Monitoring & Maintenance

### **Daily Checks**
```bash
# Quick status check
python scripts/router_manager.py --status

# Run validation
python scripts/validate_router.py --quick
```

### **Weekly Maintenance**
```bash
# Full test suite
python scripts/test_router.py --all

# Performance benchmark
python scripts/benchmark_router.py --full

# Maintenance tasks
python scripts/router_manager.py --maintenance
```

### **Monthly Optimization**
```bash
# Calibrate router
python scripts/calibrate_router.py --auto-tune

# Full validation
python scripts/validate_router.py --full

# Performance analysis
python scripts/benchmark_router.py --full --export monthly_benchmark.json
```

## 🎉 Success Metrics

### **Target Performance**
- **Analysis Time**: < 5ms average
- **Accuracy**: > 80% correct routing
- **Reliability**: > 99% uptime
- **Memory Usage**: < 100MB increase

### **Quality Gates**
- All unit tests pass
- Integration tests pass
- Performance tests pass
- Validation checks pass

## 📚 Additional Resources

- **`docs/AI_ROUTER_OPTIMIZATION_REPORT.md`** - Detailed optimization report
- **`stillme_core/modules/api_provider_manager.py`** - Router implementation
- **`tests/test_router.py`** - Unit test suite
- **`.env.example`** - Configuration template

---

**Need Help?** Check the error messages, run with `--verbose`, or examine the exported JSON files for detailed information.
