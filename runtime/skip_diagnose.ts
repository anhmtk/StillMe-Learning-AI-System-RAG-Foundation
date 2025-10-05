/**
 * StillMe Skip Diagnose Function
 * Cài đặt hành vi Skip = Diagnose thay vì Cancel
 * 
 * Purpose: Chẩn đoán trạng thái task khi user bấm Skip
 * Usage: Gọi diagnoseOnSkip() khi user bấm Skip button
 */

import * as fs from 'fs';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import { getInteractionPolicy, getLogTailingConfig, getHeartbeatConfig, getPidConfig } from './interaction_policy';

// Types cho diagnosis result
export interface SkipDiagnosisResult {
  state: 'COMPLETED' | 'RUNNING' | 'STALLED' | 'UNKNOWN';
  details: string;
  confidence: number; // 0-1
  recommendations: string[];
  logSnippet?: string;
  heartbeatStatus?: boolean;
  pidStatus?: boolean;
}

export interface SkipDiagnoseOptions {
  logPath?: string;
  pid?: number;
  heartbeatPath?: string;
  diagnoseMs?: number;
  processName?: string;
  workingDirectory?: string;
}

/**
 * Diagnose task status when Skip is pressed
 * 
 * @param opts - Diagnosis options
 * @returns Promise<SkipDiagnosisResult>
 */
export async function diagnoseOnSkip(opts: SkipDiagnoseOptions = {}): Promise<SkipDiagnosisResult> {
  const policy = getInteractionPolicy();
  const logConfig = getLogTailingConfig();
  const heartbeatConfig = getHeartbeatConfig();
  const pidConfig = getPidConfig();
  
  const {
    logPath,
    pid,
    heartbeatPath,
    diagnoseMs = policy.skip.timeouts.diagnose_ms,
    processName,
    workingDirectory = process.cwd()
  } = opts;

  console.log(`🔍 Diagnosing task status (Skip pressed)...`);
  console.log(`⏱️ Diagnose timeout: ${diagnoseMs}ms`);

  try {
    // Parallel diagnosis tasks
    const [logAnalysis, heartbeatStatus, pidStatus] = await Promise.allSettled([
      analyzeLogs(logPath, logConfig, workingDirectory),
      checkHeartbeat(heartbeatPath, heartbeatConfig, workingDirectory),
      checkPid(pid, pidConfig, workingDirectory)
    ]);

    // Combine results
    const result = combineDiagnosisResults(
      logAnalysis,
      heartbeatStatus,
      pidStatus,
      diagnoseMs
    );

    console.log(`📊 Diagnosis result: ${result.state}`);
    console.log(`📝 Details: ${result.details}`);
    console.log(`🎯 Confidence: ${(result.confidence * 100).toFixed(1)}%`);

    return result;

  } catch (error) {
    console.error(`❌ Diagnosis failed: ${error}`);
    return {
      state: 'UNKNOWN',
      details: `Diagnosis failed: ${error}`,
      confidence: 0,
      recommendations: ['Check logs manually', 'Restart task if needed']
    };
  }
}

/**
 * Analyze log files for task status
 */
async function analyzeLogs(
  logPath: string | undefined,
  logConfig: any,
  workingDirectory: string
): Promise<{ state: string; snippet: string; confidence: number }> {
  const logFiles = logPath ? [logPath] : findLogFiles(workingDirectory);
  
  if (logFiles.length === 0) {
    return { state: 'UNKNOWN', snippet: 'No log files found', confidence: 0 };
  }

  let latestLog = '';
  let latestSize = 0;

  // Find the most recent log file
  for (const logFile of logFiles) {
    try {
      const stats = fs.statSync(logFile);
      if (stats.size > latestSize) {
        latestSize = stats.size;
        latestLog = logFile;
      }
    } catch (error) {
      // Skip inaccessible files
      continue;
    }
  }

  if (!latestLog) {
    return { state: 'UNKNOWN', snippet: 'No accessible log files', confidence: 0 };
  }

  try {
    // Read last N lines
    const lines = await tailFile(latestLog, logConfig.default_lines);
    const snippet = lines.join('\n');
    
    // Analyze patterns
    const state = analyzeLogPatterns(lines, logConfig.patterns);
    const confidence = calculateLogConfidence(lines, logConfig.patterns);

    return { state, snippet, confidence };

  } catch (error) {
    return { state: 'UNKNOWN', snippet: `Log analysis failed: ${error}`, confidence: 0 };
  }
}

