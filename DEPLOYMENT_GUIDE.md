
🚀 STILLME GATEWAY SMART ROUTING - DEPLOYMENT GUIDE
==================================================

📋 FILES CREATED:
✅ deploy_smart_routing.sh - VPS deployment script
✅ gateway_integration_patch.py - Integration guide
✅ final_verification_test.py - This verification script

🔧 DEPLOYMENT STEPS:

1. COPY FILES TO VPS:
   scp deploy_smart_routing.sh root@160.191.89.99:/opt/stillme/
   scp gateway_integration_patch.py root@160.191.89.99:/opt/stillme/

2. RUN DEPLOYMENT SCRIPT:
   ssh root@160.191.89.99
   cd /opt/stillme
   chmod +x deploy_smart_routing.sh
   ./deploy_smart_routing.sh

3. UPDATE GATEWAY CODE:
   - Edit your gateway's chat endpoint
   - Add: from smart_router import route_message
   - Replace chat logic with smart routing

4. RESTART SERVICE:
   sudo systemctl restart stillme-gateway

5. VERIFY DEPLOYMENT:
   python final_verification_test.py

🔧 ROUTING CONTROLS:
- ROUTING_MODE=auto|force_gemma|force_cloud
- DISABLE_CLOUD=0|1
- GEMMA_TIMEOUT=2.5 (seconds)
- DEEPSEEK_TIMEOUT=10.0 (seconds)

📊 EXPECTED RESULTS AFTER FIX:
- Simple messages → gemma2:2b (local, fast, free)
- Complex messages → deepseek-chat (cloud, powerful, paid)
- Timeout fallback → gemma2:2b-fallback
- Success rates: Simple 90%+, Complex 80%+

🎯 SUCCESS CRITERIA:
✅ Simple messages use Gemma (not DeepSeek)
✅ Complex messages use DeepSeek (not timeout)
✅ Fallback works on timeout
✅ No sensitive data in logs
✅ Environment controls working

⚠️ TROUBLESHOOTING:
- If Gemma not working: Check Ollama service
- If DeepSeek failing: Check API key and network
- If routing wrong: Check ROUTING_MODE setting
- If timeout: Adjust timeout values in .env

📞 SUPPORT:
- Check logs: journalctl -u stillme-gateway -f
- Test scripts: /opt/stillme/tools/test_vps_gateway_*.sh
- Environment: cat /opt/stillme/.env | grep ROUTING
