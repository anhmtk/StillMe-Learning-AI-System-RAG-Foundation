/**
 * StillMe File Protection Policy Loader (TypeScript)
 * Bắt buộc nạp file protection policy ở mọi entrypoint
 * 
 * Purpose: Đảm bảo tất cả entrypoints đều tuân thủ FILE_PROTECTION.yaml
 * Usage: Gọi loadFilePolicy() ở đầu mọi entrypoint
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { spawn } from 'child_process';

// Types cho File Protection Policy
export interface FileProtectionPolicy {
  version: number;
  metadata: {
    name: string;
    description: string;
    author: string;
    last_updated: string;
    critical: boolean;
  };
  protected_files: string[];
  rules: {
    delete: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
    };
    rename: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
    };
    move: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
    };
    modify: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
      validation_required: boolean;
    };
    copy: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
    };
    read: {
      action: string;
      severity: string;
      auto_backup: boolean;
      require_approval: boolean;
    };
  };
  commit: { [key: string]: string };
  messages: { [key: string]: string };
  validation: {
    required_keys: string[];
    key_patterns: { [key: string]: string };
    file_size_limit: number;
    line_limit: number;
    encoding: string;
    line_endings: string;
  };
  backup: {
    enabled: boolean;
    directory: string;
    max_backups: number;
    compression: boolean;
    encryption: boolean;
    triggers: string[];
    naming_pattern: string;
    timestamp_format: string;
  };
  monitoring: {
    enabled: boolean;
    log_file: string;
    log_level: string;
    events: string[];
    alerts: {
      critical_violation: {
        enabled: boolean;
        channels: string[];
        threshold: number;
      };
      multiple_violations: {
        enabled: boolean;
        channels: string[];
        threshold: number;
        time_window: number;
      };
    };
  };
  compliance: {
    required_for: string[];
    must_load_policy: boolean;
    must_validate_files: boolean;
    must_backup_before_operations: boolean;
    checks: string[];
  };
  emergency: {
    recovery_procedures: string[];
    git_recovery: string[];
    emergency_contacts: {
      admin: string;
      security: string;
      devops: string;
    };
  };
  enforcement: {
    runtime: {
      enabled: boolean;
      strict_mode: boolean;
      grace_period: number;
    };
    development: {
      enabled: boolean;
      strict_mode: boolean;
      grace_period: number;
    };
    production: {
      enabled: boolean;
      strict_mode: boolean;
      grace_period: number;
    };
    testing: {
      enabled: boolean;
      strict_mode: boolean;
      grace_period: number;
    };
  };
}

// Global policy instance
let _policy: FileProtectionPolicy | null = null;
let _policyLoaded = false;

/**
 * Load File Protection Policy từ YAML file
 * @param policyPath - Đường dẫn đến policy file (mặc định: policies/FILE_PROTECTION.yaml)
 * @returns FileProtectionPolicy object
 * @throws Error nếu không load được policy
 */
export function loadFilePolicy(policyPath?: string): FileProtectionPolicy {
  if (_policyLoaded && _policy) {
    return _policy;
  }

  const defaultPath = path.join(process.cwd(), 'policies', 'FILE_PROTECTION.yaml');
  const finalPath = policyPath || defaultPath;

  try {
    // Check if policy file exists
    if (!fs.existsSync(finalPath)) {
      throw new Error(`File Protection Policy file not found: ${finalPath}`);
    }

    // Read and parse YAML
    const fileContent = fs.readFileSync(finalPath, 'utf8');
    const policy = yaml.load(fileContent) as FileProtectionPolicy;

    // Validate policy structure
    validatePolicy(policy);

    // Cache policy
    _policy = policy;
    _policyLoaded = true;

    console.log(`✅ File Protection Policy loaded successfully from: ${finalPath}`);
    console.log(`📋 Policy version: ${policy.version}`);
    console.log(`🔒 Protected files: ${policy.protected_files.length}`);
    console.log(`🛡️ Protection enabled: ${policy.enforcement.runtime.enabled}`);

    return policy;

  } catch (error) {
    const errorMessage = `Failed to load File Protection Policy from ${finalPath}: ${error}`;
    console.error(`❌ ${errorMessage}`);
    throw new Error(errorMessage);
  }
}

/**
 * Validate policy structure
 * @param policy - Policy object to validate
 * @throws Error nếu policy không hợp lệ
 */
