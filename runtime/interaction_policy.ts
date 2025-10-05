/**
 * StillMe Interaction Policy Loader
 * Bắt buộc nạp policy ở mọi entrypoint
 * 
 * Purpose: Đảm bảo tất cả entrypoints đều tuân thủ INTERACTION_POLICY.yaml
 * Usage: Gọi loadInteractionPolicy() ở đầu mọi entrypoint
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

// Types cho Interaction Policy
export interface InteractionPolicy {
  version: number;
  metadata: {
    name: string;
    description: string;
    author: string;
    last_updated: string;
  };
  skip: {
    semantics: string;
    actions: string[];
    timeouts: {
      diagnose_ms: number;
      heartbeat_timeout_ms: number;
    };
    outputs: string[];
    prompts: {
      [key: string]: string;
    };
    cancel_on_skip: boolean;
    log_tailing: {
      default_lines: number;
      max_lines: number;
      patterns: {
        completed: string[];
        error: string[];
        running: string[];
      };
    };
  };
  cancel: {
    semantics: string;
    actions: string[];
    require_confirmation: boolean;
    confirmation_message_vi: string;
    confirmation_message_en: string;
  };
  abort: {
    semantics: string;
    actions: string[];
    require_confirmation: boolean;
  };
  stop: {
    semantics: string;
    actions: string[];
    shutdown_timeout_ms: number;
  };
  heartbeat: {
    files: string[];
    check_interval_ms: number;
    timeout_ms: number;
  };
  logs: {
    files: string[];
    tailing: {
      buffer_size: number;
      encoding: string;
      follow: boolean;
    };
  };
  pid: {
    files: string[];
    check_interval_ms: number;
  };
  ui: {
    skip_button: {
      text_vi: string;
      text_en: string;
      tooltip_vi: string;
      tooltip_en: string;
      icon: string;
    };
    cancel_button: {
      text_vi: string;
      text_en: string;
      tooltip_vi: string;
      tooltip_en: string;
      icon: string;
    };
    status_display: {
      show_diagnosis: boolean;
      show_actions: boolean;
      auto_refresh_ms: number;
    };
  };
  compliance: {
    required_entrypoints: string[];
    must_load_policy: boolean;
    ci_checks: string[];
  };
}

// Global policy instance
let _policy: InteractionPolicy | null = null;
let _policyLoaded = false;

/**
 * Load Interaction Policy từ YAML file
 * @param policyPath - Đường dẫn đến policy file (mặc định: policies/INTERACTION_POLICY.yaml)
 * @returns InteractionPolicy object
 * @throws Error nếu không load được policy
 */
export function loadInteractionPolicy(policyPath?: string): InteractionPolicy {
  if (_policyLoaded && _policy) {
    return _policy;
  }

  const defaultPath = path.join(process.cwd(), 'policies', 'INTERACTION_POLICY.yaml');
  const finalPath = policyPath || defaultPath;

  try {
    // Check if policy file exists
    if (!fs.existsSync(finalPath)) {
      throw new Error(`Interaction Policy file not found: ${finalPath}`);
    }

    // Read and parse YAML
    const fileContent = fs.readFileSync(finalPath, 'utf8');
    const policy = yaml.load(fileContent) as InteractionPolicy;

    // Validate policy structure
    validatePolicy(policy);

    // Cache policy
    _policy = policy;
    _policyLoaded = true;

    console.log(`✅ Interaction Policy loaded successfully from: ${finalPath}`);
    console.log(`📋 Policy version: ${policy.version}`);
    console.log(`📝 Skip semantics: ${policy.skip.semantics}`);
    console.log(`🚫 Cancel on skip: ${policy.skip.cancel_on_skip}`);

    return policy;

  } catch (error) {
    const errorMessage = `Failed to load Interaction Policy from ${finalPath}: ${error}`;
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
    'version',
    'metadata',
    'skip',
    'cancel',
    'abort',
    'stop',
    'heartbeat',
    'logs',
    'pid',
    'ui',
    'compliance'
  ];

  for (const field of requiredFields) {
    if (!policy[field]) {
      throw new Error(`Missing required field in policy: ${field}`);
    }
  }

  // Validate skip semantics
  if (policy.skip.semantics !== 'diagnose') {
    throw new Error(`Invalid skip semantics: ${policy.skip.semantics}. Must be 'diagnose'`);
  }

  // Validate cancel_on_skip
  if (policy.skip.cancel_on_skip !== false) {
    throw new Error(`Invalid cancel_on_skip: ${policy.skip.cancel_on_skip}. Must be false`);
  }

  // Validate required outputs
  const requiredOutputs = ['COMPLETED', 'RUNNING', 'STALLED', 'UNKNOWN'];
  for (const output of requiredOutputs) {
    if (!policy.skip.outputs.includes(output)) {
      throw new Error(`Missing required skip output: ${output}`);
    }
  }
}