/**
 * Check heartbeat status
 */
async function checkHeartbeat(
  heartbeatPath: string | undefined,
  heartbeatConfig: any,
  workingDirectory: string
): Promise<boolean> {
  const heartbeatFiles = heartbeatPath ? [heartbeatPath] : heartbeatConfig.files;
  
  for (const heartbeatFile of heartbeatFiles) {
    const fullPath = path.resolve(workingDirectory, heartbeatFile);
    
    try {
      if (fs.existsSync(fullPath)) {
        const stats = fs.statSync(fullPath);
        const age = Date.now() - stats.mtime.getTime();
        
        // Check if heartbeat is recent
        if (age < heartbeatConfig.timeout_ms) {
          return true;
        }
      }
    } catch (error) {
      // Continue to next file
      continue;
    }
  }
  
  return false;
}

/**
 * Check PID status
 */
async function checkPid(
  pid: number | undefined,
  pidConfig: any,
  workingDirectory: string
): Promise<boolean> {
  if (pid) {
    return isProcessRunning(pid);
  }

  // Check PID files
  for (const pidFile of pidConfig.files) {
    const fullPath = path.resolve(workingDirectory, pidFile);
    
    try {
      if (fs.existsSync(fullPath)) {
        const pidContent = fs.readFileSync(fullPath, 'utf8').trim();
        const pidNum = parseInt(pidContent);
        
        if (!isNaN(pidNum) && isProcessRunning(pidNum)) {
          return true;
        }
      }
    } catch (error) {
      // Continue to next file
      continue;
    }
  }
  
  return false;
}

/**
 * Find log files in working directory
 */
function findLogFiles(workingDirectory: string): string[] {
  const logFiles: string[] = [];
  const commonLogPaths = [
    'logs/app.log',
    'logs/error.log',
    'logs/debug.log',
    'runtime/current.log',
    'app.log',
    'error.log',
    'debug.log'
  ];

  for (const logPath of commonLogPaths) {
    const fullPath = path.resolve(workingDirectory, logPath);
    if (fs.existsSync(fullPath)) {
      logFiles.push(fullPath);
    }
  }

  return logFiles;
}

/**
 * Tail file to get last N lines
 */
async function tailFile(filePath: string, lines: number): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const tail = spawn('tail', ['-n', lines.toString(), filePath]);
    let output = '';
    let error = '';

    tail.stdout.on('data', (data) => {
      output += data.toString();
    });

    tail.stderr.on('data', (data) => {
      error += data.toString();
    });

    tail.on('close', (code) => {
      if (code === 0) {
        resolve(output.trim().split('\n'));
      } else {
        reject(new Error(`tail failed: ${error}`));
      }
    });
  });
}

/**
 * Analyze log patterns to determine state
 */
function analyzeLogPatterns(lines: string[], patterns: any): string {
  const text = lines.join('\n').toLowerCase();
  
  // Check for completion patterns
  for (const pattern of patterns.completed) {
    if (text.includes(pattern.toLowerCase())) {
      return 'COMPLETED';
    }
  }
  
  // Check for error patterns
  for (const pattern of patterns.error) {
    if (text.includes(pattern.toLowerCase())) {
      return 'STALLED';
    }
  }
  
  // Check for running patterns
  for (const pattern of patterns.running) {
    if (text.includes(pattern.toLowerCase())) {
      return 'RUNNING';
    }
  }
  
  return 'UNKNOWN';
}

/**
 * Calculate confidence based on log analysis
 */
function calculateLogConfidence(lines: string[], patterns: any): number {
  let confidence = 0;
  const text = lines.join('\n').toLowerCase();
  
  // Higher confidence for multiple matching patterns
  const completedMatches = patterns.completed.filter((p: string) => 
    text.includes(p.toLowerCase())
  ).length;
  
  const errorMatches = patterns.error.filter((p: string) => 
    text.includes(p.toLowerCase())
  ).length;
  
  const runningMatches = patterns.running.filter((p: string) => 
    text.includes(p.toLowerCase())
  ).length;
  
  // Calculate confidence based on pattern matches
  const totalMatches = completedMatches + errorMatches + runningMatches;
  if (totalMatches > 0) {
    confidence = Math.min(0.9, totalMatches * 0.3);
  }
  
  // Boost confidence for recent activity
  if (lines.length > 0) {
    confidence += 0.1;
  }
  
  return Math.min(1, confidence);
}