function validatePolicy(policy: any): void {
  const requiredFields = [
    'version', 'metadata', 'protected_files', 'rules', 'commit',
    'messages', 'validation', 'backup', 'monitoring', 'compliance'
  ];

  for (const field of requiredFields) {
    if (!policy[field]) {
      throw new Error(`Missing required field in policy: ${field}`);
    }
  }

  // Validate protected files
  if (!policy.protected_files || policy.protected_files.length === 0) {
    throw new Error('No protected files defined in policy');
  }

  // Validate rules
  const requiredOperations = ['delete', 'rename', 'move', 'modify', 'copy', 'read'];
  for (const operation of requiredOperations) {
    if (!policy.rules[operation]) {
      throw new Error(`Missing rule for operation: ${operation}`);
    }
  }
}

/**
 * Get cached policy (must be loaded first)
 * @returns FileProtectionPolicy object
 * @throws Error nếu policy chưa được load
 */
export function getFilePolicy(): FileProtectionPolicy {
  if (!_policyLoaded || !_policy) {
    throw new Error('File Protection Policy not loaded. Call loadFilePolicy() first.');
  }
  return _policy;
}

/**
 * Check if policy is loaded
 * @returns boolean
 */
export function isPolicyLoaded(): boolean {
  return _policyLoaded && _policy !== null;
}

/**
 * Reset policy cache (for testing)
 */
export function resetPolicyCache(): void {
  _policy = null;
  _policyLoaded = false;
}

/**
 * Check if file is protected
 * @param filePath - Path to file to check
 * @returns boolean - True nếu file được bảo vệ
 */
export function isProtectedFile(filePath: string): boolean {
  const policy = getFilePolicy();
  const fileName = path.basename(filePath);
  
  return policy.protected_files.includes(fileName);
}

/**
 * Assert that protected files are not being modified
 * @param action - Action being performed ('delete', 'rename', 'move', 'modify')
 * @param filePaths - List of file paths being affected
 * @throws Error nếu vi phạm policy
 */
export function assertProtectedFiles(action: string, filePaths: string[]): void {
  const policy = getFilePolicy();
  
  for (const filePath of filePaths) {
    if (isProtectedFile(filePath)) {
      const rule = policy.rules[action as keyof typeof policy.rules];
      
      if (rule.action === 'deny') {
        const message = policy.messages[`${action}_violation_vi`] || 
                       `Cannot ${action} protected file: ${filePath}`;
        throw new Error(message);
      }
      
      if (rule.action === 'require_approval') {
        if (!rule.require_approval) {
          const message = policy.messages[`${action}_violation_vi`] ||
                         `Approval required to ${action} protected file: ${filePath}`;
          throw new Error(message);
        }
      }
    }
  }
}

/**
 * Validate .env file content
 * @param filePath - Path to .env file
 * @returns Promise<[boolean, string[]]> - [is_valid, error_messages]
 */
export async function validateEnvFile(filePath: string): Promise<[boolean, string[]]> {
  const policy = getFilePolicy();
  const validation = policy.validation;
  const errors: string[] = [];
  
  try {
    // Check file size
    const stats = fs.statSync(filePath);
    if (stats.size > validation.file_size_limit) {
      errors.push(`File size ${stats.size} exceeds limit ${validation.file_size_limit}`);
    }
    
    // Read and validate content
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    if (lines.length > validation.line_limit) {
      errors.push(`Line count ${lines.length} exceeds limit ${validation.line_limit}`);
    }
    
    // Check required keys
    for (const requiredKey of validation.required_keys) {
      if (!content.includes(requiredKey)) {
        errors.push(`Missing required key: ${requiredKey}`);
      }
    }
    
    // Validate key patterns
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.includes('=') && !trimmedLine.startsWith('#')) {
        const [key, value] = trimmedLine.split('=', 2);
        const trimmedKey = key.trim();
        const trimmedValue = value.trim();
        
        if (validation.key_patterns[trimmedKey]) {
          const pattern = new RegExp(validation.key_patterns[trimmedKey]);
          if (!pattern.test(trimmedValue)) {
            errors.push(`Invalid pattern for ${trimmedKey}: ${trimmedValue}`);
          }
        }
      }
    }
    
    return [errors.length === 0, errors];
    
  } catch (error) {
    return [false, [`Validation error: ${error}`]];
  }
}

/**
 * Create backup of protected file
 * @param filePath - Path to file to backup
 * @param operation - Operation that triggered backup
 * @returns Promise<string> - Path to backup file
 */