/**
 * Get cached policy (must be loaded first)
 * @returns InteractionPolicy object
 * @throws Error nếu policy chưa được load
 */
export function getInteractionPolicy(): InteractionPolicy {
  if (!_policyLoaded || !_policy) {
    throw new Error('Interaction Policy not loaded. Call loadInteractionPolicy() first.');
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
 * Get skip button configuration
 * @param language - Language code ('vi' or 'en')
 * @returns Skip button config
 */
export function getSkipButtonConfig(language: 'vi' | 'en' = 'en') {
  const policy = getInteractionPolicy();
  const button = policy.ui.skip_button;
  
  return {
    text: language === 'vi' ? button.text_vi : button.text_en,
    tooltip: language === 'vi' ? button.tooltip_vi : button.tooltip_en,
    icon: button.icon,
    semantics: policy.skip.semantics,
    cancelOnSkip: policy.skip.cancel_on_skip
  };
}

/**
 * Get cancel button configuration
 * @param language - Language code ('vi' or 'en')
 * @returns Cancel button config
 */
export function getCancelButtonConfig(language: 'vi' | 'en' = 'en') {
  const policy = getInteractionPolicy();
  const button = policy.ui.cancel_button;
  
  return {
    text: language === 'vi' ? button.text_vi : button.text_en,
    tooltip: language === 'vi' ? button.tooltip_vi : button.tooltip_en,
    icon: button.icon,
    semantics: policy.cancel.semantics,
    requireConfirmation: policy.cancel.require_confirmation,
    confirmationMessage: language === 'vi' 
      ? policy.cancel.confirmation_message_vi 
      : policy.cancel.confirmation_message_en
  };
}

/**
 * Get prompt for skip diagnosis result
 * @param state - Diagnosis state
 * @param language - Language code ('vi' or 'en')
 * @returns Prompt message
 */
export function getSkipPrompt(state: 'COMPLETED' | 'RUNNING' | 'STALLED' | 'UNKNOWN', language: 'vi' | 'en' = 'en'): string {
  const policy = getInteractionPolicy();
  const key = `${state.toLowerCase()}_${language}`;
  return policy.skip.prompts[key] || `Unknown state: ${state}`;
}

/**
 * Get log tailing configuration
 * @returns Log tailing config
 */
export function getLogTailingConfig() {
  const policy = getInteractionPolicy();
  return policy.skip.log_tailing;
}

/**
 * Get heartbeat configuration
 * @returns Heartbeat config
 */
export function getHeartbeatConfig() {
  const policy = getInteractionPolicy();
  return policy.heartbeat;
}

/**
 * Get PID monitoring configuration
 * @returns PID config
 */
export function getPidConfig() {
  const policy = getInteractionPolicy();
  return policy.pid;
}

/**
 * Check compliance requirements
 * @returns Compliance config
 */
export function getComplianceConfig() {
  const policy = getInteractionPolicy();
  return policy.compliance;
}

// Auto-load policy on module import
try {
  loadInteractionPolicy();
} catch (error) {
  console.warn(`⚠️ Could not auto-load Interaction Policy: ${error}`);
  console.warn('⚠️ Make sure to call loadInteractionPolicy() manually in your entrypoint');
}

// Export for CommonJS compatibility
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    loadInteractionPolicy,
    getInteractionPolicy,
    isPolicyLoaded,
    resetPolicyCache,
    getSkipButtonConfig,
    getCancelButtonConfig,
    getSkipPrompt,
    getLogTailingConfig,
    getHeartbeatConfig,
    getPidConfig,
    getComplianceConfig
  };
}