/**
 * Check if process is running
 */
function isProcessRunning(pid: number): boolean {
  try {
    // On Windows, use tasklist
    if (process.platform === 'win32') {
      const { execSync } = require('child_process');
      const result = execSync(`tasklist /FI "PID eq ${pid}"`, { encoding: 'utf8' });
      return result.includes(pid.toString());
    } else {
      // On Unix-like systems, use kill -0
      process.kill(pid, 0);
      return true;
    }
  } catch (error) {
    return false;
  }
}

/**
 * Combine diagnosis results
 */
function combineDiagnosisResults(
  logAnalysis: PromiseSettledResult<any>,
  heartbeatStatus: PromiseSettledResult<boolean>,
  pidStatus: PromiseSettledResult<boolean>,
  diagnoseMs: number
): SkipDiagnosisResult {
  const logResult = logAnalysis.status === 'fulfilled' ? logAnalysis.value : null;
  const heartbeat = heartbeatStatus.status === 'fulfilled' ? heartbeatStatus.value : false;
  const pid = pidStatus.status === 'fulfilled' ? pidStatus.value : false;

  let state: 'COMPLETED' | 'RUNNING' | 'STALLED' | 'UNKNOWN' = 'UNKNOWN';
  let details = '';
  let confidence = 0;
  const recommendations: string[] = [];

  // Determine state based on evidence
  if (logResult) {
    state = logResult.state as any;
    confidence = logResult.confidence;
    details = `Log analysis: ${logResult.state}`;
  }

  // Adjust based on heartbeat and PID
  if (heartbeat && pid) {
    if (state === 'UNKNOWN') {
      state = 'RUNNING';
      confidence = Math.max(confidence, 0.7);
    }
    details += `, Heartbeat: ✅, PID: ✅`;
  } else if (pid) {
    if (state === 'UNKNOWN') {
      state = 'STALLED';
      confidence = Math.max(confidence, 0.5);
    }
    details += `, Heartbeat: ❌, PID: ✅`;
  } else {
    if (state === 'UNKNOWN') {
      state = 'COMPLETED';
      confidence = Math.max(confidence, 0.6);
    }
    details += `, Heartbeat: ❌, PID: ❌`;
  }

  // Generate recommendations
  switch (state) {
    case 'COMPLETED':
      recommendations.push('Task completed successfully');
      break;
    case 'RUNNING':
      recommendations.push('Wait for completion', 'Move to background', 'Monitor progress');
      break;
    case 'STALLED':
      recommendations.push('Resume task', 'Retry task', 'Kill and restart');
      break;
    case 'UNKNOWN':
      recommendations.push('Check logs manually', 'Restart task', 'Contact support');
      break;
  }

  return {
    state,
    details,
    confidence,
    recommendations,
    logSnippet: logResult?.snippet,
    heartbeatStatus: heartbeat,
    pidStatus: pid
  };
}

/**
 * Get user-friendly prompt for diagnosis result
 */
export function getDiagnosisPrompt(result: SkipDiagnosisResult, language: 'vi' | 'en' = 'en'): string {
  const { getSkipPrompt } = require('./interaction_policy');
  return getSkipPrompt(result.state, language);
}

/**
 * Format diagnosis result for display
 */
export function formatDiagnosisResult(result: SkipDiagnosisResult, language: 'vi' | 'en' = 'en'): string {
  const prompt = getDiagnosisPrompt(result, language);
  const confidence = (result.confidence * 100).toFixed(1);
  
  let output = `${prompt}\n\n`;
  output += `📊 **Diagnosis Details:**\n`;
  output += `• State: ${result.state}\n`;
  output += `• Confidence: ${confidence}%\n`;
  output += `• Details: ${result.details}\n\n`;
  
  if (result.recommendations.length > 0) {
    output += `💡 **Recommendations:**\n`;
    result.recommendations.forEach((rec, index) => {
      output += `${index + 1}. ${rec}\n`;
    });
  }
  
  if (result.logSnippet) {
    output += `\n📝 **Recent Log Snippet:**\n`;
    output += `\`\`\`\n${result.logSnippet}\n\`\`\``;
  }
  
  return output;
}

// Export for CommonJS compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    diagnoseOnSkip,
    getDiagnosisPrompt,
    formatDiagnosisResult,
    SkipDiagnosisResult,
    SkipDiagnoseOptions
  };
}