export async function createBackup(filePath: string, operation: string = 'manual'): Promise<string> {
  const policy = getFilePolicy();
  const backupConfig = policy.backup;
  
  if (!backupConfig.enabled) {
    return null;
  }
  
  // Create backup directory
  const backupDir = backupConfig.directory;
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir, { recursive: true });
  }
  
  // Generate backup filename
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const backupFilename = backupConfig.naming_pattern
    .replace('{timestamp}', timestamp)
    .replace('{operation}', operation);
  const backupPath = path.join(backupDir, backupFilename);
  
  try {
    // Copy file to backup
    fs.copyFileSync(filePath, backupPath);
    
    // Compress if enabled
    if (backupConfig.compression) {
      const { gzip } = require('zlib');
      const { promisify } = require('util');
      const gzipAsync = promisify(gzip);
      
      const fileContent = fs.readFileSync(backupPath);
      const compressed = await gzipAsync(fileContent);
      fs.writeFileSync(`${backupPath}.gz`, compressed);
      fs.unlinkSync(backupPath);
      return `${backupPath}.gz`;
    }
    
    // Cleanup old backups
    await cleanupOldBackups(backupDir, backupConfig.max_backups);
    
    console.log(`✅ Created backup: ${backupPath}`);
    return backupPath;
    
  } catch (error) {
    console.error(`❌ Failed to create backup: ${error}`);
    throw error;
  }
}

/**
 * Cleanup old backup files
 * @param backupDir - Backup directory path
 * @param maxBackups - Maximum number of backups to keep
 */
async function cleanupOldBackups(backupDir: string, maxBackups: number): Promise<void> {
  try {
    const files = fs.readdirSync(backupDir);
    const backupFiles = files
      .filter(filename => filename.startsWith('.env.backup.'))
      .map(filename => ({
        path: path.join(backupDir, filename),
        mtime: fs.statSync(path.join(backupDir, filename)).mtime
      }))
      .sort((a, b) => b.mtime.getTime() - a.mtime.getTime());
    
    // Remove old backups
    for (let i = maxBackups; i < backupFiles.length; i++) {
      fs.unlinkSync(backupFiles[i].path);
      console.log(`🗑️ Removed old backup: ${backupFiles[i].path}`);
    }
    
  } catch (error) {
    console.error(`❌ Failed to cleanup old backups: ${error}`);
  }
}

/**
 * Get list of protected files
 * @returns string[] - List of protected file names
 */
export function getProtectedFiles(): string[] {
  const policy = getFilePolicy();
  return policy.protected_files;
}

/**
 * Get commit rules for protected files
 * @returns { [key: string]: string } - Commit rules (file_name -> action)
 */
export function getCommitRules(): { [key: string]: string } {
  const policy = getFilePolicy();
  return policy.commit;
}

/**
 * Get validation rules
 * @returns any - Validation rules
 */
export function getValidationRules(): any {
  const policy = getFilePolicy();
  return policy.validation;
}

/**
 * Get backup configuration
 * @returns any - Backup configuration
 */
export function getBackupConfig(): any {
  const policy = getFilePolicy();
  return policy.backup;
}

/**
 * Get monitoring configuration
 * @returns any - Monitoring configuration
 */
export function getMonitoringConfig(): any {
  const policy = getFilePolicy();
  return policy.monitoring;
}

/**
 * Get compliance configuration
 * @returns any - Compliance configuration
 */
export function getComplianceConfig(): any {
  const policy = getFilePolicy();
  return policy.compliance;
}

/**
 * Ensure policy is loaded, auto-load if not
 * @throws Error nếu không thể load policy
 */
export function ensurePolicyLoaded(): void {
  if (!isPolicyLoaded()) {
    try {
      loadFilePolicy();
    } catch (error) {
      throw new Error(`Failed to auto-load File Protection Policy: ${error}`);
    }
  }
}

// Auto-load policy on module import
try {
  loadFilePolicy();
} catch (error) {
  console.warn(`⚠️ Could not auto-load File Protection Policy: ${error}`);
  console.warn('⚠️ Make sure to call loadFilePolicy() manually in your entrypoint');
}

// Export for CommonJS compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    loadFilePolicy,
    getFilePolicy,
    isPolicyLoaded,
    resetPolicyCache,
    isProtectedFile,
    assertProtectedFiles,
    validateEnvFile,
    createBackup,
    getProtectedFiles,
    getCommitRules,
    getValidationRules,
    getBackupConfig,
    getMonitoringConfig,
    getComplianceConfig,
    ensurePolicyLoaded
  };
}
